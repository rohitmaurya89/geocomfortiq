"""
services/kmeans_classifier.py

Phase 3 — KMeans Zone Classification.
Classifies a set of parameter values into Safe / Moderate / Risky
using KMeans clustering (unsupervised ML, no training data needed).

How it works:
  - We build a small synthetic dataset from the current params + known
    Safe/Moderate/Risky anchor points so KMeans always has 3 meaningful clusters.
  - The input params vector is then assigned to its nearest cluster.
  - Cluster labels are mapped to risk categories by sorting cluster centroids
    on a combined "comfort axis" (green+shade high, dust+builtup+congestion low).
"""

import numpy as np
from sklearn.cluster import KMeans
from config.settings_config import KMEANS_CLUSTERS, KMEANS_RANDOM_STATE


# ── Feature order (must match everywhere) ─────────────────────────────────────
FEATURES = ['green_pct', 'dust_pct', 'builtup_pct', 'shade_pct', 'congestion_pct']

# ── Anchor points: representative Safe / Moderate / Risky environments ────────
# These give KMeans stable, city-independent cluster seeds.
ANCHORS = np.array([
    # green  dust  builtup  shade  congestion   → category
    [45,     10,   20,      30,    15],          # Safe
    [30,     15,   25,      20,    20],          # Safe (variant)
    [20,     28,   38,      12,    30],          # Moderate
    [18,     30,   40,      10,    35],          # Moderate (variant)
    [8,      45,   50,       5,    55],          # Risky
    [5,      50,   55,       4,    60],          # Risky (variant)
], dtype=float)


def classify_zone(params: dict) -> dict:
    """
    Runs KMeans on anchor data + current params vector.
    Returns dict with:
        risk_category : 'safe' | 'moderate' | 'risky'
        cluster_id    : int (0-2)
        all_scores    : list of comfort scores per anchor cluster
    """
    # Build feature vector for the input params
    input_vec = np.array([[params.get(f, 0.0) for f in FEATURES]], dtype=float)

    # Combine anchors + input for fitting
    data = np.vstack([ANCHORS, input_vec])

    # Fit KMeans
    km = KMeans(
        n_clusters=KMEANS_CLUSTERS,
        random_state=KMEANS_RANDOM_STATE,
        n_init=10,
    )
    km.fit(data)

    # Label for the last row = our input
    input_cluster = km.labels_[-1]

    # Map cluster id → risk category
    # Sort clusters by "comfort axis": high green+shade, low dust+builtup+congestion
    centroids = km.cluster_centers_
    comfort_axis = (
        centroids[:, 0] +          # green (positive)
        centroids[:, 3] -          # shade (positive)
        centroids[:, 1] -          # dust  (negative)
        centroids[:, 2] -          # builtup (negative)
        centroids[:, 4]            # congestion (negative)
    )
    # Rank: highest comfort_axis = safe (0), middle = moderate (1), lowest = risky (2)
    ranked = np.argsort(comfort_axis)[::-1]   # descending
    risk_map = {}
    labels = ['safe', 'moderate', 'risky']
    for rank, cluster_id in enumerate(ranked):
        risk_map[cluster_id] = labels[rank]

    risk_category = risk_map[input_cluster]

    return {
        'risk_category': risk_category,
        'cluster_id':    int(input_cluster),
    }
