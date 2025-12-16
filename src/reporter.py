import pandas as pd
import logging
from typing import List, Dict, Any
from src.config import Config

logger = logging.getLogger(__name__)

class Reporter:
    @staticmethod
    def generate_csv(data: List[Dict[str, Any]], filename: str = Config.REPORT_FILE):
        """
        Convert processed data to CSV.
        """
        if not data:
            logger.warning("No data to report.")
            return

        try:
            df = pd.DataFrame(data)
            
            # Ensure column order
            columns = [
                'title_native', 'title_en', 'total_score',
                'anilist_popularity', 'anilist_trending',
                'reddit_intent_score', 'reddit_velocity',
                'recommended_sku_manga', 'recommended_sku_goods',
                'notes', 'anilist_id'
            ]
            
            # Filter valid columns that exist in data
            valid_columns = [c for c in columns if c in df.columns]
            df = df[valid_columns]
            
            df.to_csv(filename, index=False, encoding='utf-8-sig') # sig for Excel compatibility
            logger.info(f"Report generated successfully: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
