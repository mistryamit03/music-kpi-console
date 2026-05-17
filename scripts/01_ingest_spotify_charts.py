"""
01_ingest_spotify_charts.py

Purpose:
1. Read the large Kaggle Spotify chart CSV with pandas.
2. Do light file-level preprocessing before Snowflake:
   - Filter to selected markets
   - Filter to the latest 90-day window in the dataset
   - Convert date columns
   - Strip whitespace from text columns
   - Drop rows with missing spotify_id or country
   - Standardise country codes to uppercase
3. Save a smaller filtered CSV locally.
4. Optionally load the filtered data into Snowflake table RAW.SPOTIFY_CHARTS.

Important:
- Business logic stays OUT of this script.
- KPI logic such as lifecycle stage, WoW growth, market spikes, ROAS, and joins should be done later in dbt.
"""

# ============================================================
# 1. Imports
# ============================================================

from pathlib import Path
from datetime import timedelta
import os

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas


# ============================================================
# 2. Configuration - change these values if needed
# ============================================================

# Path to the original Kaggle CSV you downloaded.
RAW_CSV_PATH = Path("data/universal_top_spotify_songs.csv")

# Small filtered output file. The campaign generator will use this file.
FILTERED_OUTPUT_PATH = Path("data/spotify_charts_filtered.csv")

# Markets for the MVP.
# This follows the project blueprint: Germany + major international benchmark markets.
# If you want a stronger GSA focus later, you can replace JP/BR with AT/CH.
MARKETS_TO_KEEP = ["DE", "FR", "IT", "GB", "US", "JP", "BR", "ES"]

# Latest N-day window based on the max snapshot_date inside the dataset.
# Using 90 matches the blueprint window: max_date 2025-06-11 -> start_date 2025-03-13.
DAYS_BACK = 90

# Chunk size keeps memory usage controlled for the 474 MB CSV.
CHUNK_SIZE = 100_000

# Set this to True only when Snowflake credentials are ready.
# Keep False when you only want to test filtering and create the local filtered CSV.
LOAD_TO_SNOWFLAKE = False

# Snowflake target objects.
SNOWFLAKE_DATABASE = "MUSIC_KPI"
SNOWFLAKE_SCHEMA = "RAW"
SNOWFLAKE_TABLE = "SPOTIFY_CHARTS"


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

    Why environment variables?
    Because credentials should never be hardcoded into GitHub files.
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
            "Missing Snowflake environment variables: "
            + ", ".join(missing_vars)
            + "\nSet them before running with LOAD_TO_SNOWFLAKE = True."
        )

    connection_args = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": SNOWFLAKE_DATABASE,
        "schema": SNOWFLAKE_SCHEMA,
    }

    # Role is optional. Add it only if it exists.
    if os.getenv("SNOWFLAKE_ROLE"):
        connection_args["role"] = os.getenv("SNOWFLAKE_ROLE")

    return snowflake.connector.connect(**connection_args)


# ============================================================
# 4. Snowflake table creation
# ============================================================


def create_spotify_charts_table(conn):
    """
    Creates the database, schema, and RAW.SPOTIFY_CHARTS table.

    CREATE OR REPLACE TABLE is intentional here because this is an MVP project.
    Each clean run should replace the old loaded version with the new one.
    """

    create_table_sql = f"""
    CREATE OR REPLACE TABLE {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE} (
        SPOTIFY_ID VARCHAR,
        NAME VARCHAR,
        ARTISTS VARCHAR,
        DAILY_RANK INTEGER,
        DAILY_MOVEMENT INTEGER,
        WEEKLY_MOVEMENT INTEGER,
        COUNTRY VARCHAR,
        SNAPSHOT_DATE DATE,
        POPULARITY INTEGER,
        IS_EXPLICIT BOOLEAN,
        DURATION_MS INTEGER,
        ALBUM_NAME VARCHAR,
        ALBUM_RELEASE_DATE DATE,
        DANCEABILITY FLOAT,
        ENERGY FLOAT,
        KEY INTEGER,
        LOUDNESS FLOAT,
        MODE INTEGER,
        SPEECHINESS FLOAT,
        ACOUSTICNESS FLOAT,
        INSTRUMENTALNESS FLOAT,
        LIVENESS FLOAT,
        VALENCE FLOAT,
        TEMPO FLOAT,
        TIME_SIGNATURE INTEGER
    );
    """

    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {SNOWFLAKE_DATABASE};")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA};")
        cur.execute(create_table_sql)

    print(f"Snowflake table ready: {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}")


