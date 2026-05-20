# ============================================================
# Music KPI Console - Streamlit Dashboard
# Project: Streaming and Campaign Analytics
#
# Purpose:
# This app connects to Snowflake mart tables created by dbt.
# It helps analyse repertoire performance, market trends,
# synthetic campaign performance, and KPI definitions.
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector


# ============================================================
# 1. Page configuration
# ============================================================

st.set_page_config(
    page_title="Music KPI Console",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state= "expanded"
)


# ============================================================
# 2. Snowflake connection
# ============================================================

def get_snowflake_connection():
    """
    Creates a connection to Snowflake using Streamlit secrets.

    The credentials are stored in:
    app/.streamlit/secrets.toml

    This file is ignored by GitHub for security reasons.
    """

    return snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        role=st.secrets["snowflake"]["role"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
    )


@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    """
    Runs a SQL query against Snowflake and returns a pandas DataFrame.

    ttl=600 means Streamlit caches the query result for 10 minutes.
    This avoids unnecessary repeated Snowflake queries while testing.
    """

    conn = get_snowflake_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        df = cursor.fetch_pandas_all()
        return df

    finally:
        cursor.close()
        conn.close()


# ============================================================
# 3. Helper functions
# ============================================================

def format_percentage(value):
    """Formats decimal values as percentages."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def format_number(value):
    """Formats large numbers with commas."""
    if pd.isna(value):
        return "N/A"
    return f"{value:,.0f}"


# ============================================================
# 4. Load filter values
# ============================================================

@st.cache_data(ttl=600)
def get_filter_values():
    """
    Gets available countries and date ranges from the repertoire mart.
    """

    query = """
        SELECT
            MIN(CHART_WEEK) AS MIN_DATE,
            MAX(CHART_WEEK) AS MAX_DATE
        FROM MUSIC_KPI.ANALYTICS.MART_REPERTOIRE_ANALYSIS
    """

    date_df = run_query(query)

    country_query = """
        SELECT DISTINCT COUNTRY
        FROM MUSIC_KPI.ANALYTICS.MART_REPERTOIRE_ANALYSIS
        ORDER BY COUNTRY
    """

    country_df = run_query(country_query)

    return date_df, country_df


# ============================================================
# 5. App header
# ============================================================

st.title("🎵 Music KPI Console")
st.caption("Streaming and Campaign Analytics | Snowflake + dbt + Streamlit")

st.info(
    "Data source notice: Spotify chart data is real and sourced from Kaggle. "
    "Campaign data is synthetic and generated for portfolio simulation. "
    "All campaign rows are linked to real track, market, and date combinations."
)


# ============================================================
# 6. Sidebar filters
# ============================================================

date_df, country_df = get_filter_values()

available_countries = country_df["COUNTRY"].dropna().tolist()

min_date = pd.to_datetime(date_df["MIN_DATE"].iloc[0]).date()
max_date = pd.to_datetime(date_df["MAX_DATE"].iloc[0]).date()

st.sidebar.header("Dashboard Filters")

selected_countries = st.sidebar.multiselect(
    "Select markets",
    options=available_countries,
    default=available_countries
)

selected_date_range = st.sidebar.date_input(
    "Select chart week range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(selected_date_range) != 2:
    st.warning("Please select a start and end date.")
    st.stop()

start_date = selected_date_range[0]
end_date = selected_date_range[1]

if not selected_countries:
    st.warning("Please select at least one market.")
    st.stop()

country_filter = ", ".join([f"'{country}'" for country in selected_countries])


# ============================================================
# 7. Load filtered mart data
# ============================================================

repertoire_query = f"""
    SELECT *
    FROM MUSIC_KPI.ANALYTICS.MART_REPERTOIRE_ANALYSIS
    WHERE COUNTRY IN ({country_filter})
      AND CHART_WEEK BETWEEN '{start_date}' AND '{end_date}'
"""

market_query = f"""
    SELECT *
    FROM MUSIC_KPI.ANALYTICS.MART_MARKET_TRENDS
    WHERE COUNTRY IN ({country_filter})
      AND CHART_WEEK BETWEEN '{start_date}' AND '{end_date}'
"""

campaign_query = f"""
    SELECT *
    FROM MUSIC_KPI.ANALYTICS.MART_CAMPAIGN_PERFORMANCE
    WHERE COUNTRY IN ({country_filter})
"""

kpi_catalog_query = """
    SELECT *
    FROM MUSIC_KPI.ANALYTICS.MART_KPI_CATALOG
    ORDER BY KPI_TIER, KPI_NAME
