-- ============================================================
-- Intermediate model: int_track_lifecycle_and_market_flags
--
-- Purpose:
-- Add lifecycle stage, catalog revival flag, market spike flag,
-- and cross-market penetration logic.
--
-- Grain:
-- One row per spotify_id, country, chart_week
--
-- Why this model exists:
-- This model turns weekly chart movement into music business signals.
-- These signals help answer:
-- - Is a track growing?
-- - Is it declining?
-- - Is it peaking?
-- - Is it reviving?
-- - Is one market overperforming?
-- - How widely is the track spreading across markets?
-- ============================================================

WITH weekly_growth AS (

    SELECT *
    FROM {{ ref('int_track_weekly_growth') }}

),

track_market_history AS (

    SELECT
        *,

        MIN(chart_week) OVER (
            PARTITION BY spotify_id, country
        ) AS first_chart_week,

        MAX(weekly_chart_points) OVER (
            PARTITION BY spotify_id, country
        ) AS max_weekly_chart_points,

        LAG(chart_week) OVER (
            PARTITION BY spotify_id, country
            ORDER BY chart_week
        ) AS previous_chart_week

    FROM weekly_growth

),

cross_market_penetration AS (

    SELECT
        spotify_id,
        chart_week,
        COUNT(DISTINCT country) AS cross_market_count
    FROM weekly_growth
    GROUP BY
        spotify_id,
        chart_week

),

market_average_growth AS (

    SELECT
        spotify_id,
        chart_week,
        AVG(wow_growth_rate) AS selected_market_avg_wow_growth
    FROM weekly_growth
    WHERE wow_growth_rate IS NOT NULL
    GROUP BY
        spotify_id,
        chart_week

),

final AS (

    SELECT
        h.spotify_id,
        h.track_name,
        h.artists,
        h.country,
        h.chart_week,

        h.weekly_chart_points,
        h.previous_week_chart_points,
        h.wow_chart_points_change,
        h.wow_growth_rate,

        h.avg_daily_rank,
        h.best_daily_rank,
        h.chart_days,
        h.avg_popularity,

        h.album_name,
        h.album_release_date,

        h.avg_danceability,
        h.avg_energy,
        h.avg_valence,
        h.avg_acousticness,
        h.avg_speechiness,
        h.avg_instrumentalness,
        h.avg_liveness,
        h.avg_tempo,

        p.cross_market_count,
        m.selected_market_avg_wow_growth,

        CASE
            WHEN h.previous_week_chart_points IS NULL
                THEN 'Debut'

            WHEN DATEDIFF('day', h.previous_chart_week, h.chart_week) > 90
                THEN 'Revived'

            WHEN h.weekly_chart_points >= 0.90 * h.max_weekly_chart_points
                THEN 'Peak'

            WHEN h.wow_growth_rate >= 0.20
                THEN 'Growing'

            WHEN h.wow_growth_rate <= -0.20
                THEN 'Declining'

            ELSE 'Stable'
        END AS lifecycle_stage,

        CASE
            WHEN DATEDIFF('day', h.previous_chart_week, h.chart_week) > 90
                THEN TRUE
            ELSE FALSE
        END AS catalog_revival_flag,

        CASE
            WHEN h.wow_growth_rate >= 0.20
                 AND m.selected_market_avg_wow_growth > 0
                 AND h.wow_growth_rate >= 3 * m.selected_market_avg_wow_growth
                THEN TRUE
            ELSE FALSE
        END AS market_spike_flag

    FROM track_market_history h

    LEFT JOIN cross_market_penetration p
        ON h.spotify_id = p.spotify_id
        AND h.chart_week = p.chart_week

    LEFT JOIN market_average_growth m
        ON h.spotify_id = m.spotify_id
        AND h.chart_week = m.chart_week

)

SELECT *
FROM final