# ============================================================
# 5. Find latest available date in the large CSV
# ============================================================


def find_dataset_max_date(csv_path):
    """
    Finds the latest snapshot_date in the source file without loading the full file.

    Why this exists:
    The dataset is large, so we scan only the snapshot_date column in chunks.
    """

    max_date = None

    for chunk in pd.read_csv(csv_path, usecols=["snapshot_date"], chunksize=CHUNK_SIZE):
        chunk_dates = pd.to_datetime(chunk["snapshot_date"], errors="coerce")
        chunk_max = chunk_dates.max()

        if max_date is None or chunk_max > max_date:
            max_date = chunk_max

    if max_date is None or pd.isna(max_date):
        raise ValueError("Could not find a valid snapshot_date in the CSV.")

    return max_date


# ============================================================
# 6. Cleaning and filtering logic
# ============================================================


def clean_and_filter_chunk(chunk, start_date, end_date):
    """
    Cleans one chunk of the Spotify chart CSV.

    This is intentionally light preprocessing only:
    - text cleanup
    - country cleanup
    - date conversion
    - null removal
    - market/date filtering

    It does NOT calculate KPIs.
    """

    # ----------------------------
    # 6.1 Strip whitespace from text columns
    # ----------------------------
    text_columns = [
        "spotify_id",
        "name",
        "artists",
        "country",
        "album_name",
    ]

    for col in text_columns:
        if col in chunk.columns:
            chunk[col] = chunk[col].astype("string").str.strip()

    # ----------------------------
    # 6.2 Standardise country codes
    # ----------------------------
    chunk["country"] = chunk["country"].astype("string").str.strip().str.upper()

    # ----------------------------
    # 6.3 Convert dates
    # ----------------------------
    chunk["snapshot_date"] = pd.to_datetime(chunk["snapshot_date"], errors="coerce")
    chunk["album_release_date"] = pd.to_datetime(chunk["album_release_date"], errors="coerce")

    # ----------------------------
    # 6.4 Drop rows that would break joins later
    # ----------------------------
    chunk = chunk.dropna(subset=["spotify_id", "country", "snapshot_date"])

    # ----------------------------
    # 6.5 Filter to selected markets and date window
    # ----------------------------
    chunk = chunk[
        chunk["country"].isin(MARKETS_TO_KEEP)
        & (chunk["snapshot_date"] >= start_date)
        & (chunk["snapshot_date"] <= end_date)
    ].copy()

    if chunk.empty:
        return chunk

    # ----------------------------
    # 6.6 Make numeric columns clean and predictable
    # ----------------------------
    numeric_columns = [
        "daily_rank",
        "daily_movement",
        "weekly_movement",
        "popularity",
        "duration_ms",
        "danceability",
        "energy",
        "key",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "time_signature",
    ]

    for col in numeric_columns:
        chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

    # ----------------------------
    # 6.7 Convert dates to Python date objects for Snowflake DATE columns
    # ----------------------------
    chunk["snapshot_date"] = chunk["snapshot_date"].dt.date
    chunk["album_release_date"] = chunk["album_release_date"].dt.date
    chunk["album_release_date"] = chunk["album_release_date"].where(
        pd.notna(chunk["album_release_date"]), None
    )

    # ----------------------------
    # 6.8 Keep columns in the original expected order
    # ----------------------------
    expected_columns = [
        "spotify_id",
        "name",
        "artists",
        "daily_rank",
        "daily_movement",
        "weekly_movement",
        "country",
        "snapshot_date",
        "popularity",
        "is_explicit",
        "duration_ms",
        "album_name",
        "album_release_date",
        "danceability",
        "energy",
        "key",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "time_signature",
    ]

    chunk = chunk[expected_columns]

    # Snowflake table columns are uppercase, so make the DataFrame columns uppercase too.
    chunk.columns = [col.upper() for col in chunk.columns]

    return chunk


