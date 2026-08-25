"""
Pattern Detection Service — Crime-Watch
=======================================
Identifies related incidents, crime patterns, and sprees using
spatiotemporal analysis and NLP similarity metrics.

Academic Context:
- Serial crime detection using MOLO (Modus Operandi Linking Analysis)
- Crime spree identification via DBSCAN time-space clustering
- Geographic profiling for journey-to-crime analysis
"""
from .similarity_engine import SimilarityEngine
from .pattern_recognizer import PatternRecognizer

__all__ = ['SimilarityEngine', 'PatternRecognizer']