"""

repertoire_df = run_query(repertoire_query)
market_df = run_query(market_query)
campaign_df = run_query(campaign_query)
kpi_catalog_df = run_query(kpi_catalog_query)

# ============================================================
# Data safety fixes for Streamlit visualisations
# ============================================================

# Plotly cannot use NaN values for bubble sizes.
# LIFT_VS_CONTROL can be NULL when no control-market comparison exists.
# So we create a safe positive bubble-size column for the scatter plot.

if not campaign_df.empty:
    campaign_df["LIFT_VS_CONTROL"] = pd.to_numeric(
        campaign_df["LIFT_VS_CONTROL"],
        errors="coerce"
    )

    campaign_df["LIFT_SIZE"] = (
        campaign_df["LIFT_VS_CONTROL"]
        .fillna(0)
        .abs()
        .clip(lower=0.01)
    )

# ============================================================
# 8. Tabs
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Repertoire Analysis",
        "Market Trends",
        "Campaign Performance",
        "KPI Catalog"
    ]
)


# ============================================================
# 9. Tab 1 - Repertoire Analysis
# ============================================================

with tab1:
    st.header("Repertoire Analysis")
    st.caption("Track-level performance, lifecycle stage, catalog revival, and market spike signals.")

    total_tracks = repertoire_df["SPOTIFY_ID"].nunique()
    avg_wow_growth = repertoire_df["WOW_GROWTH_RATE"].mean()
    catalog_revivals = repertoire_df[repertoire_df["CATALOG_REVIVAL_FLAG"] == True].shape[0]
    market_spikes = repertoire_df[repertoire_df["MARKET_SPIKE_FLAG"] == True].shape[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Tracks Tracked", format_number(total_tracks))
    col2.metric("Avg WoW Growth", format_percentage(avg_wow_growth))
    col3.metric("Catalog Revivals", format_number(catalog_revivals))
    col4.metric("Market Spikes", format_number(market_spikes))

    st.divider()

    top_tracks = (
        repertoire_df
        .groupby(["TRACK_NAME", "ARTISTS"], as_index=False)["WEEKLY_CHART_POINTS"]
        .sum()
        .sort_values("WEEKLY_CHART_POINTS", ascending=False)
        .head(10)
    )

    fig_top_tracks = px.bar(
        top_tracks,
        x="WEEKLY_CHART_POINTS",
        y="TRACK_NAME",
        orientation="h",
        hover_data=["ARTISTS"],
        title="Top 10 Tracks by Weekly Chart Points"
    )

    st.plotly_chart(fig_top_tracks, use_container_width=True)

    lifecycle_counts = (
        repertoire_df
        .groupby("LIFECYCLE_STAGE", as_index=False)
        .size()
        .rename(columns={"size": "ROW_COUNT"})
    )

    fig_lifecycle = px.pie(
        lifecycle_counts,
        names="LIFECYCLE_STAGE",
        values="ROW_COUNT",
        title="Lifecycle Stage Distribution"
    )

    st.plotly_chart(fig_lifecycle, use_container_width=True)

    st.subheader("Top Repertoire Signals")

    signal_table = (
        repertoire_df[
            [
                "TRACK_NAME",
                "ARTISTS",
                "COUNTRY",
                "CHART_WEEK",
                "WEEKLY_CHART_POINTS",
                "WOW_GROWTH_RATE",
                "LIFECYCLE_STAGE",
                "REPERTOIRE_SIGNAL",
                "CROSS_MARKET_COUNT"
            ]
        ]
        .sort_values("WEEKLY_CHART_POINTS", ascending=False)
        .head(50)
    )

    st.dataframe(signal_table, use_container_width=True)


# ============================================================
# 10. Tab 2 - Market Trends
# ============================================================

with tab2:
    st.header("Market Trends")
    st.caption("Country-week level performance and market movement signals.")

    total_market_spikes = market_df["MARKET_SPIKE_COUNT"].sum()
    multi_market_tracks = market_df["MULTI_MARKET_TRACKS"].sum()
    cross_market_champions = market_df["CROSS_MARKET_CHAMPIONS"].sum()
    avg_market_growth = market_df["AVG_WOW_GROWTH_RATE"].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Market Spikes", format_number(total_market_spikes))
    col2.metric("Multi-Market Tracks", format_number(multi_market_tracks))
    col3.metric("Cross-Market Champions", format_number(cross_market_champions))
    col4.metric("Avg Market Growth", format_percentage(avg_market_growth))

    st.divider()

    fig_market_points = px.line(
        market_df,
        x="CHART_WEEK",
        y="TOTAL_CHART_POINTS",
        color="COUNTRY",
        title="Market Chart Activity Over Time"
    )

    st.plotly_chart(fig_market_points, use_container_width=True)

    latest_market_week = market_df["CHART_WEEK"].max()
    latest_market_df = market_df[market_df["CHART_WEEK"] == latest_market_week]

    fig_market_bar = px.bar(
        latest_market_df.sort_values("TOTAL_CHART_POINTS", ascending=False),
        x="COUNTRY",
        y="TOTAL_CHART_POINTS",
        title=f"Latest Market Activity by Country ({latest_market_week})"
    )

    st.plotly_chart(fig_market_bar, use_container_width=True)

    st.subheader("Top Track per Market")

    market_table = market_df[
        [
            "COUNTRY",
            "CHART_WEEK",
            "TRACKS_TRACKED",
            "TOTAL_CHART_POINTS",
            "GROWING_TRACKS",
            "DECLINING_TRACKS",
            "MARKET_SPIKE_COUNT",
            "TOP_TRACK_NAME",
            "TOP_ARTISTS"
        ]
    ].sort_values(["CHART_WEEK", "TOTAL_CHART_POINTS"], ascending=[False, False])

    st.dataframe(market_table, use_container_width=True)


# ============================================================
# 11. Tab 3 - Campaign Performance
# ============================================================

with tab3:
    st.header("Campaign Performance")
    st.caption("Synthetic campaign performance linked to real track-market-date combinations.")

    st.warning(
        "Campaign data is synthetic. It is used to simulate marketing analytics logic "
        "because real music campaign spend data is not publicly available."
    )

    total_spend = campaign_df["SPEND_EUR"].sum()
    avg_roas = campaign_df["ROAS_PROXY"].mean()
    avg_cps = campaign_df["COST_PER_STREAM"].mean()
    active_campaigns = campaign_df["CAMPAIGN_ID"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Spend EUR", f"€{total_spend:,.0f}")
    col2.metric("Avg ROAS Proxy", f"{avg_roas:.2f}")
    col3.metric("Avg Cost per Stream", f"€{avg_cps:.4f}")
    col4.metric("Campaigns", format_number(active_campaigns))

    st.divider()

    fig_channel_roas = px.bar(
        campaign_df.groupby("CHANNEL", as_index=False)["ROAS_PROXY"].mean(),
        x="CHANNEL",
        y="ROAS_PROXY",
        title="Average ROAS Proxy by Channel"
    )

    st.plotly_chart(fig_channel_roas, use_container_width=True)

    fig_spend_streams = px.scatter(
        campaign_df,
        x="SPEND_EUR",
        y="ATTRIBUTED_STREAMS",
        color="CHANNEL",
        size="LIFT_SIZE",
        hover_data=[
            "TRACK_NAME",
            "ARTISTS",
            "COUNTRY",
            "LIFT_VS_CONTROL",
            "CAMPAIGN_PERFORMANCE_SIGNAL"
        ],
        title="Spend vs Attributed Streams"
    )

    st.plotly_chart(fig_spend_streams, use_container_width=True)

    st.subheader("Campaign Detail Table")

    campaign_table = campaign_df[
        [
            "CAMPAIGN_ID",
            "TRACK_NAME",
            "ARTISTS",
            "COUNTRY",
            "CHANNEL",
            "SPEND_EUR",
            "ATTRIBUTED_STREAMS",
            "COST_PER_STREAM",
            "ROAS_PROXY",
            "LIFT_VS_CONTROL",
            "CAMPAIGN_EFFICIENCY_ALERT",
            "CAMPAIGN_PERFORMANCE_SIGNAL"
        ]
    ].sort_values("ROAS_PROXY", ascending=False)

    st.dataframe(campaign_table, use_container_width=True)


# ============================================================
# 12. Tab 4 - KPI Catalog
# ============================================================

with tab4:
    st.header("KPI Catalog")
    st.caption("Explains which music analytics KPIs are computed, synthetic, or documented only.")

    st.dataframe(kpi_catalog_df, use_container_width=True)

    st.markdown(
        """
        **How to read this tab:**

        - Tier 1 KPIs are computed from real Spotify chart data.
        - Tier 2 KPIs are computed from synthetic campaign data.
        - Tier 3 KPIs are documented only because they require private platform or label data.
        """
    )