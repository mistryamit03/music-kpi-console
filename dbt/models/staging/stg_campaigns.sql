-- ============================================================
-- Staging model: stg_campaigns
-- Purpose:
-- Clean and standardise synthetic campaign data before downstream campaign KPI logic.
--
-- Important:
-- This campaign data is synthetic and used only for portfolio simulation.
-- ROAS, CPS, and lift calculations will be handled in mart models.
-- ============================================================

WITH source_data AS (

    SELECT *
    FROM {{ source('raw', 'campaigns') }}

),

cleaned AS (

    SELECT
        TRIM(CAMPAIGN_ID) AS campaign_id,
        TRIM(SPOTIFY_ID) AS spotify_id,
        TRIM(TRACK_NAME) AS track_name,
        TRIM(ARTISTS) AS artists,

        UPPER(TRIM(COUNTRY)) AS country,
        CAST(SNAPSHOT_DATE AS DATE) AS snapshot_date,

        CAST(CAMPAIGN_START_DATE AS DATE) AS campaign_start_date,
        CAST(CAMPAIGN_END_DATE AS DATE) AS campaign_end_date,

        TRIM(CHANNEL) AS channel,

        CAST(SPEND_EUR AS FLOAT) AS spend_eur,
        CAST(IMPRESSIONS AS INTEGER) AS impressions,
        CAST(CLICKS AS INTEGER) AS clicks,
        CAST(CTR AS FLOAT) AS ctr,
        CAST(CONVERSION_RATE AS FLOAT) AS conversion_rate,
        CAST(ATTRIBUTED_STREAMS AS INTEGER) AS attributed_streams,

        TRIM(GENERATION_TYPE) AS generation_type

    FROM source_data

    WHERE CAMPAIGN_ID IS NOT NULL
      AND SPOTIFY_ID IS NOT NULL
      AND COUNTRY IS NOT NULL
      AND SNAPSHOT_DATE IS NOT NULL

)

SELECT *
FROM cleaned