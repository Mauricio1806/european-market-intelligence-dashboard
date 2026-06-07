import os
import sqlite3
import pandas as pd
from utils import COUNTRIES, INDICATORS, INDICATOR_SHORT_NAMES, get_logger

# Initialize logger
logger = get_logger("database")

# Directories and file paths
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DATA_DIR = os.path.join(PROJECT_DIR, "data", "processed")
DATABASE_DIR = os.path.join(PROJECT_DIR, "data", "database")
DB_PATH = os.path.join(DATABASE_DIR, "europe_market.db")

def init_database() -> sqlite3.Connection:
    """
    Creates the database directory and initializes the SQLite tables.
    """
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR, exist_ok=True)
        logger.info(f"Created database directory: {DATABASE_DIR}")
        
    conn = sqlite3.connect(DB_PATH)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(conn: sqlite3.Connection):
    """
    Creates normalized tables and views for the market intelligence data.
    """
    cursor = conn.cursor()
    
    # Drop existing tables and views if they exist to prevent schema conflicts
    logger.info("Initializing schema tables...")
    cursor.execute("DROP VIEW IF EXISTS v_europe_market_indicators_long;")
    cursor.execute("DROP VIEW IF EXISTS v_europe_market_indicators_wide;")
    cursor.execute("DROP TABLE IF EXISTS market_data;")
    cursor.execute("DROP TABLE IF EXISTS countries;")
    cursor.execute("DROP TABLE IF EXISTS indicators;")
    cursor.execute("DROP TABLE IF EXISTS europe_market_indicators_flat;")
    
    # 1. Create countries table
    cursor.execute("""
    CREATE TABLE countries (
        country_code TEXT PRIMARY KEY,
        country_name TEXT NOT NULL,
        iso2 TEXT NOT NULL,
        is_eu INTEGER NOT NULL CHECK (is_eu IN (0, 1)),
        region TEXT NOT NULL,
        subregion TEXT
    );
    """)
    
    # 2. Create indicators table
    cursor.execute("""
    CREATE TABLE indicators (
        indicator_code TEXT PRIMARY KEY,
        indicator_name TEXT NOT NULL,
        indicator_short_name TEXT NOT NULL
    );
    """)
    
    # 3. Create market_data table
    cursor.execute("""
    CREATE TABLE market_data (
        country_code TEXT,
        indicator_code TEXT,
        year INTEGER,
        value REAL,
        PRIMARY KEY (country_code, indicator_code, year),
        FOREIGN KEY (country_code) REFERENCES countries(country_code) ON DELETE CASCADE,
        FOREIGN KEY (indicator_code) REFERENCES indicators(indicator_code) ON DELETE CASCADE
    );
    """)
    
    # 4. Create a flat table mapping the exact requested schema
    cursor.execute("""
    CREATE TABLE europe_market_indicators_flat (
        country TEXT,
        country_code TEXT,
        year INTEGER,
        indicator_name TEXT,
        indicator_code TEXT,
        value REAL
    );
    """)
    
    # 5. Create a view that returns the long-format schema
    cursor.execute("""
    CREATE VIEW v_europe_market_indicators_long AS
    SELECT 
        c.country_name AS country,
        md.country_code,
        md.year,
        i.indicator_name,
        md.indicator_code,
        md.value
    FROM market_data md
    JOIN countries c ON md.country_code = c.country_code
    JOIN indicators i ON md.indicator_code = i.indicator_code;
    """)
    
    conn.commit()
    logger.info("Schema tables and views successfully created.")

def populate_static_tables(conn: sqlite3.Connection):
    """
    Populates countries and indicators tables with reference data.
    """
    cursor = conn.cursor()
    
    # Populate countries
    logger.info("Loading countries metadata...")
    country_records = []
    for code, attrs in COUNTRIES.items():
        country_records.append((
            code,
            attrs['name'],
            attrs['iso2'],
            1 if attrs['eu'] else 0,
            attrs['region'],
            attrs['subregion']
        ))
    cursor.executemany("""
    INSERT INTO countries (country_code, country_name, iso2, is_eu, region, subregion)
    VALUES (?, ?, ?, ?, ?, ?);
    """, country_records)
    
    # Populate indicators
    logger.info("Loading indicators metadata...")
    indicator_records = []
    for code, name in INDICATORS.items():
        short_name = INDICATOR_SHORT_NAMES.get(code, name)
        indicator_records.append((code, name, short_name))
        
    cursor.executemany("""
    INSERT INTO indicators (indicator_code, indicator_name, indicator_short_name)
    VALUES (?, ?, ?);
    """, indicator_records)
    
    conn.commit()
    logger.info(f"Loaded {len(country_records)} countries and {len(indicator_records)} indicators into dimension tables.")

def load_and_insert_data(conn: sqlite3.Connection):
    """
    Loads transformed CSV datasets and inserts data into the SQLite database.
    """
    csv_path = os.path.join(PROCESSED_DATA_DIR, "europe_market_indicators.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Processed CSV data not found at: {csv_path}. Please run transformer.py first.")
        
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} records from processed CSV for database insertion.")
    
    # 1. Insert into flat table
    df.to_sql("europe_market_indicators_flat", conn, if_exists="append", index=False)
    logger.info("Populated flat table 'europe_market_indicators_flat'.")
    
    # 2. Insert into normalized market_data table
    # We drop any indicators or countries not present in the reference dimensions (to satisfy foreign key constraints)
    valid_countries = set(COUNTRIES.keys())
    valid_indicators = set(INDICATORS.keys())
    
    filtered_df = df[
        df['country_code'].isin(valid_countries) & 
        df['indicator_code'].isin(valid_indicators)
    ]
    
    # Extract records for normalized db
    market_records = []
    for _, row in filtered_df.iterrows():
        val = None if pd.isna(row['value']) else float(row['value'])
        market_records.append((
            row['country_code'],
            row['indicator_code'],
            int(row['year']),
            val
        ))
        
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT OR REPLACE INTO market_data (country_code, indicator_code, year, value)
    VALUES (?, ?, ?, ?);
    """, market_records)
    
    conn.commit()
    logger.info(f"Successfully loaded {len(market_records)} records into normalized 'market_data' table.")

def verify_database(conn: sqlite3.Connection):
    """
    Performs verification queries to validate database contents.
    """
    cursor = conn.cursor()
    
    # Check count in flat table
    cursor.execute("SELECT COUNT(*) FROM europe_market_indicators_flat;")
    flat_count = cursor.fetchone()[0]
    
    # Check count in normalized table
    cursor.execute("SELECT COUNT(*) FROM market_data;")
    normalized_count = cursor.fetchone()[0]
    
    # Check unique countries
    cursor.execute("SELECT COUNT(DISTINCT country_code) FROM market_data;")
    country_count = cursor.fetchone()[0]
    
    logger.info("--- Database Verification Report ---")
    logger.info(f"Flat table records: {flat_count}")
    logger.info(f"Normalized table records: {normalized_count}")
    logger.info(f"Unique countries represented: {country_count}")
    
    if flat_count == 0 or normalized_count == 0:
        raise ValueError("Verification failed: Database tables are empty!")
        
    logger.info("Database integrity verification PASSED.")

def main():
    logger.info("Initializing European Market Intelligence Database Loader pipeline...")
    conn = None
    try:
        conn = init_database()
        create_tables(conn)
        populate_static_tables(conn)
        load_and_insert_data(conn)
        verify_database(conn)
        logger.info(f"Database setup and loading completed successfully. File saved at: {DB_PATH}")
    except Exception as e:
        logger.critical(f"Database pipeline failed: {e}")
        raise e
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
