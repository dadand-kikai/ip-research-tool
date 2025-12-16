import praw
import time
import logging
from typing import Dict, Any, List
from src.config import Config

logger = logging.getLogger(__name__)

class RedditClient:
    def __init__(self):
        # Only initialize if credentials actrually exist
        if Config.REDDIT_CLIENT_ID and Config.REDDIT_CLIENT_SECRET:
            self.reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                user_agent=Config.REDDIT_USER_AGENT,
                read_only=True
            )
        else:
            self.reddit = None
            logger.warning("Reddit credentials missing. Reddit client disabled.")

    def get_signals(self, keywords: List[str]) -> Dict[str, Any]:
        """
        Search for purchase intent signals for a given title (or list of aliases).
        Returns a dictionary with metrics.
        """
        if not self.reddit:
            return {'intent_score': 0, 'velocity': 0}

        # Construct query: (Title1 OR Title2) AND (buy OR merch OR goods OR figure)
        # However, search queries can't be too long.
        # MVP: Just use the primary title (Romaji or English) + "buy/merch"
        
        primary_term = keywords[0]
        query = f'"{primary_term}" (buy OR merch OR figure OR goods OR box OR price)'
        
        try:
            # Search in relevant subreddits or globally?
            # Global is noisy. Specific subs: manga, anime, AnimeFigures, MangaCollectors
            subreddit = self.reddit.subreddit("manga+anime+AnimeFigures+MangaCollectors")
            
            # Fetch recent posts
            results = subreddit.search(query, sort='new', time_filter='month', limit=20)
            
            post_count = 0
            score_sum = 0
            
            for post in results:
                post_count += 1
                score_sum += post.score
            
            return {
                'intent_score': post_count * 10 + score_sum, # Crude heuristic
                'reddit_velocity': post_count, # Posts in last month matching buying intent
                'raw_query': query
            }
            
        except Exception as e:
            logger.error(f"Reddit Search Failed for {primary_term}: {e}")
            return {'intent_score': 0, 'velocity': 0}

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    from src.config import Config
    # Config needs to be loaded with env vars for this to really work
    # Assuming .env is present or vars are set
    
    client = RedditClient()
    if client.reddit:
        print("Testing Reddit Client...")
        met = client.get_signals(["Frieren"]) # Example
        print(f"Signals for Frieren: {met}")
    else:
        print("Skipping test (no credentials).")
