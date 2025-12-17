
import logging
import time
import random
import json
import os
import math
from typing import Dict, List, Optional, Any
from pytrends.request import TrendReq
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GoogleTrendsClient:
    CACHE_FILE = "trends_cache.json"
    # List of anchors to try in order. We want a stable high-volume term.
    ANCHOR_CANDIDATES = [
        "One Piece",
        "Jujutsu Kaisen",
        "Naruto",
        "Attack on Titan",
        "Demon Slayer"
    ]
    CACHE_EXPIRY_DAYS = 7

    def __init__(self):
        # hl='en-US', tz=360 (US CST)
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def get_signals(self, term: str) -> Dict[str, Any]:
        """
        Fetches signals with Anchor Fallback.
        Returns keys: normalized_score, intent_manga, intent_merch, velocity, status, notes, anchor_term, anchor_value
        """
        # 1. Check Cache
        cached_entry = self.cache.get(term)
        if cached_entry:
            timestamp = cached_entry.get('timestamp')
            if timestamp:
                dt_ts = datetime.fromisoformat(timestamp)
                if datetime.now() - dt_ts < timedelta(days=self.CACHE_EXPIRY_DAYS):
                     logger.info(f"Using cached Trends data for '{term}'")
                     cached_entry['data']['status'] = 'cached'
                     return cached_entry['data']

        # 2. Fetch Live with Anchor Fallback
        # Sleep to avoid rate limits
        sleep_time = random.uniform(3, 6)
        logger.info(f"Sleeping {sleep_time:.2f}s before Trends request for '{term}'...")
        time.sleep(sleep_time)

        final_result = self._create_empty_result('error_no_anchor')
        
        for anchor in self.ANCHOR_CANDIDATES:
            try:
                kw_list = [
                    term,
                    anchor,
                    f"{term} manga",
                    f"{term} figure",
                    f"{term} merch"
                ]
                
                self.pytrends.build_payload(kw_list, cat=0, timeframe='today 12-m')
                df = self.pytrends.interest_over_time()
                
                if df.empty:
                    # If empty, maybe the TERM is obscure, or API failed silently? 
                    # If API failed, usually raises Exception. 
                    # If empty, it means Google has no data. 
                    # But we should check if at least Anchor has data?
                    # actually if df is empty, we have nothing.
                    logger.warning(f"No data returned for [{term}, {anchor}]")
                    # If purely no data, returning NaN is correct. 
                    final_result = self._create_empty_result('no_data')
                    break 

                # Check Anchor Health
                recent_df = df.tail(4)
                anchor_avg = recent_df[anchor].mean()
                
                if anchor_avg < 0.1:
                    logger.warning(f"Anchor '{anchor}' has near-zero volume ({anchor_avg}). Trying next anchor...")
                    continue # Try next anchor

                # --- Valid Anchor Found ---
                term_avg = recent_df[term].mean()
                
                # Normalize Score (100 = 100% of Anchor Volume)
                norm_score = (term_avg / anchor_avg) * 100
                
                # Intents
                img_manga = recent_df[kw_list[2]].mean()
                img_figure = recent_df[kw_list[3]].mean()
                img_merch = recent_df[kw_list[4]].mean()
                intent_merch_raw = max(img_figure, img_merch)
                
                intent_manga_norm = (img_manga / anchor_avg) * 100
                intent_merch_norm = (intent_merch_raw / anchor_avg) * 100

                # Velocity
                velocity = float('nan')
                if len(df) >= 3:
                     current = df[term].iloc[-2]
                     prev = df[term].iloc[-3]
                     if prev > 0:
                         velocity = (current - prev) / prev
                     elif current > 0:
                         velocity = 1.0 
                     else:
                         velocity = 0.0
                
                result_data = {
                    'normalized_score': float(norm_score),
                    'intent_manga': float(intent_manga_norm),
                    'intent_merch': float(intent_merch_norm),
                    'velocity': float(velocity),
                    'status': 'success',
                    'notes': f"Anchor: {anchor} (Avg {anchor_avg:.1f})",
                    'anchor_term': anchor,
                    'anchor_value': float(anchor_avg)
                }
                
                # Success! Save and Return
                self.cache[term] = {
                    'timestamp': datetime.now().isoformat(),
                    'data': result_data
                }
                self._save_cache()
                logger.info(f"Trends success for '{term}' via '{anchor}': Score {norm_score:.1f}")
                return result_data

            except Exception as e:
                logger.error(f"Trends API error for [{term}, {anchor}]: {e}")
                # If it's a 429, switching anchor might not help immediately, 
                # but maybe the specific query was flagged?
                # Generally 429 means we are blocked. 
                # Break loop and return failure if it's a RateLimit (usually response code 429)
                if "429" in str(e):
                    final_result = self._create_empty_result('error_api')
                    break
                # Other errors? Continue to try next anchor just in case.
                final_result = self._create_empty_result('error_unknown')
        
        # If loop finishes without returning
        return final_result

    def _create_empty_result(self, status: str) -> Dict[str, Any]:
        return {
            'normalized_score': float('nan'),
            'intent_manga': float('nan'),
            'intent_merch': float('nan'),
            'velocity': float('nan'),
            'status': status,
            'notes': "Failed",
            'anchor_term': 'None',
            'anchor_value': float('nan')
        }
