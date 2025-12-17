import logging
from typing import List, Dict, Any
from src.google_trends_client import GoogleTrendsClient

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, trends_client: GoogleTrendsClient):
        self.trends_client = trends_client

    def process(self, anilist_data: List[Dict[str, Any]], trends_limit: int = 50) -> List[Dict[str, Any]]:
        """
        Two-Stage Processing:
        1. Calculate Base Metrics (AniList) + Anime Status
        2. Filter Top K (trends_limit)
        3. Fetch Trends for Top K
        4. Return merged list
        """
        # --- Stage 1: Base Processing ---
        pre_processed = []
        
        for item in anilist_data:
            # Extract Titles
            titles = item.get('title', {})
            romaji = titles.get('romaji', 'Unknown')
            english = titles.get('english')
            native = titles.get('native', '')
            search_term = english if english else romaji
            
            # AniList Scores
            ani_pop = item.get('popularity', 0) or 0
            ani_trend = item.get('trending', 0) or 0
            score_anilist = (ani_pop / 1000) + (ani_trend / 10)
            
            # Anime Status Detection
            anime_status = "None"
            relations = item.get('relations', {}).get('edges', [])
            for edge in relations:
                if edge.get('relationType') == 'ADAPTATION':
                    node = edge.get('node', {})
                    if node.get('type') == 'ANIME':
                        status = node.get('status')
                        # Prioritize: RELEASING > NOT_YET_RELEASED > FINISHED
                        if status == 'RELEASING':
                            anime_status = "Airing"
                            break # Highest priority found
                        elif status == 'NOT_YET_RELEASED':
                            anime_status = "Announced"
                        elif status == 'FINISHED' and anime_status == "None":
                            anime_status = "Finished"
            
            pre_processed.append({
                'item': item,
                'search_term': search_term,
                'native': native,
                'score_anilist': score_anilist,
                'anime_status': anime_status
            })
            
        # --- Stage 2: Selection & Enrichment ---
        # Sort by AniList score to pick best candidates for expensive Trends API
        pre_processed.sort(key=lambda x: x['score_anilist'], reverse=True)
        
        results = []
        
        for idx, entry in enumerate(pre_processed):
            item = entry['item']
            search_term = entry['search_term']
            score_anilist = entry['score_anilist']
            anime_status = entry['anime_status']
            
            # Determine if we check Trends
            # Top N items get Trends, others are skipped
            check_trends = idx < trends_limit
            
            if check_trends:
                # Fetch Google Trends (Expensive)
                trends_data = self.trends_client.get_signals(search_term)
                
                # Extract Signals
                intent_manga = trends_data.get('intent_manga', float('nan'))
                intent_merch = trends_data.get('intent_merch', float('nan'))
                velocity = trends_data.get('velocity', float('nan'))
                norm_score = trends_data.get('normalized_score', float('nan'))
                trends_status = trends_data.get('status', 'unknown')
                anchor_term = trends_data.get('anchor_term', 'None')
            else:
                # Skipped
                intent_manga = 0.0
                intent_merch = 0.0
                velocity = 0.0
                norm_score = 0.0
                trends_status = 'skipped'
                anchor_term = 'None'

            # Safe values for calculation
            import math
            def is_valid(v): return v is not None and not math.isnan(v)
            def safe_val(v, default=0.0): return v if is_valid(v) else default
            
            # Velocity Logic
            velocity_score = 0.0
            if check_trends and is_valid(velocity) and is_valid(norm_score):
                if norm_score >= 0.5: 
                    capped_velocity = min(velocity, 2.0)
                    velocity_score = capped_velocity * 50
            
            # Data Quality Score
            data_quality = 1.0
            if trends_status == 'skipped':
                data_quality = 0.5 # Medium confidence (AniList only)
            elif not is_valid(norm_score):
                data_quality = 0.1 # Failed API
            elif trends_status.startswith('cached'):
                data_quality = 0.8
            
            # Total Score Calculation
            score_intent_manga = safe_val(intent_manga) * 1.5
            
            if data_quality < 0.5: # Failed API
                total_score = score_anilist
            elif trends_status == 'skipped':
                total_score = score_anilist # Just AniList
            else:
                total_score = score_anilist + score_intent_manga + velocity_score
            
            # SKU Logic
            status = item.get('status')
            sku_manga = "Vol 1 (New)" if status == 'RELEASING' else "Complete Set (Used)"
            
            sku_goods = []
            if safe_val(intent_merch) > 20: 
                sku_goods.append("Scale Figure")
            elif safe_val(intent_merch) > 5:
                sku_goods.append("Acrylic Stand")
            
            if safe_val(velocity) > 0.5:
                sku_goods.append("Preorder Bonus")
                
            if anime_status == 'Announced':
                sku_goods.append("Anime Hype Investment")
            
            if not sku_goods:
                sku_goods.append("General Merch")
            
            row = {
                'title_native': entry['native'],
                'title_en': search_term,
                'anilist_id': item.get('id'),
                'anilist_popularity': item.get('popularity', 0),
                'anilist_trending': item.get('trending', 0),
                
                'score_total': round(total_score, 2),
                'score_anilist': round(score_anilist, 2),
                'score_intent_manga': round(safe_val(intent_manga), 2),
                'score_intent_merch': round(safe_val(intent_merch), 2), 
                'score_velocity': round(velocity_score, 2),
                
                'trends_normalized': round(safe_val(norm_score), 2),
                'trends_status': trends_status,
                'data_quality': data_quality,
                'anchor_term': anchor_term,
                'anime_adaptation': anime_status,
                
                'recommended_sku_manga': sku_manga,
                'recommended_sku_goods': ", ".join(sku_goods),
                'notes': f"Vel: {safe_val(velocity):.1%}, Status: {trends_status}"
            }
            
            results.append(row)
            
        # Final Sort
        results.sort(key=lambda x: x['score_total'], reverse=True)
        return results
