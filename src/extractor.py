import os
import json
import time
import requests
from utils import COUNTRIES, INDICATORS, get_logger

# Initialize logger
logger = get_logger("extractor")

# Configuration
BASE_URL = "https://api.worldbank.org/v2"
START_YEAR = 2014
END_YEAR = 2024
RAW_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "data", "raw"
)

def fetch_indicator_data(indicator_code: str, retries: int = 3, backoff: int = 2) -> dict:
    """
    Fetches raw indicator data from the World Bank API for all selected countries.
    """
    country_ids = ";".join(COUNTRIES.keys())
    url = f"{BASE_URL}/country/{country_ids}/indicator/{indicator_code}"
    params = {
        "date": f"{START_YEAR}:{END_YEAR}",
        "format": "json",
        "per_page": 1000
    }
    
    logger.info(f"Extracting indicator '{indicator_code}' from World Bank API...")
    
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # World Bank API returns a list [metadata, data_list] or an error dictionary
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                logger.info(f"Successfully extracted {len(data[1])} records for {indicator_code}.")
                return data
            else:
                # API sometimes returns a success status but contains error messages inside JSON
                logger.warning(f"Unexpected response structure for {indicator_code}: {data}")
                raise ValueError("Invalid World Bank API JSON structure.")
                
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"Attempt {attempt}/{retries} failed for indicator '{indicator_code}'. Error: {e}")
            if attempt < retries:
                sleep_time = backoff ** attempt
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Failed to retrieve data for '{indicator_code}' after {retries} attempts.")
                raise e

def save_raw_data(indicator_code: str, data: list):
    """
    Saves the raw JSON response payload to the data/raw directory.
    """
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        logger.info(f"Created raw data directory: {RAW_DATA_DIR}")
        
    filename = f"{indicator_code}.json"
    file_path = os.path.join(RAW_DATA_DIR, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Cached raw JSON for '{indicator_code}' to {file_path}")

def main():
    logger.info("Initializing European Market Intelligence Data Extractor pipeline...")
    success_count = 0
    
    for indicator_code, indicator_name in INDICATORS.items():
        try:
            raw_data = fetch_indicator_data(indicator_code)
            save_raw_data(indicator_code, raw_data)
            success_count += 1
        except Exception as e:
            logger.critical(f"Pipeline extraction stopped / failed for '{indicator_code}': {e}")
            
    logger.info(f"Extraction execution completed. Successfully extracted {success_count}/{len(INDICATORS)} indicators.")

if __name__ == "__main__":
    main()
