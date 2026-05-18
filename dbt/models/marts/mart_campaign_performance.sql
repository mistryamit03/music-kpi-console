-- ============================================================
-- Mart model: mart_campaign_performance
--
-- Purpose:
-- Final dashboard-ready table for synthetic campaign performance.
--
-- Grain:
-- One row per campaign_id
--
-- Business use:
-- Helps compare campaign spend, attributed streams, cost per stream,
-- ROAS proxy, and lift vs control markets.
--
-- Important:
-- Campaign data is synthetic and used only for portfolio simulation.
-- ============================================================

WITH campaigns AS (

    SELECT *
    FROM {{ ref('stg_campaigns') }}

),

repertoire AS (

    SELECT *
    FROM {{ ref('int_track_lifecycle_and_market_flags') }}

),

campaign_base AS (

    SELECT
        campaign_id,
        spotify_id,
        track_name,
        artists,
        country,
        snapshot_date,

        DATE_TRUNC('week', snapshot_date) AS campaign_week,

        campaign_start_date,
        campaign_end_date,
        channel,

        spend_eur,
        impressions,
        clicks,
        ctr,
        conversion_rate,
        attributed_streams,
        generation_type

    FROM campaigns

),

campaign_with_market_performance AS (

    SELECT
        c.campaign_id,
        c.spotify_id,
        c.track_name,
        c.artists,
        c.country,
        c.snapshot_date,
        c.campaign_week,

        c.campaign_start_date,
        c.campaign_end_date,
        c.channel,

        c.spend_eur,
        c.impressions,
        c.clicks,
        c.ctr,
        c.conversion_rate,
        c.attributed_streams,
        c.generation_type,

        r.weekly_chart_points AS campaign_market_chart_points,
        r.wow_growth_rate AS campaign_market_wow_growth,
        r.lifecycle_stage AS campaign_market_lifecycle_stage,
        r.market_spike_flag AS campaign_market_spike_flag,
        r.cross_market_count

    FROM campaign_base c

    LEFT JOIN repertoire r
        ON c.spotify_id = r.spotify_id
        AND c.country = r.country
        AND c.campaign_week = r.chart_week

),

control_market_growth AS (

    SELECT
        c.campaign_id,
        AVG(r.wow_growth_rate) AS control_market_avg_wow_growth

    FROM campaign_base c

    LEFT JOIN repertoire r
        ON c.spotify_id = r.spotify_id
        AND c.campaign_week = r.chart_week
        AND c.country <> r.country

    WHERE r.wow_growth_rate IS NOT NULL

    GROUP BY
        c.campaign_id

),

campaign_metrics AS (

    SELECT
        c.campaign_id,
        c.spotify_id,
        c.track_name,
        c.artists,
        c.country,
        c.snapshot_date,
        c.campaign_week,

        c.campaign_start_date,
        c.campaign_end_date,
        c.channel,

        c.spend_eur,
        c.impressions,
        c.clicks,
        c.ctr,
        c.conversion_rate,
        c.attributed_streams,
        c.generation_type,

        c.campaign_market_chart_points,
        c.campaign_market_wow_growth,
        ctrl.control_market_avg_wow_growth,

        c.campaign_market_wow_growth
        - ctrl.control_market_avg_wow_growth AS lift_vs_control,

        c.campaign_market_lifecycle_stage,
        c.campaign_market_spike_flag,
        c.cross_market_count,

        c.spend_eur / NULLIF(c.attributed_streams, 0) AS cost_per_stream,

        -- Public streaming payout proxy used only for portfolio simulation.
        -- This does not represent an actual Sony/Spotify payout value.
        (c.attributed_streams * 0.004) / NULLIF(c.spend_eur, 0) AS roas_proxy

    FROM campaign_with_market_performance c

    LEFT JOIN control_market_growth ctrl
        ON c.campaign_id = ctrl.campaign_id

),

channel_benchmarks AS (

    SELECT
        channel,
        AVG(cost_per_stream) AS channel_avg_cost_per_stream
    FROM campaign_metrics
    WHERE cost_per_stream IS NOT NULL
    GROUP BY channel

),

final AS (

    SELECT
        m.campaign_id,
        m.spotify_id,
        m.track_name,
        m.artists,
        m.country,
        m.snapshot_date,
        m.campaign_week,

        m.campaign_start_date,
        m.campaign_end_date,
        m.channel,

        m.spend_eur,
        m.impressions,
        m.clicks,
        m.ctr,
        m.conversion_rate,
        m.attributed_streams,
        m.generation_type,

        m.campaign_market_chart_points,
        m.campaign_market_wow_growth,
        m.control_market_avg_wow_growth,
        m.lift_vs_control,

        m.campaign_market_lifecycle_stage,
        m.campaign_market_spike_flag,
        m.cross_market_count,

        m.cost_per_stream,
        m.roas_proxy,

        b.channel_avg_cost_per_stream,

        CASE
            WHEN m.cost_per_stream > 2 * b.channel_avg_cost_per_stream
                THEN TRUE
            ELSE FALSE
        END AS campaign_efficiency_alert,

        CASE
            WHEN m.roas_proxy >= 1
                THEN 'Positive ROAS Proxy'

            WHEN m.lift_vs_control > 0
                 AND m.cost_per_stream <= b.channel_avg_cost_per_stream
                THEN 'Efficient Growth'

            WHEN m.cost_per_stream > 2 * b.channel_avg_cost_per_stream
                THEN 'High Cost Alert'

            ELSE 'Monitor'
        END AS campaign_performance_signal

    FROM campaign_metrics m

    LEFT JOIN channel_benchmarks b
        ON m.channel = b.channel

)

SELECT *
FROM final