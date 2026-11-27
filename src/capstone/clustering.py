"""
src/capstone/clustering.py
Consumer Segmentation and Clustering Module.

Author: Omonigho Khalin Egbo (@omonigho-egbo-15)
Role: Consumer Segmentation & Clustering Analyst
Repository: jpierre-7/itds-2373-capstone
Branch: issue-24-clustering / issue-9-clustering
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Default continuous metrics selected for clustering
DEFAULT_CLUSTER_FEATURES: List[str] = [
    "score",
    "popularity",
    "n_favorites",
    "episodes",
    "adjusted_review_sentiment",
]

# Right-skewed features requiring log1p transformation prior to scaling
LOG_TRANSFORM_FEATURES: List[str] = [
    "n_favorites",
    "episodes",
]

# Strategic business archetypes for streaming investment
ARCHETYPE_LABELS: Dict[str, str] = {
    "MAINSTREAM_HIT": "Mainstream Hit",
    "HIDDEN_GEM": "Hidden Gem",
    "HIGH_RATED_NICHE": "High-Rated Niche",
    "FRANCHISE_PROPERTY": "Franchise Property",
    "UNDERPERFORMER": "Underperforming Catalog",
}


@dataclass
class ClusteringPipelineResult:
    """Container holding outputs of the segmentation pipeline."""

    data: pd.DataFrame
    model: KMeans
    scaler: StandardScaler
    pca_transformer: Optional[PCA]
    silhouette: float
    inertia: float
    feature_names: List[str]
    cluster_centroids: pd.DataFrame


def preprocess_clustering_features(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    log_cols: Optional[List[str]] = None,
) -> Tuple[np.ndarray, StandardScaler, List[str]]:
    """Clean, transform, and standardize quantitative segmentation features.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing anime metadata.
    feature_cols : Optional[List[str]]
        List of continuous feature names to cluster on.
    log_cols : Optional[List[str]]
        Subset of features to apply log1p transform before scaling.

    Returns
    -------
    Tuple[np.ndarray, StandardScaler, List[str]]
        - Scaled numpy feature matrix ready for distance-based clustering.
        - Fitted StandardScaler instance.
        - List of active feature names.
    """
    features = list(feature_cols or DEFAULT_CLUSTER_FEATURES)
    log_transforms = list(log_cols or LOG_TRANSFORM_FEATURES)

    missing_cols = [c for c in features if c not in df.columns]
    if missing_cols:
        raise KeyError(
            f"Required feature columns missing from DataFrame: {missing_cols}"
        )

    # Work on a copy of features
    X_df = df[features].copy()

    # Handle missing values using column-wise median
    for col in features:
        if X_df[col].isnull().any():
            median_val = X_df[col].median()
            X_df[col] = X_df[col].fillna(median_val)
            logger.info("Imputed missing values in '%s' with median %0.4f", col, median_val)

    # Apply log1p transform to skewed non-negative metrics
    for col in log_transforms:
        if col in X_df.columns:
            # Shift negatives to zero if any exist
            min_val = X_df[col].min()
            if min_val < 0:
                X_df[col] = X_df[col] - min_val
            X_df[col] = np.log1p(X_df[col].astype(float))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df.values)

    return X_scaled, scaler, features


def evaluate_cluster_range(
    X_scaled: np.ndarray,
    k_range: range = range(2, 11),
    random_state: int = 42,
) -> pd.DataFrame:
    """Evaluate Inertia and Silhouette scores across candidate k values.

    Parameters
    ----------
    X_scaled : np.ndarray
        Standardized feature matrix.
    k_range : range
        Sequence of cluster counts to test (default 2 to 10).
    random_state : int
        Seed for deterministic centroid initialization.

    Returns
    -------
    pd.DataFrame
        Metrics table with columns ['k', 'inertia', 'silhouette_score'].
    """
    records = []
    for k in k_range:
        kmeans = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=10,
            max_iter=300,
            random_state=random_state,
        )
        labels = kmeans.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        records.append(
            {
                "k": k,
                "inertia": kmeans.inertia_,
                "silhouette_score": sil,
            }
        )

    return pd.DataFrame(records)


def assign_strategic_archetypes(
    centroids_df: pd.DataFrame,
) -> Dict[int, str]:
    """Map unsupervised cluster indices to strategic streaming business archetypes.

    Considers relative centroid ranks across score, popularity, favorites,
    episodes, and sentiment.

    Parameters
    ----------
    centroids_df : pd.DataFrame
        Unscaled or scaled cluster centroids indexed by cluster_id.

    Returns
    -------
    Dict[int, str]
        Mapping from cluster integer ID to human-readable archetype label.
    """
    cluster_ids = list(centroids_df.index)
    assigned: Dict[int, str] = {}
    available_ids = set(cluster_ids)

    # 1. Underperformer: lowest mean score / lowest sentiment
    underperformer_id = centroids_df.loc[list(available_ids), "score"].idxmin()
    assigned[underperformer_id] = ARCHETYPE_LABELS["UNDERPERFORMER"]
    available_ids.remove(underperformer_id)

    # 2. Franchise Property: highest episode count / long-running format
    if "episodes" in centroids_df.columns and len(available_ids) > 1:
        franchise_id = centroids_df.loc[list(available_ids), "episodes"].idxmax()
        assigned[franchise_id] = ARCHETYPE_LABELS["FRANCHISE_PROPERTY"]
        available_ids.remove(franchise_id)

    # 3. Mainstream Hit: highest popularity / favorites among remaining
    pop_metric = "n_favorites" if "n_favorites" in centroids_df.columns else "popularity"
    if pop_metric in centroids_df.columns and len(available_ids) > 1:
        mainstream_id = centroids_df.loc[list(available_ids), pop_metric].idxmax()
        assigned[mainstream_id] = ARCHETYPE_LABELS["MAINSTREAM_HIT"]
        available_ids.remove(mainstream_id)

    # 4. Hidden Gem: high score/sentiment but lower popularity
    if len(available_ids) > 1:
        # Score-to-popularity or high sentiment
        sent_metric = (
            "adjusted_review_sentiment"
            if "adjusted_review_sentiment" in centroids_df.columns
            else "score"
        )
        hidden_gem_id = centroids_df.loc[list(available_ids), sent_metric].idxmax()
        assigned[hidden_gem_id] = ARCHETYPE_LABELS["HIDDEN_GEM"]
        available_ids.remove(hidden_gem_id)

    # 5. Remaining clusters: High-Rated Niche or default
    for remaining_id in available_ids:
        assigned[remaining_id] = ARCHETYPE_LABELS["HIGH_RATED_NICHE"]

    return assigned


def run_clustering_pipeline(
    df: pd.DataFrame,
    n_clusters: int = 5,
    feature_cols: Optional[List[str]] = None,
    log_cols: Optional[List[str]] = None,
    random_state: int = 42,
    compute_pca: bool = True,
) -> ClusteringPipelineResult:
    """Execute end-to-end segmentation: preprocess, fit K-Means, label archetypes, and project 2D PCA.

    Parameters
    ----------
    df : pd.DataFrame
        Clean input DataFrame.
    n_clusters : int
        Number of clusters to generate (default: 5 archetypes).
    feature_cols : Optional[List[str]]
        Specific columns to include.
    log_cols : Optional[List[str]]
        Features requiring log transform.
    random_state : int
        Seed for reproducibility.
    compute_pca : bool
        Whether to generate 'pca_x' and 'pca_y' coordinates for plotting.

    Returns
    -------
    ClusteringPipelineResult
        Container with tagged DataFrame and model metadata.
    """
    result_df = df.copy()

    # 1. Preprocess & Scale
    X_scaled, scaler, features = preprocess_clustering_features(
        result_df, feature_cols=feature_cols, log_cols=log_cols
    )

    # 2. Fit K-Means
    kmeans = KMeans(
        n_clusters=n_clusters,
        init="k-means++",
        n_init=10,
        max_iter=300,
        random_state=random_state,
    )
    labels = kmeans.fit_predict(X_scaled)
    result_df["cluster_id"] = labels

    # 3. Calculate Diagnostics
    inertia = float(kmeans.inertia_)
    sil = float(silhouette_score(X_scaled, labels))

    # 4. Profile Centroids & Archetypes
    centroids_unscaled = pd.DataFrame(
        scaler.inverse_transform(kmeans.cluster_centers_),
        columns=features,
        index=range(n_clusters),
    )
    archetype_map = assign_strategic_archetypes(centroids_unscaled)
    result_df["cluster_label"] = result_df["cluster_id"].map(archetype_map)

    # 5. 2D PCA Coordinates for visualizations
    pca_transformer = None
    if compute_pca:
        pca_transformer = PCA(n_components=2, random_state=random_state)
        pca_coords = pca_transformer.fit_transform(X_scaled)
        result_df["pca_x"] = pca_coords[:, 0]
        result_df["pca_y"] = pca_coords[:, 1]

    return ClusteringPipelineResult(
        data=result_df,
        model=kmeans,
        scaler=scaler,
        pca_transformer=pca_transformer,
        silhouette=sil,
        inertia=inertia,
        feature_names=features,
        cluster_centroids=centroids_unscaled,
    )