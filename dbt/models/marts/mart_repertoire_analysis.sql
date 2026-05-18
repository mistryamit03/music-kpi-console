-- ============================================================
-- Mart model: mart_repertoire_analysis
--
-- Purpose:
-- Final dashboard-ready table for track and repertoire analysis.
--
-- Grain:
-- One row per spotify_id, country, chart_week
--
-- Business use:
-- Helps identify growing tracks, declining tracks, catalog revivals,
-- market spikes, and cross-market opportunities.
-- ============================================================

WITH repertoire_base AS (

    SELECT *
    FROM {{ ref('int_track_lifecycle_and_market_flags') }}

),

ranked_repertoire AS (

    SELECT
        spotify_id,
        track_name,
        artists,
        country,
        chart_week,

        weekly_chart_points,
        previous_week_chart_points,
        wow_chart_points_change,
        wow_growth_rate,

        avg_daily_rank,
        best_daily_rank,
        chart_days,
        avg_popularity,

        album_name,
        album_release_date,

        DATEDIFF('day', album_release_date, chart_week) AS release_age_days,

        avg_danceability,
        avg_energy,
        avg_valence,
        avg_acousticness,
        avg_speechiness,
        avg_instrumentalness,
        avg_liveness,
        avg_tempo,

        cross_market_count,
        lifecycle_stage,
        catalog_revival_flag,
        market_spike_flag,

        ROW_NUMBER() OVER (
            PARTITION BY country, chart_week
            ORDER BY weekly_chart_points DESC
        ) AS market_week_rank,

        CASE
            WHEN catalog_revival_flag = TRUE
                THEN 'Catalog Revival Opportunity'

            WHEN market_spike_flag = TRUE
                THEN 'Market Spike'

            WHEN lifecycle_stage = 'Growing'
                 AND cross_market_count >= 5
                THEN 'Cross-Market Growth'

            WHEN lifecycle_stage = 'Growing'
                THEN 'Local Growth'

            WHEN lifecycle_stage = 'Declining'
                THEN 'Declining Attention Needed'

            WHEN lifecycle_stage = 'Peak'
                THEN 'Peak Performance'

            ELSE 'Monitor'
        END AS repertoire_signal

    FROM repertoire_base

)

SELECT *
FROM ranked_repertoire