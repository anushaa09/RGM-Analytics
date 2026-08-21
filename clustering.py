"""
clustering.py
--------------
Step 5 of the RGM Analytics Suite.

Groups categories into elasticity segments using K-Means, so instead of
reasoning about hundreds of categories individually, the business can
reason about a handful of groups: e.g. "highly elastic", "moderate",
"inelastic".

Validation:
    Silhouette score is computed to check the clusters are actually
    well-separated rather than an arbitrary split. The script tries
    k = 2, 3, and 4 clusters and automatically picks whichever value
    gives the best silhouette score, instead of hardcoding k=3.

Input:
    data/category_elasticity.csv (produced by elasticity_model.py)

Output:
    data/category_segments.csv
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import os

DATA_DIR = "data"
CANDIDATE_K_VALUES = [2, 3, 4]
RANDOM_STATE = 42


def choose_best_k(X) -> tuple:
    """
    Fits K-Means for each candidate k, computes silhouette score for each,
    and returns the (best_k, best_score, best_labels) combination.
    """
    best_k = None
    best_score = -1
    best_labels = None

    print("Evaluating cluster counts:")
    for k in CANDIDATE_K_VALUES:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels)
        print(f"  k={k} -> silhouette score = {score:.3f}")

        if score > best_score:
            best_k = k
            best_score = score
            best_labels = labels

    print(f"Chosen k={best_k} (silhouette score = {best_score:.3f})")
    return best_k, best_score, best_labels


def run():
    df = pd.read_csv(os.path.join(DATA_DIR, "category_elasticity.csv"))

    X = df[["elasticity"]]
    best_k, best_score, labels = choose_best_k(X)

    df["cluster"] = labels

    # Rank clusters by centroid value so labels are consistent
    # (most negative elasticity = most price-sensitive)
    centroids = df.groupby("cluster")["elasticity"].mean().sort_values()
    ordered_clusters = list(centroids.index)

    # Build generic labels that scale to however many clusters were chosen
    if best_k == 2:
        names = ["Elastic (price-sensitive)", "Inelastic (staple-like)"]
    elif best_k == 3:
        names = [
            "Highly Elastic (very price-sensitive)",
            "Moderate",
            "Inelastic (staple-like)",
        ]
    else:  # k == 4
        names = [
            "Highly Elastic (very price-sensitive)",
            "Elastic",
            "Moderate",
            "Inelastic (staple-like)",
        ]

    label_map = {cluster_id: names[i] for i, cluster_id in enumerate(ordered_clusters)}
    df["segment_label"] = df["cluster"].map(label_map)
    df["silhouette_score"] = best_score

    out_path = os.path.join(DATA_DIR, "category_segments.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved segmented categories to {out_path}")
    print(df[["category", "elasticity", "segment_label"]].sort_values("elasticity"))


if __name__ == "__main__":
    run()