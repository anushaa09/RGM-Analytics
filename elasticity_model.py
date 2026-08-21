"""
elasticity_model.py
--------------------
Step 4 of the RGM Analytics Suite.

For each product category, estimates price elasticity of demand by
regressing log(units_sold) on log(avg_price).

Elasticity interpretation:
    < -1        -> elastic (price-sensitive; demand drops sharply as price rises)
    -1 to 0      -> inelastic (staple-like; demand barely reacts to price)

Validation:
    Each category's regression is checked with an 80/20 train/test split
    and test-set RMSE, so the reported fit isn't just measured on data
    the model already saw. The final elasticity coefficient is then
    refit on the full data (standard practice: split to validate, use
    all data for the final estimate).

Input:
    data/weekly_category_data.csv (produced by data_prep.py)

Output:
    data/category_elasticity.csv
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error

DATA_DIR = "data"
MIN_WEEKS_REQUIRED = 15  # need enough data points for a stable regression
TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_weekly_data() -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_DIR, "weekly_category_data.csv"))


def estimate_elasticity_for_category(df_category: pd.DataFrame) -> dict:
    """
    Runs OLS: log(units) = const + elasticity * log(price)

    Returns the elasticity coefficient (fit on all data), R-squared,
    p-value, number of observations, and a held-out test RMSE used to
    check the model generalizes rather than just fitting historical noise.
    """
    df_category = df_category[df_category["units_sold"] > 0]
    df_category = df_category[df_category["avg_price"] > 0]

    if len(df_category) < MIN_WEEKS_REQUIRED:
        return None

    log_price = np.log(df_category["avg_price"])
    log_units = np.log(df_category["units_sold"])

    X = sm.add_constant(log_price)
    y = log_units

    # --- Train/test split to validate generalization ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    train_model = sm.OLS(y_train, X_train).fit()
    y_pred_test = train_model.predict(X_test)
    test_rmse = root_mean_squared_error(y_test, y_pred_test)

    # --- Refit on full data for the final reported elasticity estimate ---
    full_model = sm.OLS(y, X).fit()

    return {
        "elasticity": full_model.params.iloc[1],
        "r_squared": full_model.rsquared,
        "p_value": full_model.pvalues.iloc[1],
        "n_weeks": len(df_category),
        "test_rmse": test_rmse,
    }


def run():
    weekly = load_weekly_data()
    results = []

    for category, group in weekly.groupby("category"):
        result = estimate_elasticity_for_category(group)
        if result is not None:
            result["category"] = category
            results.append(result)

    elasticity_df = pd.DataFrame(results)
    elasticity_df = elasticity_df[
        ["category", "elasticity", "r_squared", "p_value", "n_weeks", "test_rmse"]
    ].sort_values("elasticity")

    def label_segment(e):
        if e < -1:
            return "elastic (price-sensitive)"
        elif e < -0.2:
            return "moderate"
        else:
            return "inelastic (staple-like)"

    elasticity_df["interpretation"] = elasticity_df["elasticity"].apply(label_segment)

    out_path = os.path.join(DATA_DIR, "category_elasticity.csv")
    elasticity_df.to_csv(out_path, index=False)
    print(f"Saved elasticity results for {len(elasticity_df)} categories to {out_path}")
    print(f"Average held-out test RMSE across categories: {elasticity_df['test_rmse'].mean():.4f}")
    print(elasticity_df.head(10))


if __name__ == "__main__":
    run()