# ============================================================
# 7. Main ingestion flow
# ============================================================


def main():
    """
    Main script flow:
    1. Validate source file exists.
    2. Find latest snapshot_date.
    3. Define latest 90-day window.
    4. Process the large CSV in chunks.
    5. Save filtered CSV locally.
    6. Optionally upload chunks to Snowflake.
    """

    if not RAW_CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found: {RAW_CSV_PATH}\n"
            "Put universal_top_spotify_songs.csv inside the data/ folder."
        )

    FILTERED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove old filtered output so this run starts clean.
    if FILTERED_OUTPUT_PATH.exists():
        FILTERED_OUTPUT_PATH.unlink()

    print("Finding latest date in the source CSV...")
    end_date = find_dataset_max_date(RAW_CSV_PATH)
    start_date = end_date - timedelta(days=DAYS_BACK)

    print(f"Markets selected: {MARKETS_TO_KEEP}")
    print(f"Date window: {start_date.date()} to {end_date.date()}")

    conn = None

    if LOAD_TO_SNOWFLAKE:
        print("Connecting to Snowflake...")
        conn = connect_to_snowflake()
        create_spotify_charts_table(conn)
    else:
        print("LOAD_TO_SNOWFLAKE is False. Only the filtered local CSV will be created.")

    total_filtered_rows = 0
    first_output_chunk = True

    print("Reading, cleaning, filtering, and writing chunks...")

    # Read country as string because global rows have NULL country values.
    dtype_overrides = {
        "spotify_id": "string",
        "name": "string",
        "artists": "string",
        "country": "string",
        "album_name": "string",
    }

    for chunk_number, chunk in enumerate(
        pd.read_csv(RAW_CSV_PATH, chunksize=CHUNK_SIZE, dtype=dtype_overrides),
        start=1,
    ):
        cleaned_chunk = clean_and_filter_chunk(chunk, start_date, end_date)

        if cleaned_chunk.empty:
            continue

        total_filtered_rows += len(cleaned_chunk)

        # Save the filtered data locally. This file becomes the input for generate_campaigns.py.
        cleaned_chunk.to_csv(
            FILTERED_OUTPUT_PATH,
            mode="a",
            index=False,
            header=first_output_chunk,
        )
        first_output_chunk = False

        # Upload the same cleaned chunk to Snowflake if enabled.
        if LOAD_TO_SNOWFLAKE:
            success, number_of_chunks, number_of_rows, _ = write_pandas(
                conn=conn,
                df=cleaned_chunk,
                table_name=SNOWFLAKE_TABLE,
                database=SNOWFLAKE_DATABASE,
                schema=SNOWFLAKE_SCHEMA,
                quote_identifiers=False,
            )

            if not success:
                raise RuntimeError(f"Snowflake upload failed on chunk {chunk_number}.")

            print(f"Chunk {chunk_number}: uploaded {number_of_rows} rows to Snowflake.")
        else:
            print(f"Chunk {chunk_number}: wrote {len(cleaned_chunk)} rows locally.")

    if conn:
        conn.close()

    print("Done.")
    print(f"Filtered rows written: {total_filtered_rows}")
    print(f"Local filtered file: {FILTERED_OUTPUT_PATH}")

    if LOAD_TO_SNOWFLAKE:
        print(f"Snowflake table loaded: {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{SNOWFLAKE_TABLE}")


# ============================================================
# 8. Run script
# ============================================================

if __name__ == "__main__":
    main()
