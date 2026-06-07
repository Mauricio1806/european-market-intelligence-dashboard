import logging
import sys

# Define country mappings and attributes
COUNTRIES = {
    'DEU': {'name': 'Germany', 'iso2': 'DE', 'eu': True, 'region': 'Western Europe', 'subregion': 'DACH'},
    'FRA': {'name': 'France', 'iso2': 'FR', 'eu': True, 'region': 'Western Europe', 'subregion': None},
    'ITA': {'name': 'Italy', 'iso2': 'IT', 'eu': True, 'region': 'Southern Europe', 'subregion': None},
    'ESP': {'name': 'Spain', 'iso2': 'ES', 'eu': True, 'region': 'Southern Europe', 'subregion': None},
    'NLD': {'name': 'Netherlands', 'iso2': 'NL', 'eu': True, 'region': 'Western Europe', 'subregion': None},
    'PRT': {'name': 'Portugal', 'iso2': 'PT', 'eu': True, 'region': 'Southern Europe', 'subregion': None},
    'POL': {'name': 'Poland', 'iso2': 'PL', 'eu': True, 'region': 'Eastern Europe', 'subregion': None},
    'SWE': {'name': 'Sweden', 'iso2': 'SE', 'eu': True, 'region': 'Nordics', 'subregion': None},
    'BEL': {'name': 'Belgium', 'iso2': 'BE', 'eu': True, 'region': 'Western Europe', 'subregion': None},
    'AUT': {'name': 'Austria', 'iso2': 'AT', 'eu': True, 'region': 'Western Europe', 'subregion': 'DACH'},
    'DNK': {'name': 'Denmark', 'iso2': 'DK', 'eu': True, 'region': 'Nordics', 'subregion': None},
    'IRL': {'name': 'Ireland', 'iso2': 'IE', 'eu': True, 'region': 'Western Europe', 'subregion': None},
    'FIN': {'name': 'Finland', 'iso2': 'FI', 'eu': True, 'region': 'Nordics', 'subregion': None},
    'NOR': {'name': 'Norway', 'iso2': 'NO', 'eu': False, 'region': 'Nordics', 'subregion': None},
    'CHE': {'name': 'Switzerland', 'iso2': 'CH', 'eu': False, 'region': 'Western Europe', 'subregion': 'DACH'},
    'GBR': {'name': 'United Kingdom', 'iso2': 'GB', 'eu': False, 'region': 'Western Europe', 'subregion': None},
}

# Define the indicators to fetch
INDICATORS = {
    'NY.GDP.PCAP.CD': 'GDP per capita (current US$)',
    'SP.POP.TOTL': 'Population, total',
    'SL.UEM.TOTL.ZS': 'Unemployment, total (% of total labor force)',
    'FP.CPI.TOTL.ZG': 'Inflation, consumer prices (annual %)',
    'IT.NET.USER.ZS': 'Individuals using the Internet (% of population)',
    'NE.EXP.GNFS.ZS': 'Exports of goods and services (% of GDP)'
}

# Helper mapping for easier dashboard use
INDICATOR_SHORT_NAMES = {
    'NY.GDP.PCAP.CD': 'GDP per capita',
    'SP.POP.TOTL': 'Population',
    'SL.UEM.TOTL.ZS': 'Unemployment rate',
    'FP.CPI.TOTL.ZG': 'Inflation',
    'IT.NET.USER.ZS': 'Internet users percentage',
    'NE.EXP.GNFS.ZS': 'Exports percentage of GDP'
}

def get_logger(name: str) -> logging.Logger:
    """
    Sets up a clean, professional logger that writes to standard output.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
