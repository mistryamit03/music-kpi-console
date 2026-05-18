-- ============================================================
-- Staging model: stg_spotify_charts
-- Purpose:
-- Clean and standardise raw Spotify chart data before downstream KPI logic.
--
-- Important:
-- This model does not calculate business KPIs.
-- KPI logic such as chart points, WoW growth, lifecycle stage,
-- and market spikes will be handled in intermediate/mart models.
-- ============================================================

WITH source_data AS (

    SELECT *
    FROM {{ source('raw', 'spotify_charts') }}

),

cleaned AS (

    SELECT
        TRIM(SPOTIFY_ID) AS spotify_id,
        TRIM(NAME) AS track_name,
        TRIM(ARTISTS) AS artists,

        CAST(DAILY_RANK AS INTEGER) AS daily_rank,
        CAST(DAILY_MOVEMENT AS INTEGER) AS daily_movement,
        CAST(WEEKLY_MOVEMENT AS INTEGER) AS weekly_movement,

        UPPER(TRIM(COUNTRY)) AS country,
        CAST(SNAPSHOT_DATE AS DATE) AS snapshot_date,

        CAST(POPULARITY AS INTEGER) AS popularity,
        CAST(IS_EXPLICIT AS BOOLEAN) AS is_explicit,
        CAST(DURATION_MS AS INTEGER) AS duration_ms,

        TRIM(ALBUM_NAME) AS album_name,
        CAST(ALBUM_RELEASE_DATE AS DATE) AS album_release_date,

        CAST(DANCEABILITY AS FLOAT) AS danceability,
        CAST(ENERGY AS FLOAT) AS energy,
        CAST("KEY" AS INTEGER) AS musical_key,
        CAST(LOUDNESS AS FLOAT) AS loudness,
        CAST(MODE AS INTEGER) AS mode,
        CAST(SPEECHINESS AS FLOAT) AS speechiness,
        CAST(ACOUSTICNESS AS FLOAT) AS acousticness,
        CAST(INSTRUMENTALNESS AS FLOAT) AS instrumentalness,
        CAST(LIVENESS AS FLOAT) AS liveness,
        CAST(VALENCE AS FLOAT) AS valence,
        CAST(TEMPO AS FLOAT) AS tempo,
        CAST(TIME_SIGNATURE AS INTEGER) AS time_signature

    FROM source_data

    WHERE SPOTIFY_ID IS NOT NULL
      AND COUNTRY IS NOT NULL
      AND SNAPSHOT_DATE IS NOT NULL

)

SELECT *
FROM cleaned