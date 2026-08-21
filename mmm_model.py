import pandas as pd
import numpy as np
import statsmodels.api as sm
import os

DATA_DIR = "data"
MIN_WEEKS_REQUIRED = 20


def build_features(df_category: pd.DataFrame) -> pd.DataFrame:
    df = df_category.copy()
    df["log_units"] = np.log(df["units_sold"])
    df["log_price"] = np.log(df["avg_price"])
    # coarse seasonality: which quarter of the year (52-week cycle assumed)
    df["quarter"] = ((df["WEEK_NO"] % 52) // 13).astype(int)
    df = pd.get_dummies(df, columns=["quarter"], prefix="q", drop_first=True)
    return df


def run():
    weekly = pd.read_csv(os.path.join(DATA_DIR, "weekly_category_data.csv"))
    all_rows = []

    for category, group in weekly.groupby("category"):
        if len(group) < MIN_WEEKS_REQUIRED:
            continue

        df = build_features(group)
        seasonality_cols = [c for c in df.columns if c.startswith("q_")]
        feature_cols = ["log_price", "promo_flag"] + seasonality_cols

        X = sm.add_constant(df[feature_cols].astype(float))
        y = df["log_units"]

        model = sm.OLS(y, X).fit()

        # contribution of each term for each week = coefficient * feature value
        df["baseline_contribution"] = model.params["const"]
        df["price_contribution"] = model.params["log_price"] * df["log_price"]
        df["promo_contribution"] = model.params["promo_flag"] * df["promo_flag"]
        df["seasonality_contribution"] = sum(
            model.params[c] * df[c] for c in seasonality_cols
        )
        df["category"] = category

        all_rows.append(
            df[[
                "category", "WEEK_NO", "log_units",
                "baseline_contribution", "price_contribution",
                "promo_contribution", "seasonality_contribution",
            ]]
        )

    result = pd.concat(all_rows, ignore_index=True)
    out_path = os.path.join(DATA_DIR, "mmm_decomposition.csv")
    result.to_csv(out_path, index=False)
    print(f"Saved MMM decomposition ({len(result)} rows) to {out_path}")


if __name__ == "__main__":
    run()
