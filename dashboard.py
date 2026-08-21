"""
dashboard.py
------------
Step 9 of the RGM Analytics Suite.

Streamlit app that ties together elasticity, clustering, promo uplift,
MMM decomposition, and the what-if simulator into one interactive tool.

Reliability handling:
    Not every category's elasticity estimate is trustworthy. A category
    is treated as "confident" only if p_value < 0.05 AND r_squared > 0.10.
    Categories that fail this check (or that were flagged as having
    positive/economically unexpected elasticity) are visually marked as
    unreliable throughout the dashboard, and the What-If Simulator shows
    an explicit warning rather than silently using a noisy number.

Run with:
    streamlit run dashboard.py

Assumes you have already run, in order:
    1. data_prep.py
    2. elasticity_model.py
    3. clustering.py
    4. promo_uplift.py
    5. mmm_model.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os

from simulator import simulate_price_change

DATA_DIR = "data"

# Same thresholds used in the elasticity sanity check
P_VALUE_THRESHOLD = 0.05
R2_THRESHOLD = 0.10

st.set_page_config(page_title="RGM Analytics Suite", layout="wide")
st.title("RGM Analytics Suite")
st.caption(
    "Price elasticity, promotion ROI, and a simplified marketing-mix "
    "decomposition, built on the dunnhumby Complete Journey dataset."
)


@st.cache_data
def load_all_data():
    segments = pd.read_csv(os.path.join(DATA_DIR, "category_segments.csv"))
    uplift = pd.read_csv(os.path.join(DATA_DIR, "promo_uplift.csv"))
    mmm = pd.read_csv(os.path.join(DATA_DIR, "mmm_decomposition.csv"))
    weekly = pd.read_csv(os.path.join(DATA_DIR, "weekly_category_data.csv"))

    # --- Reliability flag, computed once here so every tab can use it ---
    segments["is_confident"] = (
        (segments["p_value"] < P_VALUE_THRESHOLD)
        & (segments["r_squared"] > R2_THRESHOLD)
    )
    segments["is_sensible"] = segments["elasticity"] < 0
    segments["reliability"] = "Not statistically confident"
    segments.loc[
        segments["is_confident"] & segments["is_sensible"], "reliability"
    ] = "Confident & sensible"
    segments.loc[
        segments["is_confident"] & ~segments["is_sensible"], "reliability"
    ] = "Confident but unexpected (flag)"

    return segments, uplift, mmm, weekly


segments, uplift, mmm, weekly = load_all_data()

n_total = len(segments)
n_confident_sensible = (segments["reliability"] == "Confident & sensible").sum()
n_confident_unexpected = (segments["reliability"] == "Confident but unexpected (flag)").sum()
n_unreliable = (segments["reliability"] == "Not statistically confident").sum()

st.info(
    f"**Reliability summary:** of {n_total} categories, "
    f"**{n_confident_sensible}** have statistically confident, economically "
    f"sensible elasticity estimates. **{n_confident_unexpected}** are "
    f"statistically confident but show unexpected (positive) elasticity — "
    f"often seasonal categories where price and demand rise together, "
    f"confounding the estimate. **{n_unreliable}** did not pass the "
    f"significance/fit thresholds (p<0.05, R²>0.10) and should not be "
    f"treated as reliable findings."
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Elasticity & Segments", "Promotion ROI", "MMM Decomposition", "What-If Simulator"]
)

# ---------------- TAB 1: Elasticity ----------------
with tab1:
    st.subheader("Price Elasticity by Category")
    st.caption(
        "Elasticity < -1 = price-sensitive (elastic). "
        "Between -1 and 0 = staple-like (inelastic). "
        "Color shows reliability, not just the elasticity segment."
    )

    show_only_reliable = st.checkbox(
        "Show only statistically confident & sensible categories", value=True
    )

    plot_df = segments.copy()
    if show_only_reliable:
        plot_df = plot_df[plot_df["reliability"] == "Confident & sensible"]

    fig = px.bar(
        plot_df.sort_values("elasticity"),
        x="elasticity",
        y="category",
        color="reliability",
        orientation="h",
        height=700,
        color_discrete_map={
            "Confident & sensible": "#2E7D32",
            "Confident but unexpected (flag)": "#F9A825",
            "Not statistically confident": "#BDBDBD",
        },
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        segments[[
            "category", "elasticity", "r_squared", "p_value",
            "segment_label", "reliability",
        ]]
    )

# ---------------- TAB 2: Promo ROI ----------------
with tab2:
    st.subheader("Promotion Uplift by Category")
    st.caption(
        "Naive comparison of average units sold during promoted vs "
        "non-promoted weeks. Not causally adjusted for seasonality or "
        "cannibalization -- see README for methodology notes. Extreme "
        "uplift values (e.g. >500%) are often artifacts of a very small "
        "baseline and should be treated with caution."
    )

    top_n = st.slider("Show top N categories by uplift", 5, 30, 15)
    fig2 = px.bar(
        uplift.head(top_n),
        x="uplift_pct",
        y="category",
        orientation="h",
        height=600,
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(uplift)

# ---------------- TAB 3: MMM ----------------
with tab3:
    st.subheader("Simplified Marketing Mix Decomposition")
    st.caption(
        "Lightweight OLS-based decomposition -- not a production MMM "
        "(no adstock, saturation, or Bayesian priors)."
    )

    category_choice = st.selectbox("Choose a category", mmm["category"].unique())
    cat_mmm = mmm[mmm["category"] == category_choice].sort_values("WEEK_NO")

    fig3 = px.area(
        cat_mmm,
        x="WEEK_NO",
        y=[
            "baseline_contribution",
            "price_contribution",
            "promo_contribution",
            "seasonality_contribution",
        ],
        title=f"Sales Decomposition — {category_choice}",
    )
    st.plotly_chart(fig3, use_container_width=True)

# ---------------- TAB 4: Simulator ----------------
with tab4:
    st.subheader("What-If Price Simulator")

    sim_category = st.selectbox(
        "Category", segments["category"].unique(), key="sim_cat"
    )
    cat_row = segments.loc[segments["category"] == sim_category].iloc[0]
    elasticity_val = cat_row["elasticity"]
    reliability = cat_row["reliability"]

    if reliability == "Confident & sensible":
        st.success(
            f"This category's elasticity estimate is statistically confident "
            f"(p={cat_row['p_value']:.4f}, R²={cat_row['r_squared']:.2f}) and "
            f"economically sensible. Simulation results below can be treated "
            f"as a reasonable estimate."
        )
    elif reliability == "Confident but unexpected (flag)":
        st.warning(
            f"⚠️ This category shows a statistically significant but "
            f"**positive** elasticity ({elasticity_val:.2f}) — economically "
            f"backwards from standard demand theory. This is likely driven "
            f"by seasonality or price/demand confounding rather than a real "
            f"price effect. Treat any simulation below with caution."
        )
    else:
        st.error(
            f"⚠️ This category's elasticity estimate did NOT pass the "
            f"statistical reliability check (p={cat_row['p_value']:.4f}, "
            f"R²={cat_row['r_squared']:.2f}). The number below may be close "
            f"to noise. Simulation results are shown for exploration only "
            f"and should not be treated as a real prediction."
        )

    cat_weekly = weekly[weekly["category"] == sim_category]
    current_units = cat_weekly["units_sold"].mean()
    current_price = cat_weekly["avg_price"].mean()

    st.write(f"Current avg weekly units: **{current_units:.0f}**")
    st.write(f"Current avg price: **${current_price:.2f}**")
    st.write(f"Estimated elasticity: **{elasticity_val:.2f}**")

    pct_change = st.slider("Proposed price change (%)", -50, 50, -10)

    result = simulate_price_change(
        elasticity=elasticity_val,
        pct_price_change=pct_change,
        current_units=current_units,
        current_price=current_price,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Predicted Units", f"{result['predicted_units']:.0f}",
                f"{result['pct_volume_change']}%")
    col2.metric("Predicted Price", f"${result['predicted_price']:.2f}")
    col3.metric("Predicted Revenue", f"${result['predicted_revenue']:.0f}",
                f"{result['pct_revenue_change']}%")