"""
03_ingest_campaigns.py

Purpose:
Load the generated synthetic campaigns.csv file into Snowflake table RAW.CAMPAIGNS.

This script is separate from 01_ingest_spotify_charts.py because campaign generation
runs after the filtered Spotify chart file exists.
"""

# ============================================================
# 1. Imports
# ============================================================

from pathlib import Path
import os

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas


# ============================================================
# 2. Configuration
# ============================================================

CAMPAIGN_CSV_PATH = Path("data/campaigns.csv")

SNOWFLAKE_DATABASE = "MUSIC_KPI"
SNOWFLAKE_SCHEMA = "RAW"
SNOWFLAKE_TABLE = "CAMPAIGNS"


# ============================================================
# 3. Snowflake connection helper
# ============================================================


def connect_to_snowflake():
    """
    Creates a Snowflake connection using environment variables.

    Required environment variables:
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD
    - SNOWFLAKE_WAREHOUSE

    Optional environment variable:
    - SNOWFLAKE_ROLE
    """

    required_vars = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise RuntimeError(
            "Missing Snowflake environment variables: " + ", ".join(missing_vars)
        )

    connection_args = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": SNOWFLAKE_DATABASE,
        "schema": SNOWFLAKE_SCHEMA,
    }

    if os.getenv("SNOWFLAKE_ROLE"):
        connection_args["role"] = os.getenv("SNOWFLAKE_ROLE")

    return snowflake.connector.connect(**connection_args)


# ============================================================
# 4. Snowflake table creation
# ============================================================


def create_campaigns_table(conn):
    """
    Creates RAW.CAMPAIGNS.

    CREATE OR REPLACE TABLE is fine for this MVP because campaign data is generated.
    """

    create_table_sql = f"""
    CREATE OR REPLACE TABLE {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE} (
        CAMPAIGN_ID VARCHAR,
        SPOTIFY_ID VARCHAR,
        TRACK_NAME VARCHAR,
        ARTISTS VARCHAR,
        COUNTRY VARCHAR,
        SNAPSHOT_DATE DATE,
        CAMPAIGN_START_DATE DATE,
        CAMPAIGN_END_DATE DATE,
        CHANNEL VARCHAR,
        SPEND_EUR FLOAT,
        IMPRESSIONS INTEGER,
        CLICKS INTEGER,
        CTR FLOAT,
        CONVERSION_RATE FLOAT,
        ATTRIBUTED_STREAMS INTEGER,
        GENERATION_TYPE VARCHAR
    );
    """

    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {SNOWFLAKE_DATABASE};")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA};")
        cur.execute(create_table_sql)

    print(f"Snowflake table ready: {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}")


# ============================================================
# 5. Campaign cleaning
# ============================================================


def clean_campaigns(campaigns):
    """
    Light cleaning before Snowflake upload.
    Business KPIs like ROAS and CPS are intentionally NOT calculated here.
    Those belong in dbt marts.
    """

    text_columns = [
        "CAMPAIGN_ID",
        "SPOTIFY_ID",
        "TRACK_NAME",
        "ARTISTS",
        "COUNTRY",
        "CHANNEL",
        "GENERATION_TYPE",
    ]

    for col in text_columns:
        campaigns[col] = campaigns[col].astype("string").str.strip()

    campaigns["COUNTRY"] = campaigns["COUNTRY"].str.upper()

    date_columns = ["SNAPSHOT_DATE", "CAMPAIGN_START_DATE", "CAMPAIGN_END_DATE"]
    for col in date_columns:
        campaigns[col] = pd.to_datetime(campaigns[col], errors="coerce").dt.date

    numeric_columns = [
        "SPEND_EUR",
        "IMPRESSIONS",
        "CLICKS",
        "CTR",
        "CONVERSION_RATE",
        "ATTRIBUTED_STREAMS",
    ]

    for col in numeric_columns:
        campaigns[col] = pd.to_numeric(campaigns[col], errors="coerce")

    campaigns = campaigns.dropna(
        subset=["CAMPAIGN_ID", "SPOTIFY_ID", "COUNTRY", "SNAPSHOT_DATE"]
    )

    return campaigns


# ============================================================
# 6. Main load flow
# ============================================================


def main():
    if not CAMPAIGN_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Campaign file not found: {CAMPAIGN_CSV_PATH}\n"
            "Run 02_generate_campaigns.py first."
        )

    campaigns = pd.read_csv(CAMPAIGN_CSV_PATH)
    campaigns = clean_campaigns(campaigns)

    print(f"Campaign rows ready to load: {len(campaigns)}")

    conn = connect_to_snowflake()
    create_campaigns_table(conn)

    success, number_of_chunks, number_of_rows, _ = write_pandas(
        conn=conn,
        df=campaigns,
        table_name=SNOWFLAKE_TABLE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        quote_identifiers=False,
    )

    conn.close()

    if not success:
        raise RuntimeError("Snowflake upload failed for campaigns.csv.")

    print("Done.")
    print(f"Rows uploaded: {number_of_rows}")
    print(f"Snowflake table loaded: {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}")


# ============================================================
# 7. Run script
# ============================================================

if __name__ == "__main__":
    main()
