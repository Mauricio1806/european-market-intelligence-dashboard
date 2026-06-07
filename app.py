import os
import streamlit as pd_st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# We import the countries list and indicator details from src/utils
# In order to allow running streamlit from the root directory, we add the root to sys.path if needed.
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from utils import COUNTRIES, INDICATORS, INDICATOR_SHORT_NAMES

# Page configuration
pd_st.set_page_config(
    page_title="European Market Intelligence Dashboard",
    page_icon="🇪🇺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Corporate CSS Styling
pd_st.markdown("""
<style>
    /* Executive Color Palette */
    :root {
        --primary-color: #1e293b;
        --secondary-color: #0f172a;
        --accent-color: #0d9488;
        --bg-color: #f8fafc;
    }
    
    /* Title and header adjustments */
    .main-title {
        color: #1e293b;
        font-family: 'Outfit', 'Segoe UI', sans-serif;
        font-weight: 800;
        font-size: 2.4rem;
        margin-bottom: 0.1rem;
        padding-bottom: 0;
    }
    .main-subtitle {
        color: #64748b;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        margin-bottom: 1.8rem;
    }
    
    /* Metrics KPI Cards Style */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
        border-left: 5px solid #0d9488;
        margin-bottom: 15px;
    }
    .kpi-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .kpi-subtext {
        font-size: 0.75rem;
        color: #94a3b8;
    }
    
    /* Custom divider line */
    .section-divider {
        height: 2px;
        background-color: #e2e8f0;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Cache data loading
@pd_st.cache_data
def load_data():
    csv_path = os.path.join("data", "processed", "europe_market_indicators.csv")
    if not os.path.exists(csv_path):
        return None
    df = pd.read_csv(csv_path)
    return df

df_long = load_data()

# Handle missing data files gracefully
if df_long is None:
    pd_st.error("### ⚠️ Data Files Not Found")
    pd_st.info("The data pipeline has not been executed yet. Please run the data extraction and transformation pipeline commands:")
    pd_st.code("python src/extractor.py\npython src/transformer.py\npython src/database.py", language="bash")
    pd_st.stop()

# Helper dictionaries and columns
df_long["indicator_short"] = df_long["indicator_code"].map(INDICATOR_SHORT_NAMES)
df_long["is_eu"] = df_long["country_code"].map(lambda x: COUNTRIES.get(x, {}).get("eu", False))
df_long["region"] = df_long["country_code"].map(lambda x: COUNTRIES.get(x, {}).get("region", "Other"))
df_long["subregion"] = df_long["country_code"].map(lambda x: COUNTRIES.get(x, {}).get("subregion"))

# Pivot data to wide format for specific operations
df_wide = df_long.pivot_table(
    index=["country", "country_code", "year", "is_eu", "region", "subregion"],
    columns="indicator_short",
    values="value"
).reset_index()

# ----------------- SIDEBAR FILTERS -----------------
pd_st.sidebar.image("https://img.icons8.com/clouds/100/european-union.png", width=70)
pd_st.sidebar.title("Navigation & Filters")

# 1. Market Group Filter
market_groups = ["All European Markets", "European Union (EU)", "Non-EU", "Nordics", "DACH", "Western Europe", "Southern Europe"]
selected_group = pd_st.sidebar.selectbox("Market Grouping", market_groups)

# Filter country options based on selected Market Group
def get_countries_for_group(group):
    if group == "All European Markets":
        return list(COUNTRIES.keys())
    elif group == "European Union (EU)":
        return [k for k, v in COUNTRIES.items() if v['eu']]
    elif group == "Non-EU":
        return [k for k, v in COUNTRIES.items() if not v['eu']]
    elif group == "Nordics":
        return [k for k, v in COUNTRIES.items() if v['region'] == 'Nordics']
    elif group == "DACH":
        return [k for k, v in COUNTRIES.items() if v['subregion'] == 'DACH']
    elif group == "Western Europe":
        return [k for k, v in COUNTRIES.items() if v['region'] == 'Western Europe']
    elif group == "Southern Europe":
        return [k for k, v in COUNTRIES.items() if v['region'] == 'Southern Europe']
    return list(COUNTRIES.keys())

filtered_iso_codes = get_countries_for_group(selected_group)
group_countries = [COUNTRIES[code]['name'] for code in filtered_iso_codes]

# 2. Country Multi-select (defaults to all countries in the selected group)
selected_countries = pd_st.sidebar.multiselect(
    "Select Target Countries",
    options=sorted(list(set(df_long["country"].unique()))),
    default=sorted(group_countries)
)

# 3. Year range filter
min_year = int(df_long["year"].min())
max_year = int(df_long["year"].max())
selected_year_range = pd_st.sidebar.slider(
    "Historical Period",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Apply filters to dataframes
df_filtered_long = df_long[
    df_long["country"].isin(selected_countries) &
    (df_long["year"] >= selected_year_range[0]) &
    (df_long["year"] <= selected_year_range[1])
]

df_filtered_wide = df_wide[
    df_wide["country"].isin(selected_countries) &
    (df_wide["year"] >= selected_year_range[0]) &
    (df_wide["year"] <= selected_year_range[1])
]

# Sidebar metadata summary
pd_st.sidebar.markdown("---")
pd_st.sidebar.markdown("### Executive Deliverable Details")
pd_st.sidebar.info(
    "**Data Source**: World Bank Public API\n\n"
    "**Pipeline Storage**: SQLite Database, CSV, and Multi-Sheet Excel Workbook.\n\n"
    "**Status**: Automated Pipeline Synced"
)

# ----------------- MAIN PANEL -----------------
# Header Title and Subtitle
pd_st.markdown('<div class="main-title">European Market Intelligence Dashboard</div>', unsafe_allow_html=True)
pd_st.markdown('<div class="main-subtitle">Public economic indicators transformed into an executive market research dashboard for expansion analysis.</div>', unsafe_allow_html=True)

# Tabs navigation
tab1, tab2, tab3, tab4, tab5 = pd_st.tabs([
    "📊 Executive Overview",
    "🔄 Country Comparison",
    "📈 Indicator Trends",
    "🏆 Market Ranking",
    "🔍 Data Explorer"
])

# Compute Latest Non-Null value matrices for KPI calculations & rankings
# To be robust, find the latest available year per country-indicator combination
latest_values = []
for country in df_long["country"].unique():
    country_df = df_long[df_long["country"] == country]
    for ind_short in df_long["indicator_short"].unique():
        ind_country_df = country_df[country_df["indicator_short"] == ind_short]
        # Drop null values and find max year
        non_null_df = ind_country_df.dropna(subset=["value"])
        if not non_null_df.empty:
            latest_row = non_null_df.loc[non_null_df["year"].idxmax()]
            latest_values.append(latest_row)

df_latest = pd.DataFrame(latest_values)
df_latest_wide = df_latest.pivot_table(
    index=["country", "country_code", "is_eu", "region", "subregion"],
    columns="indicator_short",
    values="value"
).reset_index()

# Filter df_latest for selected countries
df_latest_filtered_wide = df_latest_wide[df_latest_wide["country"].isin(selected_countries)]
df_latest_filtered_long = df_latest[df_latest["country"].isin(selected_countries)]


# ----------------- TAB 1: EXECUTIVE OVERVIEW -----------------
with tab1:
    pd_st.markdown("### Executive Key Performance Indicators")
    pd_st.write("Calculated using the latest available reporting year for each country (non-null entries only).")
    
    # Calculate KPIs
    kpi_countries_count = len(selected_countries)
    
    # Latest total population
    latest_pop = df_latest_filtered_wide["Population"].sum() if "Population" in df_latest_filtered_wide else 0
    # Average GDP per Capita
    avg_gdp = df_latest_filtered_wide["GDP per capita"].mean() if "GDP per capita" in df_latest_filtered_wide else 0
    # Average Internet Penetration
    avg_internet = df_latest_filtered_wide["Internet users percentage"].mean() if "Internet users percentage" in df_latest_filtered_wide else 0
    # Average Unemployment Rate
    avg_unempl = df_latest_filtered_wide["Unemployment rate"].mean() if "Unemployment rate" in df_latest_filtered_wide else 0
    # Latest year in filtered dataset
    latest_year_avail = df_filtered_long["year"].max() if not df_filtered_long.empty else "N/A"
    
    # Display KPI Cards
    col1, col2, col3, col4, col5, col6 = pd_st.columns(6)
    
    with col1:
        pd_st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #0d9488;">
            <div class="kpi-label">Countries Analyzed</div>
            <div class="kpi-value">{kpi_countries_count}</div>
            <div class="kpi-subtext">European Markets</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        pop_str = f"{latest_pop / 1e6:.1f}M" if latest_pop > 1e6 else f"{latest_pop:,}"
        pd_st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #2563eb;">
            <div class="kpi-label">Total Population</div>
            <div class="kpi-value">{pop_str}</div>
            <div class="kpi-subtext">Sum of latest records</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        gdp_str = f"${avg_gdp:,.0f}" if avg_gdp > 0 else "N/A"
        pd_st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #4f46e5;">
            <div class="kpi-label">Avg GDP Per Capita</div>
            <div class="kpi-value">{gdp_str}</div>
            <div class="kpi-subtext">Current USD</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        internet_str = f"{avg_internet:.1f}%" if avg_internet > 0 else "N/A"
        pd_st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #f59e0b;">
            <div class="kpi-label">Avg Internet Users</div>
            <div class="kpi-value">{internet_str}</div>
            <div class="kpi-subtext">% of Population</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        unempl_str = f"{avg_unempl:.2f}%" if avg_unempl > 0 else "N/A"
        pd_st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #ef4444;">
            <div class="kpi-label">Avg Unemployment</div>
            <div class="kpi-value">{unempl_str}</div>
            <div class="kpi-subtext">ILO estimate</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col6:
        pd_st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #8b5cf6;">
            <div class="kpi-label">Latest Year</div>
            <div class="kpi-value">{latest_year_avail}</div>
            <div class="kpi-subtext">Max reporting cycle</div>
        </div>
        """, unsafe_allow_html=True)

    pd_st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Visual Layout: Country Benchmarking
    pd_st.markdown("### Country Benchmarking Metrics")
    chart_col1, chart_col2 = pd_st.columns(2)
    
    with chart_col1:
        # GDP per capita Bar Chart
        if "GDP per capita" in df_latest_filtered_wide.columns and not df_latest_filtered_wide.empty:
            df_gdp_sorted = df_latest_filtered_wide.sort_values(by="GDP per capita", ascending=True)
            fig_gdp = px.bar(
                df_gdp_sorted,
                x="GDP per capita",
                y="country",
                orientation="h",
                title="GDP per Capita comparison (Latest Available Year)",
                labels={"GDP per capita": "GDP per Capita (Current USD)", "country": "Country"},
                color="GDP per capita",
                color_continuous_scale="Viridis",
                height=500
            )
            fig_gdp.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=100, r=20, t=50, b=50),
                coloraxis_showscale=False
            )
            pd_st.plotly_chart(fig_gdp, use_container_width=True)
        else:
            pd_st.info("GDP data not available for selected countries.")
            
    with chart_col2:
        # Population bar chart
        if "Population" in df_latest_filtered_wide.columns and not df_latest_filtered_wide.empty:
            df_pop_sorted = df_latest_filtered_wide.sort_values(by="Population", ascending=True)
            fig_pop = px.bar(
                df_pop_sorted,
                x="Population",
                y="country",
                orientation="h",
                title="Total Population comparison (Latest Available Year)",
                labels={"Population": "Total Population", "country": "Country"},
                color="Population",
                color_continuous_scale="Mrybm",
                height=500
            )
            fig_pop.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=100, r=20, t=50, b=50),
                coloraxis_showscale=False
            )
            pd_st.plotly_chart(fig_pop, use_container_width=True)
        else:
            pd_st.info("Population data not available.")

    # Second row of overview charts
    chart_col3, chart_col4 = pd_st.columns(2)
    with chart_col3:
        # Development Bubble Chart (GDP vs Internet users, size = Population)
        if all(c in df_latest_filtered_wide.columns for c in ["GDP per capita", "Internet users percentage", "Population"]) and not df_latest_filtered_wide.empty:
            fig_bubble = px.scatter(
                df_latest_filtered_wide,
                x="GDP per capita",
                y="Internet users percentage",
                size="Population",
                color="region",
                hover_name="country",
                title="Technology Adoption vs Economic Level (Bubble Size = Population)",
                labels={
                    "GDP per capita": "GDP per Capita (Current USD)",
                    "Internet users percentage": "Internet Users (%)",
                    "region": "Market Group"
                },
                size_max=50,
                height=500
            )
            fig_bubble.update_layout(
                plot_bgcolor="rgba(240,244,248,0.5)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=50, r=20, t=50, b=50),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            pd_st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            pd_st.info("Tech adoption comparison details unavailable.")
            
    with chart_col4:
        # Exports comparison
        if "Exports percentage of GDP" in df_latest_filtered_wide.columns and not df_latest_filtered_wide.empty:
            df_exp_sorted = df_latest_filtered_wide.sort_values(by="Exports percentage of GDP", ascending=True)
            fig_exp = px.bar(
                df_exp_sorted,
                x="Exports percentage of GDP",
                y="country",
                orientation="h",
                title="Exports of Goods & Services (% of GDP) (Latest Year)",
                labels={"Exports percentage of GDP": "Exports (% of GDP)", "country": "Country"},
                color="Exports percentage of GDP",
                color_continuous_scale="Tealgrn",
                height=500
            )
            fig_exp.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=100, r=20, t=50, b=50),
                coloraxis_showscale=False
            )
            pd_st.plotly_chart(fig_exp, use_container_width=True)
        else:
            pd_st.info("Exports percentage of GDP comparison data not available.")

