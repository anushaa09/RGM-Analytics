# RGM Analytics Suite — Price Elasticity & Promotion ROI Dashboard

## Problem
Retail and CPG companies constantly need to decide: which products should
be discounted, by how much, and does a promotion actually create new
demand or just cannibalize sales from a similar product? This project
builds a small-scale version of the analytics a Revenue Growth Management
(RGM) team uses to answer that question.

## Data
[dunnhumby "The Complete Journey"](https://www.dunnhumby.com/source-files/)
— real household-level transaction data from a retail chain, including
pricing and promotion (display/mailer) activity across product categories.

## Methodology
1. **Price elasticity** — OLS regression of log(units) on log(price) per
   category, giving an elasticity coefficient per category.
2. **Segmentation** — K-Means clustering of categories by elasticity into
   "elastic", "moderate", and "inelastic" groups.
3. **Promotion uplift** — comparison of average units sold in promoted vs
   non-promoted weeks per category.
4. **Simplified MMM** — OLS decomposition of weekly sales into baseline,
   price, promotion, and seasonality contributions.
5. **What-if simulator** — interactive tool predicting volume/revenue
   impact of a proposed price change, using the estimated elasticity.

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
- Elasticity estimates assume price is the primary driver of demand
  variation and do not account for competitor pricing or macro factors.

## Project Structure
```
rgm-analytics-suite/
├── data/                   # place downloaded dunnhumby CSVs here
├── data_prep.py            # loads & cleans raw data into weekly table
├── elasticity_model.py     # estimates price elasticity per category
├── clustering.py           # segments categories via K-Means
├── promo_uplift.py         # promotion lift analysis
├── mmm_model.py             # simplified marketing mix decomposition
├── simulator.py              # what-if price simulator (used by dashboard)
├── dashboard.py               # Streamlit app
├── requirements.txt
└── README.md
```

## How to Run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download dunnhumby "Complete Journey" from Kaggle and place
#    transaction_data.csv, product.csv, causal_data.csv into ./data/

# 3. Run the pipeline in order
python data_prep.py
python elasticity_model.py
python clustering.py
python promo_uplift.py
python mmm_model.py

# 4. Launch the dashboard
streamlit run dashboard.py
```

## Example Finding
*(fill in after running — e.g. "Category X showed elasticity of -1.8,
indicating high price sensitivity, while promotions on Category Y
generated only 4% uplift, suggesting limited ROI on further discounting.")*

## Future Work
- Replace naive promo uplift with a difference-in-differences design.
- Add adstock/carryover effects to the MMM component.
- Extend the simulator to jointly optimize price + promotion timing.
