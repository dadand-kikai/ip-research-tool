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

    def get_trending_manga(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch trending manga from AniList.
        """
        query = '''
        query ($page: Int, $perPage: Int) {
          Page (page: $page, perPage: $perPage) {
            pageInfo {
              total
              currentPage
              lastPage
              hasNextPage
              perPage
            }
            media (type: MANGA, sort: TRENDING_DESC, countryOfOrigin: "JP", isAdult: false) {
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
            }
          }
        }
        '''
        
        variables = {
            'page': 1,
            'perPage': limit
        }
        
        logger.info(f"Fetching top {limit} trending manga from AniList...")
        data = self._query(query, variables)
        
        if not data or 'Page' not in data or 'media' not in data['Page']:
            logger.error("Failed to parse AniList response.")
            return []
            
        manga_list = data['Page']['media']
        logger.info(f"Successfully fetched {len(manga_list)} manga.")
        return manga_list

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    client = AniListClient()
    results = client.get_trending_manga(5)
    for m in results:
        print(f"{m['title']['romaji']} (Pop: {m['popularity']}, Trend: {m['trending']})")