# ----------------- TAB 2: COUNTRY COMPARISON -----------------
with tab2:
    pd_st.markdown("### Country-Level Head-to-Head Benchmarking")
    pd_st.write("Select countries in the sidebar to compare their metrics across historical years.")
    
    if len(selected_countries) < 2:
        pd_st.warning("⚠️ Please select at least two countries in the sidebar filters to enable side-by-side comparison.")
    else:
        # Multi-metric comparisons
        metrics_to_compare = list(INDICATOR_SHORT_NAMES.values())
        
        comp_col1, comp_col2 = pd_st.columns(2)
        
        for idx, metric in enumerate(metrics_to_compare):
            target_col = comp_col1 if idx % 2 == 0 else comp_col2
            with target_col:
                # Filter data for this specific metric
                metric_df = df_filtered_long[df_filtered_long["indicator_short"] == metric].dropna(subset=["value"])
                if not metric_df.empty:
                    fig_comp = px.line(
                        metric_df,
                        x="year",
                        y="value",
                        color="country",
                        title=f"{metric} over Time",
                        labels={"value": metric, "year": "Year", "country": "Country"},
                        markers=True,
                        height=400
                    )
                    fig_comp.update_layout(
                        plot_bgcolor="rgba(240,244,248,0.3)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=50, r=20, t=40, b=40),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) if len(selected_countries) <= 5 else dict(orientation="v")
                    )
                    pd_st.plotly_chart(fig_comp, use_container_width=True)
                else:
                    pd_st.info(f"No historical data records found for {metric}.")

