-- ============================================================
-- Mart model: mart_kpi_catalog
--
-- Purpose:
-- Dashboard-ready KPI catalog explaining which KPIs are computed,
-- synthetic, or documented only due to data limitations.
--
-- Business use:
-- Shows domain awareness and honest handling of data availability.
-- ============================================================

SELECT
    'Chart Points' AS kpi_name,
    'Tier 1 - Real Spotify chart data' AS kpi_tier,
    '201 - daily_rank, aggregated by track, market, and week' AS formula_or_definition,
    'Real Kaggle Spotify chart data' AS data_source_requirement,
    TRUE AS computed_in_project

UNION ALL

SELECT
    'Week-over-Week Growth',
    'Tier 1 - Real Spotify chart data',
    '(this_week_chart_points - previous_week_chart_points) / previous_week_chart_points',
    'Real Kaggle Spotify chart data',
    TRUE

UNION ALL

SELECT
    'Lifecycle Stage',
    'Tier 1 - Real Spotify chart data',
    'Classifies tracks as Debut, Growing, Peak, Declining, Revived, or Stable based on weekly chart movement',
    'Real Kaggle Spotify chart data',
    TRUE

UNION ALL

SELECT
    'Catalog Revival Flag',
    'Tier 1 - Real Spotify chart data',
    'Flags tracks that return after a long gap in chart activity',
    'Real Kaggle Spotify chart data',
    TRUE

UNION ALL

SELECT
    'Market Spike Flag',
    'Tier 1 - Real Spotify chart data',
    'Flags tracks where market-level growth is significantly above the selected-market average',
    'Real Kaggle Spotify chart data',
    TRUE

UNION ALL

SELECT
    'Cross-Market Penetration',
    'Tier 1 - Real Spotify chart data',
    'Counts distinct countries where a track appears in the same chart week',
    'Real Kaggle Spotify chart data',
    TRUE

UNION ALL

SELECT
    'Cost per Stream',
    'Tier 2 - Synthetic campaign data',
    'spend_eur / attributed_streams',
    'Synthetic campaign data linked to real track-market-date combinations',
    TRUE

UNION ALL

SELECT
    'ROAS Proxy',
    'Tier 2 - Synthetic campaign data',
    '(attributed_streams * 0.004) / spend_eur',
    'Synthetic campaign data plus public stream value proxy',
    TRUE

UNION ALL

SELECT
    'Lift vs Control',
    'Tier 2 - Synthetic campaign data',
    'campaign_market_wow_growth - control_market_avg_wow_growth',
    'Synthetic campaign data joined with real chart trend data',
    TRUE

UNION ALL

SELECT
    'Skip Rate',
    'Tier 3 - Documented only',
    'skips / total_streams',
    'Requires Spotify for Artists or platform-level consumption data',
    FALSE

UNION ALL

SELECT
    'Save Rate',
    'Tier 3 - Documented only',
    'saves / total_listeners or saves / total_streams',
    'Requires Spotify for Artists data',
    FALSE

UNION ALL

SELECT
    'Monthly Listeners',
    'Tier 3 - Documented only',
    'Unique listeners over a rolling monthly window',
    'Requires Spotify for Artists data',
    FALSE

UNION ALL

SELECT
    'D7 Retention',
    'Tier 3 - Documented only',
    'listeners returning seven days after first listening event',
    'Requires user-level listening data',
    FALSE

UNION ALL

SELECT
    'Playlist Reach',
    'Tier 3 - Documented only',
    'Estimated listeners reachable through playlist placement',
    'Requires Spotify for Artists, Chartmetric, or internal label tools',
    FALSE

UNION ALL

SELECT
    'CAC per Follower',
    'Tier 3 - Documented only',
    'campaign_spend / new_followers',
    'Requires internal campaign spend and follower growth data',
    FALSE