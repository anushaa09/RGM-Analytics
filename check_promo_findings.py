"""
check_promo_findings.py
------------------------
Sanity-checks the promotion uplift results the same way
check_findings.py did for elasticity: separates plausible,
trustworthy findings from likely artifacts.

Flags two kinds of unreliable results:
1. Tiny baseline (baseline_avg_units too small) -- a small % change
   in a tiny number produces an inflated, misleading uplift_pct.
2. Extreme uplift (> EXTREME_UPLIFT_THRESHOLD%) -- almost always a
   symptom of #1 rather than a real promotional effect.

Run with:
    python check_promo_findings.py

Output:
    - Prints summary to terminal
    - Saves full results to promo_findings_summary.txt
"""

import pandas as pd

MIN_BASELINE_UNITS = 5          # below this, % change is unreliable
EXTREME_UPLIFT_THRESHOLD = 300  # % uplift above this is flagged as likely artifact


def run():
    df = pd.read_csv("data/promo_uplift.csv")

    df["flag_tiny_baseline"] = df["baseline_avg_units"] < MIN_BASELINE_UNITS
    df["flag_extreme_uplift"] = df["uplift_pct"].abs() > EXTREME_UPLIFT_THRESHOLD
    df["is_reliable"] = ~(df["flag_tiny_baseline"] | df["flag_extreme_uplift"])

    reliable = df[df["is_reliable"]].sort_values("uplift_pct", ascending=False)
    flagged = df[~df["is_reliable"]].sort_values("uplift_pct", ascending=False)

    with open("promo_findings_summary.txt", "w") as f:
        f.write(f"Total categories with promo uplift computed: {len(df)}\n")
        f.write(f"Reliable (baseline >= {MIN_BASELINE_UNITS} units, uplift <= {EXTREME_UPLIFT_THRESHOLD}%): {len(reliable)}\n")
        f.write(f"Flagged (tiny baseline or extreme uplift): {len(flagged)}\n\n")

        f.write("=== SUMMARY STATS (reliable subset only) ===\n")
        f.write(reliable["uplift_pct"].describe().to_string())
        f.write("\n\n")

        f.write("=== TOP 15 RELIABLE UPLIFT CATEGORIES ===\n")
        f.write(reliable.head(15).to_string())
        f.write("\n\n")

        f.write("=== BOTTOM 15 RELIABLE UPLIFT CATEGORIES (promotions that hurt or did nothing) ===\n")
        f.write(reliable.tail(15).to_string())
        f.write("\n\n")

        f.write(f"=== FLAGGED CATEGORIES ({len(flagged)}) -- likely artifacts, exclude from findings ===\n")
        f.write(flagged.to_string())

    print(f"Total categories: {len(df)}")
    print(f"Reliable: {len(reliable)} | Flagged: {len(flagged)}")
    print("Full results saved to promo_findings_summary.txt")


if __name__ == "__main__":
    run()