# ----------------- TAB 3: INDICATOR TRENDS -----------------
with tab3:
    pd_st.markdown("### Historical Economic Trend Analysis")
    
    # Selection of specific indicator
    selected_ind = pd_st.selectbox("Select Macroeconomic Indicator to Analyze", list(INDICATOR_SHORT_NAMES.values()))
    
    # Filter long df for this indicator and selected countries
    trend_df = df_filtered_long[df_filtered_long["indicator_short"] == selected_ind].dropna(subset=["value"])
    
    if not trend_df.empty:
        # Sort values chronologically
        trend_df = trend_df.sort_values(by=["country", "year"])
        
        # Show Line Chart
        fig_trend = px.line(
            trend_df,
            x="year",
            y="value",
            color="country",
            markers=True,
            title=f"Historical Trend: {selected_ind} ({selected_year_range[0]} - {selected_year_range[1]})",
            labels={"value": selected_ind, "year": "Year", "country": "Country"},
            height=600
        )
        fig_trend.update_layout(
            plot_bgcolor="rgba(240,244,248,0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis=dict(dtick=1)
        )
        pd_st.plotly_chart(fig_trend, use_container_width=True)
        
        # Display statistical distribution summary
        pd_st.markdown("#### Statistical Summary Table (Filtered Countries & Period)")
        summary_data = []
        for c in selected_countries:
            c_trend = trend_df[trend_df["country"] == c]
            if not c_trend.empty:
                summary_data.append({
                    "Country": c,
                    "Starting Value": f"{c_trend.iloc[0]['value']:,.2f}",
                    "Ending Value": f"{c_trend.iloc[-1]['value']:,.2f}",
                    "Min Value": f"{c_trend['value'].min():,.2f}",
                    "Max Value": f"{c_trend['value'].max():,.2f}",
                    "Avg Value": f"{c_trend['value'].mean():,.2f}"
                })
        pd_st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
    else:
        pd_st.warning(f"No available data found for '{selected_ind}' within the selected criteria.")

