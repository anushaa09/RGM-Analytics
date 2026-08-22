# RGM Analytics Suite — Price Elasticity & Promotion ROI Dashboard

## Problem
Retail and CPG companies constantly need to decide: which products should
be discounted, by how much, and does a promotion actually create new
demand or just cannibalize sales from a similar product? This project
builds a small-scale version of the analytics a Revenue Growth Management
(RGM) team uses to answer that question — price elasticity, promotion
ROI, and a lightweight marketing-mix decomposition — with an emphasis on
validating results rather than just reporting whatever a model outputs.

## Data
[dunnhumby "The Complete Journey"](https://www.dunnhumby.com/source-files/)
— real household-level transaction data from a retail chain, including
pricing and promotion (display/mailer) activity across product categories.

## Methodology
1. **Exploratory Data Analysis** — before any modeling, the raw data is
   inspected for nulls, duplicates, negative/zero values, price and
   quantity distributions, category imbalance, and promo frequency, to
   justify every cleaning decision made downstream.
2. **Price elasticity** — OLS regression of log(units) on log(price) per
   category, giving an elasticity coefficient per category. Each
   regression is validated with an 80/20 train/test split and held-out
   RMSE, rather than being evaluated only on data it already saw.
3. **Segmentation** — K-Means clustering of categories by elasticity.
   The number of clusters (k=2, 3, or 4) is chosen automatically based on
   whichever produces the best silhouette score, rather than being
   hardcoded.
4. **Promotion uplift** — comparison of average units sold in promoted vs
   non-promoted weeks per category.
5. **Simplified MMM** — OLS decomposition of weekly sales into baseline,
   price, promotion, and seasonality contributions.
6. **What-if simulator** — interactive tool predicting volume/revenue
   impact of a proposed price change, using the estimated elasticity.
7. **Result validation** — every elasticity and promo-uplift result is
   checked against statistical reliability thresholds (p-value, R²,
   baseline size) and against basic economic intuition (does the sign
   and magnitude make sense?) before being reported as a finding. See
   "Key Findings" below.

## Key Findings

### Price Elasticity
Of 295 categories analyzed, 55 (19%) produced statistically significant
elasticity estimates (p < 0.05, R² > 0.10). Of these, 37 categories (67%
of the confident set) showed negative elasticity consistent with
standard demand theory — discretionary and substitutable goods such as
BACON (-5.28), FROZEN NOVELTIES/WATER ICE (-4.50), and BREAD (-3.44) were
the most price-sensitive, while staples showed elasticity closer to zero.

The remaining 18 confident categories showed unexpected *positive*
elasticity (demand rising alongside price). Most of these were seasonal
categories (HALLOWEEN, CHRISTMAS SEASONAL, FIREWORKS, SPRING/SUMMER
SEASONAL) — a known confound where price and demand both rise ahead of a
holiday, which a simple bivariate regression cannot separate. A smaller
number of non-seasonal categories (FUEL, POTATOES, SOUP, SNACKS) showed
the same pattern and are flagged as candidates for further investigation,
likely reflecting promotional pricing coinciding with naturally higher
demand (price endogeneity).

The remaining 240 categories (81%) did not meet the statistical
reliability threshold and are excluded from confident findings.

**Takeaway:** the analysis identifies a reliable core set of ~37
price-sensitive categories where discounting is likely to drive real
volume, while flagging seasonal and low-confidence categories as
requiring a more sophisticated model (e.g. controlling for seasonality
and promotion simultaneously, or panel fixed-effects) before their
elasticity estimates should inform pricing decisions.

### Promotion ROI
Of 249 categories with sufficient promo/non-promo weeks to compare, 219
(88%) produced reliable uplift estimates (baseline ≥ 5 units, uplift ≤
300%). The median promoted category saw an 81% increase in units sold
during promotion weeks, with high-visibility staples — ICE CREAM/MILK/
SHERBETS, BAKING MIXES, FLUID MILK, EGGS, BATH TISSUES, PAPER TOWELS —
showing the strongest response (250–300% uplift), consistent with their
common use as loss-leader or traffic-driving promotions. Lower-uplift
categories (MAGAZINES, COFFEE FILTERS, HERBS, SALAD BAR) showed uplift
under 20%, suggesting limited ROI from further promotional investment in
these categories.

30 categories (12%) were excluded as unreliable. Notably, seasonal/
holiday categories (EASTER, VALENTINE, CHRISTMAS, HALLOWEEN) showed the
most extreme apparent uplift (400–650%) — the same seasonality confound
identified in the elasticity analysis: these products have minimal
baseline sales outside their holiday window, so any promotion during
that window produces an inflated, unreliable percentage rather than a
genuine promotional effect. The remaining flagged categories were
low-volume/niche items where a small baseline (under 5 units) makes
percentage-based comparisons statistically unstable.

**Takeaway:** the same seasonality confound independently shows up in
both the elasticity and promotion analyses, which is itself a useful,
generalizable finding — any pricing/promo model applied to this kind of
retail data needs to explicitly account for seasonal categories, or risk
systematically misleading conclusions for a meaningful subset of the
catalog.

## Limitations (read before citing results)
- **Promotion uplift** is a naive pre/post-style comparison, not a causal
  estimate. It does not control for trend, seasonality, or
  cross-category cannibalization. A more rigorous approach would use
  difference-in-differences or synthetic control methods.
- **The MMM component is a simplified, non-production approximation.**
  Real MMM tools (e.g. Google Meridian, Meta Robyn) use Bayesian
  hierarchical models with adstock (carryover) and saturation curves.
  This project's decomposition is a linear OLS approximation intended to
  demonstrate the concept, not to be decision-grade.
- Elasticity estimates use a simple bivariate regression (price only) and
  do not control for promotion activity, competitor pricing, or macro
  factors — this is the primary driver of the seasonality confound
  described above. A stronger version would include promo_flag and
  seasonality terms directly in the elasticity regression itself.
- Only 19% of categories produced statistically reliable elasticity
  estimates; the majority did not have enough price variation in the
  data window to support a confident conclusion.

## Project Structure
```
rgm-analytics-suite/
├── data/                          # place downloaded dunnhumby CSVs here
├── notebooks/
│   ├── 01_eda.ipynb                # raw data exploration (run first)
│   └── 02_elasticity_sanity_check.ipynb  # validates elasticity results
├── data_prep.py                    # loads & cleans raw data into weekly table
├── elasticity_model.py             # estimates price elasticity per category (with train/test validation)
├── clustering.py                   # segments categories via K-Means (auto-selects k via silhouette score)
├── promo_uplift.py                 # promotion lift analysis
├── mmm_model.py                    # simplified marketing mix decomposition
├── simulator.py                    # what-if price simulator (used by dashboard)
├── dashboard.py                    # Streamlit app (reliability-aware)
├── check_findings.py               # sanity-checks elasticity results (confident vs flagged)
├── check_promo_findings.py         # sanity-checks promo uplift results (reliable vs flagged)
├── requirements.txt
└── README.md
```

## How to Run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download dunnhumby "Complete Journey" from Kaggle and place
#    transaction_data.csv, product.csv, causal_data.csv into ./data/

# 3. (Optional but recommended) Explore the raw data first
jupyter notebook notebooks/01_eda.ipynb

# 4. Run the pipeline in order
python data_prep.py
python elasticity_model.py
python clustering.py
python promo_uplift.py
python mmm_model.py

# 5. Validate the results
python check_findings.py
python check_promo_findings.py
# (or open notebooks/02_elasticity_sanity_check.ipynb for a more visual version)

# 6. Launch the dashboard
streamlit run dashboard.py
```

## Future Work
- Add promo_flag and seasonality controls directly into the elasticity
  regression to reduce the seasonal confound identified above.
- Replace naive promo uplift with a difference-in-differences design.
- Add adstock/carryover effects to the MMM component.
- Extend the simulator to jointly optimize price + promotion timing.
- Investigate the non-seasonal categories with unexpected positive
  elasticity (FUEL, POTATOES, SOUP, SNACKS) individually.