import sys
import logging
from src.config import Config
from src.anilist_client import AniListClient
from src.reddit_client import RedditClient
from src.processor import DataProcessor
from src.reporter import Reporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ip_research.log")
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting IP Research Tool Weekly Batch...")
    
    # Validate Config
    Config.validate()
    
    try:
        # Step 1 - Fetch Candidates from AniList
        logger.info("Step 1: Fetching candidates from AniList...")
        anilist = AniListClient()
        candidates = anilist.get_trending_manga(limit=20) # Limit 20 for MVP speed
        
        if not candidates:
            logger.warning("No candidates found. Exiting.")
            return

        # Step 2 - Enrich with Reddit Signals
        logger.info("Step 2: Enriching data with Reddit signals...")
        reddit = RedditClient()
        processor = DataProcessor(reddit)
        processed_data = processor.process(candidates)
        
        # Step 3 - Generate Report
        logger.info("Step 3: Generating report.csv...")
        Reporter.generate_csv(processed_data)
        
        logger.info("Batch completed successfully.")
        
    except Exception as e:
        logger.error(f"Batch failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
