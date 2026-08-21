import pandas as pd
import os

DATA_DIR = "data"
MIN_WEEKS_PER_GROUP = 5  # need enough promo and non-promo weeks to compare


def run():
    weekly = pd.read_csv(os.path.join(DATA_DIR, "weekly_category_data.csv"))

    results = []
    for category, group in weekly.groupby("category"):
        promo_weeks = group[group["promo_flag"] == 1]
        baseline_weeks = group[group["promo_flag"] == 0]

        if len(promo_weeks) < MIN_WEEKS_PER_GROUP or len(baseline_weeks) < MIN_WEEKS_PER_GROUP:
            continue

        baseline_avg = baseline_weeks["units_sold"].mean()
        promo_avg = promo_weeks["units_sold"].mean()
        uplift_pct = (promo_avg - baseline_avg) / baseline_avg * 100

        results.append({
            "category": category,
            "baseline_avg_units": baseline_avg,
            "promo_avg_units": promo_avg,
            "uplift_pct": uplift_pct,
            "n_promo_weeks": len(promo_weeks),
            "n_baseline_weeks": len(baseline_weeks),
        })

    uplift_df = pd.DataFrame(results).sort_values("uplift_pct", ascending=False)

    out_path = os.path.join(DATA_DIR, "promo_uplift.csv")
    uplift_df.to_csv(out_path, index=False)
    print(f"Saved promo uplift results for {len(uplift_df)} categories to {out_path}")
    print(uplift_df.head(10))


if __name__ == "__main__":
    run()
