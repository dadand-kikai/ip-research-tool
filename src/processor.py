import logging
from typing import List, Dict, Any
from src.reddit_client import RedditClient

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, reddit_client: RedditClient):
        self.reddit_client = reddit_client

    def process(self, anilist_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge AniList data with Reddit signals and calculate scores.
        """
        results = []
        
        for item in anilist_data:
            try:
                # Extract Titles
                titles = item.get('title', {})
                romaji = titles.get('romaji', 'Unknown')
                english = titles.get('english')
                native = titles.get('native', '')
                
                # Use English or Romaji for Reddit search
                search_terms = []
                if english: search_terms.append(english)
                if romaji: search_terms.append(romaji)
                
                # Fetch Reddit Signals
                reddit_data = self.reddit_client.get_signals(search_terms) if search_terms else {'intent_score': 0, 'velocity': 0}
                
                # Calculate Score (Heuristic MVP)
                # Weights: AniList Popularity (normalized / 1000) + Reddit Intent * 5
                ani_pop = item.get('popularity', 0) or 0
                ani_trend = item.get('trending', 0) or 0
                reddit_score = reddit_data.get('intent_score', 0)
                
                total_score = (ani_pop / 1000) + (ani_trend / 10) + (reddit_score * 5)
                
                # Determine Suggested SKU
                status = item.get('status')
                sku_manga = "Vol 1 (New)" if status == 'RELEASING' else "Complete Set (Used)"
                
                sku_goods = []
                if total_score > 100:
                    sku_goods.append("Scale Figure")
                if reddit_score > 10:
                    sku_goods.append("Limited Merch")
                if not sku_goods:
                    sku_goods.append("Acrylic Stand / Keychains")
                
                row = {
                    'title_native': native,
                    'title_en': english or romaji,
                    'anilist_id': item.get('id'),
                    'anilist_popularity': ani_pop,
                    'anilist_trending': ani_trend,
                    'reddit_intent_score': reddit_score,
                    'reddit_velocity': reddit_data.get('velocity', 0),
                    'total_score': round(total_score, 2),
                    'recommended_sku_manga': sku_manga,
                    'recommended_sku_goods': ", ".join(sku_goods),
                    'notes': f"Reddit Query: {reddit_data.get('raw_query', 'N/A')}"
                }
                
                results.append(row)
                
            except Exception as e:
                logger.error(f"Error processing item {item.get('id')}: {e}")
                continue
                
        # Sort by total score descending
        results.sort(key=lambda x: x['total_score'], reverse=True)
        return results