# ----------------- TAB 4: MARKET RANKING -----------------
with tab4:
    pd_st.markdown("### Country Market Ranking Benchmarks")
    pd_st.write("Rank European countries on specific indicators for a given reporting year.")
    
    rank_col1, rank_col2 = pd_st.columns([1, 3])
    
    with rank_col1:
        # Ranking options
        rank_indicator = pd_st.selectbox("Ranking Metric", list(INDICATOR_SHORT_NAMES.values()), key="rank_ind")
        rank_year = pd_st.selectbox("Target Year", sorted(list(df_long["year"].unique()), reverse=True), key="rank_yr")
        sort_order = pd_st.radio("Ordering Sequence", ["Highest to Lowest", "Lowest to Highest"])
        
    with rank_col2:
        # Filter data for specific year and indicator
        rank_df = df_long[
            (df_long["indicator_short"] == rank_indicator) &
            (df_long["year"] == rank_year) &
            (df_long["country"].isin(selected_countries))
        ].dropna(subset=["value"])
        
        if not rank_df.empty:
            ascending = (sort_order == "Lowest to Highest")
            rank_df_sorted = rank_df.sort_values(by="value", ascending=ascending).reset_index(drop=True)
            rank_df_sorted["Rank"] = rank_df_sorted.index + 1
            
            # Format and show rank table
            rank_display = rank_df_sorted[["Rank", "country", "value"]].copy()
            rank_display = rank_display.rename(columns={"country": "Country", "value": "Value"})
            
            # Display Plotly Ranking Bar Chart
            fig_rank = px.bar(
                rank_df_sorted,
                x="value",
                y="country",
                orientation="h",
                text="value",
                title=f"European Market Rankings: {rank_indicator} in {rank_year}",
                labels={"value": rank_indicator, "country": "Country"},
                color="value",
                color_continuous_scale="Plotly3",
                height=500
            )
            fig_rank.update_traces(texttemplate='%{x:,.2f}', textposition='outside')
            fig_rank.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=100, r=50, t=50, b=50),
                coloraxis_showscale=False
            )
            pd_st.plotly_chart(fig_rank, use_container_width=True)
            
            # Show Table below
            pd_st.markdown("#### Detailed Rankings Table")
            pd_st.dataframe(rank_display, use_container_width=True, hide_index=True)
        else:
            pd_st.warning(f"No records found for '{rank_indicator}' in the year {rank_year} for the selected countries. (The year might not have reporting data yet. Try selecting an earlier year).")

