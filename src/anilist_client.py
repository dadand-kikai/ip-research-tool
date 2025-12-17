import requests
import time
import logging
from typing import List, Dict, Any, Optional
from src.config import Config

logger = logging.getLogger(__name__)

class AniListClient:
    def __init__(self):
        self.url = Config.ANILIST_API_URL

    def _query(self, query: str, variables: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Execute GraphQL query with simple rate limit handling.
        """
        try:
            response = requests.post(
                self.url,
                json={'query': query, 'variables': variables},
                timeout=10
            )
            
            # Rate limit handling (naive)
            # Headers: X-RateLimit-Limit, X-RateLimit-Remaining
            remaining = int(response.headers.get('X-RateLimit-Remaining', 90))
            if remaining < 10:
                logger.warning(f"AniList Rate Limit low ({remaining}). Sleeping 2s...")
                time.sleep(2)
                
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"GraphQL Errors: {data['errors']}")
                return None
                
            return data.get('data')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"AniList Request Failed: {e}")
            return None

    def get_candidates(self, target_count: int = 200) -> List[Dict[str, Any]]:
        """
        Fetch candidate manga merging Trending and Popular lists.
        Deduplicates by ID.
        """
        # We'll split the target budget between Trending and Popular
        # e.g. 100 Trending, 100 Popular
        batch_size = target_count // 2
        
        # 1. Fetch Trending
        trending = self._fetch_list(sort='TRENDING_DESC', limit=batch_size)
        
        # 2. Fetch Popularity
        popular = self._fetch_list(sort='POPULARITY_DESC', limit=batch_size)
        
        # 3. Merge and Deduplicate
        seen_ids = set()
        merged = []
        
        for item in trending + popular:
            if item['id'] not in seen_ids:
                merged.append(item)
                seen_ids.add(item['id'])
        
        logger.info(f"Merged candidates: {len(merged)} unique items (from {len(trending)} trending, {len(popular)} popular)")
        return merged

    def _fetch_list(self, sort: str, limit: int) -> List[Dict[str, Any]]:
        """
        Internal helper to fetch a list with specific sort.
        """
        query = '''
        query ($page: Int, $perPage: Int, $sort: [MediaSort]) {
          Page (page: $page, perPage: $perPage) {
            media (type: MANGA, sort: $sort, countryOfOrigin: "JP", isAdult: false) {
              id
              title {
                romaji
                english
                native
              }
              status
              updatedAt
              averageScore
              popularity
              trending
              favourites
              genres
              relations {
                edges {
                  relationType
                  node {
                    type
                    status
                  }
                }
              }
            }
          }
        }
        '''
        
        variables = {
            'page': 1,
            'perPage': limit,
            'sort': sort
        }
        
        logger.info(f"Fetching {limit} items sorted by {sort}...")
        data = self._query(query, variables)
        
        if not data or 'Page' not in data or 'media' not in data['Page']:
            logger.error("Failed to parse AniList response.")
            return []
            
        return data['Page']['media']
        
    # Deprecated fallback
    def get_trending_manga(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._fetch_list('TRENDING_DESC', limit)

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    client = AniListClient()
    results = client.get_trending_manga(5)
    for m in results:
        print(f"{m['title']['romaji']} (Pop: {m['popularity']}, Trend: {m['trending']})")
