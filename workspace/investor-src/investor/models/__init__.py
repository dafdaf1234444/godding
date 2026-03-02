"""
Advanced quantitative models for institutional-level investment analysis.

This module contains sophisticated factor models, regime detection, and statistical
arbitrage frameworks that replace basic technical analysis with institutional-quality
quantitative methods.
"""

from .factor_models import (
    FamaFrenchFactorModel,
    FamaFrenchDataDownloader,
    CustomFactorConstructor,
    FactorLoadings,
    FactorPerformance,
    analyze_factor_model_vs_technical_analysis
)

__all__ = [
    'FamaFrenchFactorModel',
    'FamaFrenchDataDownloader', 
    'CustomFactorConstructor',
    'FactorLoadings',
    'FactorPerformance',
    'analyze_factor_model_vs_technical_analysis'
]