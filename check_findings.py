import pandas as pd

df = pd.read_csv('data/category_elasticity.csv')
confident = df[(df['p_value'] < 0.05) & (df['r_squared'] > 0.10)]

sensible = confident[confident['elasticity'] < 0]
unexpected = confident[confident['elasticity'] >= 0]

with open('findings_summary.txt', 'w') as f:
    f.write(f"Total categories: {len(df)}\n")
    f.write(f"Statistically confident (p<0.05, r2>0.10): {len(confident)}\n\n")

    f.write(f"CONFIDENT AND SENSIBLE (negative elasticity): {len(sensible)}\n")
    f.write(sensible.sort_values('elasticity').to_string())
    f.write("\n\n")

    f.write(f"CONFIDENT BUT UNEXPECTED (positive elasticity): {len(unexpected)}\n")
    f.write(unexpected.sort_values('elasticity').to_string())

print("Saved to findings_summary.txt — open it to see the full results.")