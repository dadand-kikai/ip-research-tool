import sys
import logging
from src.config import Config
from src.anilist_client import AniListClient
from src.google_trends_client import GoogleTrendsClient
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
        # Fetching 200 candidates total (100 Trending, 100 Popular)
        candidates = anilist.get_candidates(target_count=200)
        
        if not candidates:
            logger.warning("No candidates found. Exiting.")
            return

        # Step 2 - Enrich with Google Trends Signals
        logger.info("Step 2: Enriching data with Google Trends signals...")
        google_trends = GoogleTrendsClient()
        processor = DataProcessor(google_trends)
        # Only check Trends for Top 50 to save quota/time
        processed_data = processor.process(candidates, trends_limit=50)
        
        # Step 3 - Generate Report
        logger.info("Step 3: Generating report.csv...")
        Reporter.generate_csv(processed_data)
        
        # Step 4 - Market Gate (Buy List)
        logger.info("Step 4: Running Market Gate (buy_list.csv)...")
        from src.market_gate import MarketGate
        gate = MarketGate()
        gate.process()
        
        logger.info("Batch completed successfully.")
        
    except Exception as e:
        logger.error(f"Batch failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
