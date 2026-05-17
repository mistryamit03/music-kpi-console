# Music KPI Console - Streaming and Campaign Analytics

## Project Overview

Music KPI Console is a portfolio analytics project that simulates how a music label could monitor streaming performance, repertoire movement, market trends, and campaign efficiency.

The project is designed to demonstrate practical data analyst skills relevant to a music and entertainment analytics role, including Python ingestion, SQL-based modelling, dbt transformations, Snowflake data warehousing, and Streamlit dashboarding.

## Business Problem

Music marketing and label teams need to understand which tracks are gaining momentum, which markets show unusual growth, and which campaigns are performing efficiently.

This project answers questions such as:

- Which tracks are growing or declining?
- Which markets show strong chart movement?
- Which songs show cross-market potential?
- Which campaigns appear efficient based on synthetic spend and attributed streams?
- Which KPIs can be calculated from public data, and which require internal label or Spotify for Artists data?

## Data Sources

### Real Data

The project uses the Kaggle dataset:

**Top Spotify Songs in 73 Countries**

The raw file used is:

`universal_top_spotify_songs.csv`

This dataset contains daily Spotify chart rankings, country-level chart positions, track metadata, and audio features.

### Synthetic Data

Campaign data is synthetic and generated for portfolio purposes.

Every synthetic campaign row is linked to a real track, country, and date combination from the filtered Spotify chart data.

## Tech Stack

- Python
- Pandas
- Snowflake
- dbt
- SQL
- Streamlit
- Plotly
- GitHub

## Repository Structure

```text
music-kpi-console/
├── README.md
├── Project.md
├── requirements.txt
├── .gitignore
├── data/
├── scripts/
├── dbt/
└── app/