# Snowflake Setup Documentation

## Project

Music KPI Console - Streaming and Campaign Analytics

## Purpose

Snowflake is used as the cloud data warehouse for this project.

The raw Spotify chart data and synthetic campaign data are loaded into Snowflake before transformation with dbt.

## Snowflake Structure

```text
Snowflake Account
└── MUSIC_KPI database
    └── RAW schema
        ├── SPOTIFY_CHARTS
        └── CAMPAIGNS