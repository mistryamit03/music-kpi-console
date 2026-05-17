"""
02_generate_campaigns.py

Purpose:
Generate a clearly labelled synthetic campaign dataset for the Music KPI Console project.

Important rule:
Every campaign must reference a real SPOTIFY_ID + COUNTRY + SNAPSHOT_DATE combination
from the already-filtered Spotify chart data.

This prevents orphan campaign rows and keeps downstream joins clean.
"""

# ============================================================
# 1. Imports
# ============================================================

from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd


# ============================================================
# 2. Configuration
# ============================================================

FILTERED_CHART_PATH = Path("data/spotify_charts_filtered.csv")
OUTPUT_CAMPAIGN_PATH = Path("data/campaigns.csv")

NUMBER_OF_CAMPAIGNS = 50
RANDOM_SEED = 42

CHANNELS = ["Spotify Ads", "TikTok", "Meta", "Editorial Push"]

# Simple benchmark assumptions used only to create believable synthetic data.
# These are not real Sony or Spotify campaign numbers.
CHANNEL_CPM = {
    "Spotify Ads": 8.0,
    "TikTok": 6.0,
    "Meta": 5.0,
    "Editorial Push": 2.0,
}


# ============================================================
# 3. Helper functions
# ============================================================


def load_filtered_chart_data(path):
    """
    Loads the already-filtered chart data created by 01_ingest_spotify_charts.py.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Filtered chart file not found: {path}\n"
            "Run 01_ingest_spotify_charts.py first to create this file."
        )

    charts = pd.read_csv(path, parse_dates=["SNAPSHOT_DATE", "ALBUM_RELEASE_DATE"])

    required_columns = [
        "SPOTIFY_ID",
        "NAME",
        "ARTISTS",
        "COUNTRY",
        "SNAPSHOT_DATE",
        "DAILY_MOVEMENT",
    ]

    missing_columns = [col for col in required_columns if col not in charts.columns]
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns))

    charts = charts.dropna(subset=["SPOTIFY_ID", "COUNTRY", "SNAPSHOT_DATE"])
    charts["COUNTRY"] = charts["COUNTRY"].astype("string").str.strip().str.upper()

    return charts



def make_one_campaign(campaign_id, anchor_row, rng, generation_type):
    """
    Creates one synthetic campaign row.

    anchor_row is a real row from the filtered Spotify chart data.
    Therefore SPOTIFY_ID + COUNTRY + SNAPSHOT_DATE always exists in the chart data.
    """

    channel = rng.choice(CHANNELS)
    spend_eur = round(float(rng.uniform(500, 50_000)), 2)

    # Campaign starts around the anchor chart date.
    # Movement-anchored campaigns start 2-3 days before the positive movement date.
    # Random campaigns start 0-10 days before the sampled chart date.
    anchor_date = pd.to_datetime(anchor_row["SNAPSHOT_DATE"]).date()

    if generation_type == "movement_anchored":
        days_before_anchor = int(rng.choice([2, 3]))
    else:
        days_before_anchor = int(rng.integers(0, 11))

    campaign_start_date = anchor_date - timedelta(days=days_before_anchor)
    campaign_duration_days = int(rng.integers(7, 31))
    campaign_end_date = campaign_start_date + timedelta(days=campaign_duration_days)

    # Synthetic campaign mechanics.
    # CTR = clicks / impressions.
    # Conversion rate = attributed streams / clicks.
    # A small multiplier makes streams more realistic because one interested listener can stream more than once.
    ctr = float(rng.uniform(0.005, 0.03))
    conversion_rate = float(rng.uniform(0.05, 0.25))
    stream_multiplier = float(rng.uniform(1.0, 3.0))

    cpm = CHANNEL_CPM[channel]
    impressions = int((spend_eur / cpm) * 1000 * rng.uniform(0.85, 1.15))
    clicks = int(impressions * ctr)
    attributed_streams = max(1, int(clicks * conversion_rate * stream_multiplier))

    return {
        "CAMPAIGN_ID": f"CMP_{campaign_id:03d}",
        "SPOTIFY_ID": anchor_row["SPOTIFY_ID"],
        "TRACK_NAME": anchor_row["NAME"],
        "ARTISTS": anchor_row["ARTISTS"],
        "COUNTRY": anchor_row["COUNTRY"],
        "SNAPSHOT_DATE": anchor_date,
        "CAMPAIGN_START_DATE": campaign_start_date,
        "CAMPAIGN_END_DATE": campaign_end_date,
        "CHANNEL": channel,
        "SPEND_EUR": spend_eur,
        "IMPRESSIONS": impressions,
        "CLICKS": clicks,
        "CTR": round(ctr, 4),
        "CONVERSION_RATE": round(conversion_rate, 4),
        "ATTRIBUTED_STREAMS": attributed_streams,
        "GENERATION_TYPE": generation_type,
    }


# ============================================================
# 4. Main campaign generation flow
# ============================================================


def main():
    """
    Main script flow:
    1. Load filtered chart data.
    2. Find rows with positive daily movement.
    3. Generate 60% movement-anchored campaigns.
    4. Generate 40% random campaigns.
    5. Save campaigns.csv.
    """

    rng = np.random.default_rng(RANDOM_SEED)

    charts = load_filtered_chart_data(FILTERED_CHART_PATH)

    # Keep only unique track-country-date combinations to avoid repeated anchors.
    valid_anchor_rows = charts.drop_duplicates(
        subset=["SPOTIFY_ID", "COUNTRY", "SNAPSHOT_DATE"]
    ).reset_index(drop=True)

    positive_movement_rows = valid_anchor_rows[
        pd.to_numeric(valid_anchor_rows["DAILY_MOVEMENT"], errors="coerce") > 0
    ].reset_index(drop=True)

    if valid_anchor_rows.empty:
        raise ValueError("No valid chart rows found after filtering.")

    campaigns = []
    movement_anchored_target = int(NUMBER_OF_CAMPAIGNS * 0.60)

    for campaign_number in range(1, NUMBER_OF_CAMPAIGNS + 1):
        if campaign_number <= movement_anchored_target and not positive_movement_rows.empty:
            source_rows = positive_movement_rows
            generation_type = "movement_anchored"
        else:
            source_rows = valid_anchor_rows
            generation_type = "random_timing"

        random_index = int(rng.integers(0, len(source_rows)))
        anchor_row = source_rows.iloc[random_index]

        campaign = make_one_campaign(
            campaign_id=campaign_number,
            anchor_row=anchor_row,
            rng=rng,
            generation_type=generation_type,
        )
        campaigns.append(campaign)

    campaigns_df = pd.DataFrame(campaigns)

    OUTPUT_CAMPAIGN_PATH.parent.mkdir(parents=True, exist_ok=True)
    campaigns_df.to_csv(OUTPUT_CAMPAIGN_PATH, index=False)

    print("Synthetic campaign file created.")
    print(f"Rows created: {len(campaigns_df)}")
    print(f"Output path: {OUTPUT_CAMPAIGN_PATH}")
    print("Generation types:")
    print(campaigns_df["GENERATION_TYPE"].value_counts().to_string())


# ============================================================
# 5. Run script
# ============================================================

if __name__ == "__main__":
    main()
