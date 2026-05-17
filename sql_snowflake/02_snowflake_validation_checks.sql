-- ============================================================
-- Snowflake Validation Checks
-- Project: Music KPI Console - Streaming and Campaign Analytics
-- Purpose: Confirm setup, loaded tables, and join integrity
-- ============================================================

-- 1. Set active Snowflake context
USE WAREHOUSE MUSIC_KPI_WH;
USE DATABASE MUSIC_KPI;
USE SCHEMA RAW;

-- 2. Confirm database exists
SHOW DATABASES LIKE 'MUSIC_KPI';

-- 3. Confirm RAW schema exists
SHOW SCHEMAS IN DATABASE MUSIC_KPI;

-- 4. Confirm warehouse exists
SHOW WAREHOUSES LIKE 'MUSIC_KPI_WH';

-- 5. Count Spotify chart rows
SELECT COUNT(*) AS spotify_rows
FROM SPOTIFY_CHARTS;

-- 6. Count campaign rows
SELECT COUNT(*) AS campaign_rows
FROM CAMPAIGNS;

-- 7. Preview Spotify chart table
SELECT *
FROM SPOTIFY_CHARTS
LIMIT 10;

-- 8. Preview campaign table
SELECT *
FROM CAMPAIGNS
LIMIT 10;

-- 9. Join sanity check
-- Expected result: 50 matching rows. This confirms that every synthetic campaign row links to a real Spotify chart row.


SELECT 
    COUNT(*) AS matching_campaign_rows
FROM RAW.CAMPAIGNS c
INNER JOIN RAW.SPOTIFY_CHARTS s
    ON c.SPOTIFY_ID = s.SPOTIFY_ID
    AND c.COUNTRY = s.COUNTRY
    AND c.SNAPSHOT_DATE = s.SNAPSHOT_DATE;