import os
import json
import pandas as pd
from utils import COUNTRIES, INDICATORS, INDICATOR_SHORT_NAMES, get_logger

# Initialize logger
logger = get_logger("transformer")

# Directories
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(PROJECT_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(PROJECT_DIR, "data", "processed")

def load_and_parse_raw_data() -> pd.DataFrame:
    """
    Loads all raw JSON files, parses records, and creates a consolidated long-format DataFrame.
    """
    all_records = []
    
    if not os.path.exists(RAW_DATA_DIR):
        raise FileNotFoundError(f"Raw data directory does not exist: {RAW_DATA_DIR}. Please run extractor.py first.")
        
    for filename in os.listdir(RAW_DATA_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(RAW_DATA_DIR, filename)
            logger.info(f"Processing raw JSON file: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_json = json.load(f)
                
            # Second element of list contains the records
            records = raw_json[1] if len(raw_json) > 1 else []
            
            for rec in records:
                # Get the country code (standardize on ISO-3)
                country_iso3 = rec.get("countryiso3code")
                if not country_iso3:
                    # Fallback to country ID (ISO-2 usually) or check if it matches in our dict
                    country_id = rec.get("country", {}).get("id")
                    # Try to map back to country iso3 if possible
                    country_iso3 = next((k for k, v in COUNTRIES.items() if v['iso2'] == country_id), None)
                
                # Filter to only keep our target 16 countries
                if country_iso3 not in COUNTRIES:
                    continue
                    
                country_name = COUNTRIES[country_iso3]['name']
                year = int(rec.get("date"))
                indicator_code = rec.get("indicator", {}).get("id")
                indicator_name = INDICATORS.get(indicator_code, rec.get("indicator", {}).get("value"))
                value = rec.get("value")
                
                # Force numeric value type if it exists, otherwise leave as None
                if value is not None:
                    try:
                        value = float(value)
                    except ValueError:
                        value = None
                        
                all_records.append({
                    "country": country_name,
                    "country_code": country_iso3,
                    "year": year,
                    "indicator_name": indicator_name,
                    "indicator_code": indicator_code,
                    "value": value
                })
                
    df = pd.DataFrame(all_records)
    logger.info(f"Extracted a total of {len(df)} records from raw JSON files.")
    return df

def generate_wide_format(long_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivots the long format DataFrame into a wide format where each indicator is a column.
    """
    logger.info("Generating wide-format analytical table...")
    
    # Pivot the data
    wide_df = long_df.pivot_table(
        index=["country", "country_code", "year"],
        columns="indicator_code",
        values="value"
    ).reset_index()
    
    # Rename columns to human-readable short names
    rename_dict = {}
    for code, short_name in INDICATOR_SHORT_NAMES.items():
        # Clean the short name to be snake_case for easy DB and pandas access
        clean_col = short_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%_of_", "_pct_").replace("%", "_pct_")
        rename_dict[code] = clean_col
        
    wide_df = wide_df.rename(columns=rename_dict)
    
    # Add helper columns for grouping/regions in the wide table
    wide_df["is_eu"] = wide_df["country_code"].map(lambda x: COUNTRIES[x]["eu"])
    wide_df["region"] = wide_df["country_code"].map(lambda x: COUNTRIES[x]["region"])
    wide_df["subregion"] = wide_df["country_code"].map(lambda x: COUNTRIES[x]["subregion"])
    
    return wide_df

def save_datasets(long_df: pd.DataFrame, wide_df: pd.DataFrame):
    """
    Saves the processed dataframes to data/processed/ in CSV and Excel formats.
    """
    if not os.path.exists(PROCESSED_DATA_DIR):
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        logger.info(f"Created processed data directory: {PROCESSED_DATA_DIR}")
        
    # File paths
    csv_path = os.path.join(PROCESSED_DATA_DIR, "europe_market_indicators.csv")
    excel_path = os.path.join(PROCESSED_DATA_DIR, "europe_market_indicators.xlsx")
    
    # 1. Save long-format to CSV (standardized schema)
    long_df.to_csv(csv_path, index=False, encoding='utf-8')
    logger.info(f"Saved clean long-format dataset to CSV: {csv_path}")
    
    # 2. Save both formats to Excel (professional workbook)
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        long_df.to_excel(writer, sheet_name="Indicator Records (Long)", index=False)
        wide_df.to_excel(writer, sheet_name="Analytical Table (Wide)", index=False)
    logger.info(f"Saved professional multi-sheet workbook to Excel: {excel_path}")

def main():
    logger.info("Initializing European Market Intelligence Transformer pipeline...")
    try:
        long_df = load_and_parse_raw_data()
        
        # Check if we have data
        if long_df.empty:
            logger.warning("No records were loaded. Transformer execution halted.")
            return
            
        wide_df = generate_wide_format(long_df)
        
        save_datasets(long_df, wide_df)
        logger.info("Transformation execution successfully completed.")
        
    except Exception as e:
        logger.critical(f"Transformer pipeline failed: {e}")
        raise e

if __name__ == "__main__":
    main()
