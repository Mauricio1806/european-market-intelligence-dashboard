# European Market Intelligence Dashboard

![Project Cover](assets/project-cover.png)

A completed data pipeline and analytics dashboard built to collect, structure and visualize public economic indicators for selected European markets.

The solution transforms raw World Bank API data into clean datasets, a SQLite database, Excel/CSV outputs and an interactive dashboard for market research, country comparison and expansion analysis.

## Final Delivery

- Automated public API data extraction
- Clean economic indicators dataset
- Excel export for business users
- SQLite database for structured storage
- Interactive Streamlit dashboard
- Country comparison analysis
- Indicator trend analysis
- Market ranking view
- Downloadable reporting files

## Dashboard Preview

![Dashboard Preview](assets/dashboard-preview.png)

## Business Value

This solution helps business teams replace manual market research spreadsheets with an automated data workflow.

It can support expansion analysis, regional benchmarking, investment research, executive reporting and country-level market comparison across Europe.

## Data Workflow

World Bank API → Python Extractor → Raw JSON → Data Cleaning → SQLite / Excel / CSV → Streamlit Dashboard

## Key Features

- Public API data extraction
- Multi-country European market dataset
- Economic indicator cleaning and standardization
- Historical trend analysis
- Country comparison dashboard
- Market ranking tables
- CSV, Excel and SQLite outputs
- Interactive filters and downloadable data

## Tech Stack

Python, Requests, Pandas, SQLite, Streamlit, Plotly, Excel, CSV, World Bank API

## Freelance Use Cases

This type of solution can be adapted for:

- European market research
- Country benchmarking
- Expansion analysis
- Investment research dashboards
- Public data automation
- Executive reporting
- Economic indicator tracking
- Regional business intelligence

## Repository Structure

```
european-market-intelligence-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── assets/
│   ├── project-cover.png
│   ├── dashboard-preview.png
│   └── fiverr_portfolio_text.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── database/
└── src/
    ├── extractor.py
    ├── transformer.py
    ├── database.py
    └── utils.py
```

## How to Run Locally

Run the following commands on Windows to set up and start the application:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Execute data pipeline
python src/extractor.py
python src/transformer.py
python src/database.py

# Run dashboard application
streamlit run app.py
```
