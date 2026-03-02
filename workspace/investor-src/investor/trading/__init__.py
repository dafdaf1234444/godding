"""
Trading module for the investor analysis system.
Includes pairs trading, portfolio optimization, and execution algorithms.
"""

from .pairs_trading import (
    PairsTradingFramework,
    PairsTradingStrategy,
    PairSelector,
    CointegrationAnalyzer,
    PairSelectionMethod,
    TradingSignal,
    PairTradingSignal
)

__all__ = [
    'PairsTradingFramework',
    'PairsTradingStrategy', 
    'PairSelector',
    'CointegrationAnalyzer',
    'PairSelectionMethod',
    'TradingSignal',
    'PairTradingSignal'
]