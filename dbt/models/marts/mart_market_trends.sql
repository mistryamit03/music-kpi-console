-- ============================================================
-- Mart model: mart_market_trends
--
-- Purpose:
-- Final dashboard-ready table for market-level trend analysis.
--
-- Grain:
-- One row per country, chart_week
--
-- Business use:
-- Helps compare market momentum, audio style differences,
-- market spikes, and cross-market track activity.
-- ============================================================

WITH repertoire AS (

    SELECT *
    FROM {{ ref('int_track_lifecycle_and_market_flags') }}

),

country_week_summary AS (

    SELECT
        country,
        chart_week,

        COUNT(DISTINCT spotify_id) AS tracks_tracked,
        SUM(weekly_chart_points) AS total_chart_points,
        AVG(wow_growth_rate) AS avg_wow_growth_rate,

        COUNT_IF(lifecycle_stage = 'Debut') AS debut_tracks,
        COUNT_IF(lifecycle_stage = 'Growing') AS growing_tracks,
        COUNT_IF(lifecycle_stage = 'Peak') AS peak_tracks,
        COUNT_IF(lifecycle_stage = 'Declining') AS declining_tracks,
        COUNT_IF(lifecycle_stage = 'Revived') AS revived_tracks,
        COUNT_IF(market_spike_flag = TRUE) AS market_spike_count,
        COUNT_IF(catalog_revival_flag = TRUE) AS catalog_revival_count,

        COUNT(DISTINCT CASE
            WHEN cross_market_count >= 5 THEN spotify_id
        END) AS multi_market_tracks,

        COUNT(DISTINCT CASE
            WHEN cross_market_count >= 8 THEN spotify_id
        END) AS cross_market_champions,

        AVG(avg_popularity) AS avg_market_popularity,

        AVG(avg_danceability) AS avg_danceability,
        AVG(avg_energy) AS avg_energy,
        AVG(avg_valence) AS avg_valence,
        AVG(avg_acousticness) AS avg_acousticness

    FROM repertoire

    GROUP BY
        country,
        chart_week

),

top_track_per_market AS (

    SELECT
        country,
        chart_week,
        spotify_id AS top_spotify_id,
        track_name AS top_track_name,
        artists AS top_artists,
        weekly_chart_points AS top_track_chart_points,

        ROW_NUMBER() OVER (
            PARTITION BY country, chart_week
            ORDER BY weekly_chart_points DESC
        ) AS track_rank

    FROM repertoire

),

final AS (

    SELECT
        s.country,
        s.chart_week,

        s.tracks_tracked,
        s.total_chart_points,
        s.avg_wow_growth_rate,

        s.debut_tracks,
        s.growing_tracks,
        s.peak_tracks,
        s.declining_tracks,
        s.revived_tracks,
        s.market_spike_count,
        s.catalog_revival_count,

        s.multi_market_tracks,
        s.cross_market_champions,

        s.avg_market_popularity,

        s.avg_danceability,
        s.avg_energy,
        s.avg_valence,
        s.avg_acousticness,

        t.top_spotify_id,
        t.top_track_name,
        t.top_artists,
        t.top_track_chart_points

    FROM country_week_summary s

    LEFT JOIN top_track_per_market t
        ON s.country = t.country
        AND s.chart_week = t.chart_week
        AND t.track_rank = 1

)

SELECT *
FROM final