# ----------------- TAB 5: DATA EXPLORER -----------------
with tab5:
    pd_st.markdown("### Interactive Dataset Explorer & Downloads")
    pd_st.write("Browse the processed European economic dataset. You can toggle between Long-format (records) and Wide-format (analytical table).")
    
    # Format selection
    format_toggle = pd_st.radio("Dataset View Format", ["Wide Format (Analytical Row per Year)", "Long Format (Standardized Schema)"])
    
    # Download dataset logic
    csv_file = os.path.join("data", "processed", "europe_market_indicators.csv")
    excel_file = os.path.join("data", "processed", "europe_market_indicators.xlsx")
    
    # Load raw binary data for download buttons
    csv_bytes = b""
    excel_bytes = b""
    try:
        with open(csv_file, "rb") as f:
            csv_bytes = f.read()
        with open(excel_file, "rb") as f:
            excel_bytes = f.read()
    except Exception as e:
        pd_st.warning(f"Downloadable assets could not be loaded: {e}")
        
    dl_col1, dl_col2 = pd_st.columns(2)
    with dl_col1:
        pd_st.download_button(
            label="📥 Download Clean CSV Dataset",
            data=csv_bytes,
            file_name="europe_market_indicators.csv",
            mime="text/csv",
            use_container_width=True
        )
    with dl_col2:
        pd_st.download_button(
            label="📥 Download Professional Excel Report",
            data=excel_bytes,
            file_name="europe_market_indicators.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    pd_st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Display table based on toggle
    if format_toggle == "Long Format (Standardized Schema)":
        pd_st.dataframe(
            df_filtered_long[["country", "country_code", "year", "indicator_name", "indicator_code", "value"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        # Display Wide format with cleaned column names
        display_wide = df_filtered_wide.copy()
        # Drop columns not needed for general view
        display_wide = display_wide.drop(columns=["is_eu", "region", "subregion"])
        pd_st.dataframe(
            display_wide,
            use_container_width=True,
            hide_index=True
        )
