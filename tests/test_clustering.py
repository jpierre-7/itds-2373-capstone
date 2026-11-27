"""
tests/test_clustering.py
Unit and regression tests for consumer segmentation & clustering pipeline.
"""

import numpy as np
import pandas as pd
import pytest
from capstone.clustering import (
    ARCHETYPE_LABELS,
    DEFAULT_CLUSTER_FEATURES,
    assign_strategic_archetypes,
    evaluate_cluster_range,
    preprocess_clustering_features,
    run_clustering_pipeline,
)


@pytest.fixture
def synthetic_anime_df() -> pd.DataFrame:
    """Create a controlled synthetic anime dataset representing diverse archetypes."""
    np.random.seed(42)
    n_samples = 60

    return pd.DataFrame(
        {
            "anime_id": range(1, n_samples + 1),
            "title": [f"Anime {i}" for i in range(1, n_samples + 1)],
            "score": np.concatenate(
                [
                    np.random.uniform(8.5, 9.5, 12),  # Mainstream
                    np.random.uniform(8.0, 9.0, 12),  # Hidden Gem
                    np.random.uniform(7.5, 8.5, 12),  # Franchise
                    np.random.uniform(7.8, 8.8, 12),  # Niche
                    np.random.uniform(4.0, 6.0, 12),  # Underperformer
                ]
            ),
            "popularity": np.concatenate(
                [
                    np.random.uniform(1, 50, 12),
                    np.random.uniform(500, 1500, 12),
                    np.random.uniform(100, 300, 12),
                    np.random.uniform(800, 2000, 12),
                    np.random.uniform(2500, 5000, 12),
                ]
            ),
            "n_favorites": np.concatenate(
                [
                    np.random.uniform(50000, 120000, 12),
                    np.random.uniform(2000, 8000, 12),
                    np.random.uniform(15000, 40000, 12),
                    np.random.uniform(1000, 5000, 12),
                    np.random.uniform(10, 200, 12),
                ]
            ),
            "episodes": np.concatenate(
                [
                    np.random.choice([12, 24], 12),
                    np.random.choice([12, 13], 12),
                    np.random.uniform(100, 500, 12),  # Long-running franchise
                    np.random.choice([12, 24], 12),
                    np.random.choice([12], 12),
                ]
            ),
            "adjusted_review_sentiment": np.concatenate(
                [
                    np.random.uniform(0.7, 0.95, 12),
                    np.random.uniform(0.85, 0.98, 12),  # High sentiment
                    np.random.uniform(0.5, 0.75, 12),
                    np.random.uniform(0.6, 0.8, 12),
                    np.random.uniform(0.1, 0.4, 12),  # Low sentiment
                ]
            ),
        }
    )


def test_preprocess_clustering_features(synthetic_anime_df):
    """Test standard scaling, missing value imputation, and log transforms."""
    df_with_nans = synthetic_anime_df.copy()
    df_with_nans.loc[0, "score"] = np.nan

    X_scaled, scaler, features = preprocess_clustering_features(df_with_nans)

    assert X_scaled.shape == (len(synthetic_anime_df), len(DEFAULT_CLUSTER_FEATURES))
    assert not np.isnan(X_scaled).any()
    assert features == DEFAULT_CLUSTER_FEATURES
    assert np.allclose(X_scaled.mean(axis=0), 0, atol=1e-5)


def test_evaluate_cluster_range(synthetic_anime_df):
    """Verify evaluation metric calculations across cluster sizes."""
    X_scaled, _, _ = preprocess_clustering_features(synthetic_anime_df)
    eval_df = evaluate_cluster_range(X_scaled, k_range=range(2, 5))

    assert len(eval_df) == 3
    assert list(eval_df.columns) == ["k", "inertia", "silhouette_score"]
    assert (eval_df["silhouette_score"] >= -1.0).all()
    assert (eval_df["silhouette_score"] <= 1.0).all()


def test_assign_strategic_archetypes():
    """Verify assignment logic correctly labels all 5 target business categories."""
    mock_centroids = pd.DataFrame(
        {
            "score": [5.0, 8.8, 9.2, 8.5, 7.9],
            "popularity": [4000, 200, 20, 1500, 900],
            "n_favorites": [50, 30000, 100000, 3000, 2000],
            "episodes": [12, 300, 24, 12, 12],
            "adjusted_review_sentiment": [0.2, 0.65, 0.88, 0.95, 0.72],
        },
        index=[0, 1, 2, 3, 4],
    )

    mapping = assign_strategic_archetypes(mock_centroids)

    assert len(mapping) == 5
    assigned_names = set(mapping.values())
    assert ARCHETYPE_LABELS["UNDERPERFORMER"] in assigned_names
    assert ARCHETYPE_LABELS["FRANCHISE_PROPERTY"] in assigned_names
    assert ARCHETYPE_LABELS["MAINSTREAM_HIT"] in assigned_names
    assert ARCHETYPE_LABELS["HIDDEN_GEM"] in assigned_names
    assert ARCHETYPE_LABELS["HIGH_RATED_NICHE"] in assigned_names


def test_run_clustering_pipeline_integration(synthetic_anime_df):
    """Test complete pipeline execution, label consistency, and 2D PCA projection."""
    result = run_clustering_pipeline(synthetic_anime_df, n_clusters=5, compute_pca=True)

    assert "cluster_id" in result.data.columns
    assert "cluster_label" in result.data.columns
    assert "pca_x" in result.data.columns
    assert "pca_y" in result.data.columns
    assert len(result.data["cluster_id"].unique()) == 5
    assert not result.data["cluster_label"].isnull().any()
    assert result.cluster_centroids.shape == (5, len(DEFAULT_CLUSTER_FEATURES))