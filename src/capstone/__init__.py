"""
capstone
========
Analytical pipeline for the ITDS 2373 Capstone: Anime Streaming Catalog Optimization.
"""

from capstone.clean import build_anime_table, clean_animes, clean_reviews, parse_aired
from capstone.clustering import (
    ARCHETYPE_LABELS,
    DEFAULT_CLUSTER_FEATURES,
    ClusteringPipelineResult,
    assign_strategic_archetypes,
    evaluate_cluster_range,
    preprocess_clustering_features,
    run_clustering_pipeline,
)
from capstone.data import fetch_raw_data
from capstone.dataset import load_anime, load_reviews, needs_rebuild
from capstone.features import add_features, franchise_root

__all__ = [
    # Data ingestion
    "fetch_raw_data",
    "load_anime",
    "load_reviews",
    "needs_rebuild",
    # Data cleaning
    "build_anime_table",
    "clean_animes",
    "clean_reviews",
    "parse_aired",
    # Feature engineering
    "add_features",
    "franchise_root",
    # Clustering & Segmentation
    "ARCHETYPE_LABELS",
    "DEFAULT_CLUSTER_FEATURES",
    "ClusteringPipelineResult",
    "preprocess_clustering_features",
    "evaluate_cluster_range",
    "assign_strategic_archetypes",
    "run_clustering_pipeline",
]