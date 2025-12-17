import csv
import logging
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)

class MarketGate:
    def __init__(self, input_file: str = "report.csv", output_file: str = "buy_list.csv"):
        self.input_file = input_file
        self.output_file = output_file

    def process(self):
        """
        Reads report.csv, applies market gate logic, and writes buy_list.csv.
        """
        if not os.path.exists(self.input_file):
            logger.error(f"Input file not found: {self.input_file}")
            return

        rows = self._read_csv()
        processed_rows = []

        for row in rows:
            processed_row = self._process_row(row)
            if processed_row:
                processed_rows.append(processed_row)

        # Sort by Tier (A->B->C) then Score (Desc)
        # Tier logic: A < B < C (lexicographically A comes first)
        processed_rows.sort(key=lambda x: (x['Tier'], -float(x['Pri Score'])))

        self._write_csv(processed_rows)
        logger.info(f"Market Gate processed {len(processed_rows)} items. Saved to {self.output_file}")

    def _read_csv(self) -> List[Dict[str, str]]:
        with open(self.input_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _process_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        try:
            # 1. Parse Base Data
            title_en = row.get('title_en', 'Unknown')
            title_native = row.get('title_native', '')
            score_total = float(row.get('score_total', 0))
            data_quality = float(row.get('data_quality', 0))
            trends_norm = float(row.get('trends_normalized', 0))
            anime_status = row.get('anime_adaptation', 'None')
            
            # 2. Actionability Score
            score_actionable = score_total * data_quality
            
            # Mission 3.2: Priority Bonus for Pre-Anime/No-Anime
            priority_bonus = 0.0
            if anime_status == 'None':
                priority_bonus = 20.0
            elif anime_status == 'Announced':
                priority_bonus = 10.0
            
            score_prioritized = score_actionable + priority_bonus
            
            # 3. Tiering (Using Prioritized Score)
            tier = 'C'
            if score_prioritized > 150 and trends_norm > 10:
                tier = 'A'
            elif score_prioritized > 80:
                tier = 'B'
            
            # 4. SKU Generation
            # Simplified logic for MVP
            skus = []
            
            # Always suggest Volume 1 First Print if manga
            skus.append("Vol 1 First Print (Obi)")
            
            # Suggest Bonus/Tokuten if score is decent
            if score_actionable > 50:
                skus.append("Store Bonus Card/Paper")
            
            # High tier gets premium suggestion
            if tier == 'A':
                skus.append("Limited Acrylic Stand")

            test_sku_1 = skus[0] if len(skus) > 0 else ""
            test_sku_2 = skus[1] if len(skus) > 1 else ""

            # 5. Queries
            ebay_query = f"{title_en} manga"
            # Mercari JP: Title + basic sourcing words
            mercari_keywords = []
            if title_native:
                mercari_keywords.append(f"{title_native} 特典") # Bonus
                mercari_keywords.append(f"{title_native} 初版") # First Edition
            
            mercari_str = " | ".join(mercari_keywords)

            return {
                'Tier': tier,
                'Title': title_en,
                'Anime': anime_status,
                'Actionable Score': f"{score_actionable:.1f}",
                'Bonus': f"{priority_bonus:.0f}",
                'Pri Score': f"{score_prioritized:.1f}",
                'Trends Norm': f"{trends_norm:.1f}", 
                'Test SKU 1': test_sku_1,
                'Test SKU 2': test_sku_2,
                'eBay Query': ebay_query,
                'Mercari Keywords (JP)': mercari_str,
                '[MANUAL] Sold 30d': '',
                '[MANUAL] Price Range': '',
                '[MANUAL] Result (Pass/Fail)': '',
                'Notes': f"Qual: {data_quality}"
            }
        except Exception as e:
            logger.warning(f"Skipping row {row.get('title_en')}: {e}")
            return None

    def _write_csv(self, rows: List[Dict[str, Any]]):
        if not rows:
            return
        
        fieldnames = [
                'Tier', 'Title', 'Anime', 'Actionable Score', 'Bonus', 'Pri Score', 'Trends Norm',
                'Test SKU 1', 'Test SKU 2', 'eBay Query', 'Mercari Keywords (JP)',
                '[MANUAL] Sold 30d', '[MANUAL] Price Range', '[MANUAL] Result (Pass/Fail)',
                'Notes'
            ]
        
        with open(self.output_file, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    gate = MarketGate()
    gate.process()
