-- ============================================================
-- Intermediate model: int_track_weekly_growth
--
-- Purpose:
-- Calculate week-over-week growth for each track in each market.
--
-- Grain:
-- One row per spotify_id, country, chart_week
--
-- Why this model exists:
-- Week-over-week growth helps identify tracks gaining or losing momentum.
-- This is central for trend monitoring and repertoire analysis.
-- ============================================================

WITH weekly_data AS (

    SELECT *
    FROM {{ ref('int_track_weekly_aggregates') }}

),

growth_calculation AS (

    SELECT
        spotify_id,
        track_name,
        artists,
        country,
        chart_week,

        weekly_chart_points,
        avg_daily_chart_points,
        avg_daily_rank,
        best_daily_rank,
        chart_days,
        avg_popularity,

        album_name,
        album_release_date,

        avg_danceability,
        avg_energy,
        avg_valence,
        avg_acousticness,
        avg_speechiness,
        avg_instrumentalness,
        avg_liveness,
        avg_tempo,

        LAG(weekly_chart_points) OVER (
            PARTITION BY spotify_id, country
            ORDER BY chart_week
        ) AS previous_week_chart_points,

        weekly_chart_points
        - LAG(weekly_chart_points) OVER (
            PARTITION BY spotify_id, country
            ORDER BY chart_week
        ) AS wow_chart_points_change,

        CASE
            WHEN LAG(weekly_chart_points) OVER (
                PARTITION BY spotify_id, country
                ORDER BY chart_week
            ) IS NULL
                THEN NULL

            WHEN LAG(weekly_chart_points) OVER (
                PARTITION BY spotify_id, country
                ORDER BY chart_week
            ) = 0
                THEN NULL

            ELSE
                (
                    weekly_chart_points
                    - LAG(weekly_chart_points) OVER (
                        PARTITION BY spotify_id, country
                        ORDER BY chart_week
                    )
                )
                / NULLIF(
                    LAG(weekly_chart_points) OVER (
                        PARTITION BY spotify_id, country
                        ORDER BY chart_week
                    ),
                    0
                )
        END AS wow_growth_rate

    FROM weekly_data

)

SELECT *
FROM growth_calculation