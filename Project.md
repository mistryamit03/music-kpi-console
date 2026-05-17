# Project Blueprint - Music KPI Console

## 1. Project Purpose

This project simulates a music analytics workflow for streaming and campaign performance analysis.

The goal is to build a compact but realistic analytics pipeline that shows how a music label could monitor repertoire performance, market trends, and campaign efficiency.

## 2. Role Alignment

This project is aligned with a Junior Data Analyst role in the music industry.

It demonstrates the ability to:

- Analyse diverse data sources
- Build dashboards and reports
- Translate data into business recommendations
- Use Python for technical process improvement
- Monitor trends and repertoire performance
- Communicate insights through data storytelling

## 3. Main Business Questions

The project focuses on the following questions:

1. Which tracks are gaining or losing chart momentum?
2. Which markets show unusual spikes in performance?
3. Which songs have strong cross-market potential?
4. Which campaign channels appear efficient?
5. Which KPIs can be calculated from public data?
6. Which KPIs would require internal music label data?

## 4. Data Strategy

### Real Dataset

The real dataset contains Spotify daily chart data across multiple countries.

The full raw file is large, so Python preprocessing is used before loading data into Snowflake.

### Filtered Scope

The project will filter the dataset to selected markets and a recent 90-day period.

Selected markets:

- DE
- FR
- IT
- GB
- US
- JP
- BR
- ES

### Synthetic Campaign Dataset

Campaign data is generated separately using Python.

The campaign dataset is synthetic but linked to real track, country, and date combinations from the filtered Spotify chart data.

## 5. Architecture

```text
Kaggle CSV
↓
Python ingestion and preprocessing
↓
Snowflake RAW tables
↓
dbt staging, intermediate, and marts models
↓
Streamlit dashboard