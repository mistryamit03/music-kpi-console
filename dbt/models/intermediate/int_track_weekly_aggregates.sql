-- ============================================================
-- Intermediate model: int_track_weekly_aggregates
--
-- Purpose:
-- Aggregate daily Spotify chart rows into weekly track-market level data.
--
-- Grain:
-- One row per spotify_id, country, chart_week
--
-- Why this model exists:
-- Daily chart data is too detailed for trend analysis.
-- For repertoire and market analysis, weekly movement is easier to compare.
-- ============================================================

WITH daily_chart_data AS (

    SELECT
        spotify_id,
        track_name,
        artists,
        country,
        snapshot_date,

        -- Convert daily rank into chart points.
        -- Rank 1 gets 200 points, rank 50 gets 151 points.
        -- This is a proxy because the public dataset does not contain real stream counts.
        201 - daily_rank AS chart_points,

        daily_rank,
        daily_movement,
        weekly_movement,
        popularity,

        album_name,
        album_release_date,

        danceability,
        energy,
        valence,
        acousticness,
        speechiness,
        instrumentalness,
        liveness,
        tempo

    FROM {{ ref('stg_spotify_charts') }}

),

weekly_aggregates AS (

    SELECT
        spotify_id,

        -- Track metadata should describe the track, but should not define the row grain.
        -- The real grain is spotify_id + country + chart_week.
        MAX(track_name) AS track_name,
        MAX(artists) AS artists,

        country,
        DATE_TRUNC('week', snapshot_date) AS chart_week,

        SUM(chart_points) AS weekly_chart_points,
        AVG(chart_points) AS avg_daily_chart_points,
        AVG(daily_rank) AS avg_daily_rank,
        MIN(daily_rank) AS best_daily_rank,
        COUNT(*) AS chart_days,

        AVG(popularity) AS avg_popularity,

        MIN(snapshot_date) AS first_chart_date_in_week,
        MAX(snapshot_date) AS last_chart_date_in_week,

        MAX(album_name) AS album_name,
        MIN(album_release_date) AS album_release_date,

        AVG(danceability) AS avg_danceability,
        AVG(energy) AS avg_energy,
        AVG(valence) AS avg_valence,
        AVG(acousticness) AS avg_acousticness,
        AVG(speechiness) AS avg_speechiness,
        AVG(instrumentalness) AS avg_instrumentalness,
        AVG(liveness) AS avg_liveness,
        AVG(tempo) AS avg_tempo

    FROM daily_chart_data

    GROUP BY
        spotify_id,
        country,
        DATE_TRUNC('week', snapshot_date)

)

SELECT *
FROM weekly_aggregates