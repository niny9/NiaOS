from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.optimization.optimizer import ParameterOptimizer
    from src.optimization.parameter_manager import ParameterManager, ParameterSet
    from src.optimization.regime_detector import MarketRegimeDetector, RegimeDetector, MarketRegime, RegimeInfo

__all__ = [
    "ParameterManager",
    "ParameterSet",
    "ParameterOptimizer",
    "MarketRegimeDetector",
    "RegimeDetector",
    "MarketRegime",
    "RegimeInfo",
]


def __getattr__(name: str):
    if name in {"ParameterManager", "ParameterSet"}:
        from src.optimization.parameter_manager import ParameterManager, ParameterSet

        return {"ParameterManager": ParameterManager, "ParameterSet": ParameterSet}[name]
    if name == "ParameterOptimizer":
        from src.optimization.optimizer import ParameterOptimizer

        return ParameterOptimizer
    if name in {"MarketRegimeDetector", "RegimeDetector", "MarketRegime", "RegimeInfo"}:
        from src.optimization.regime_detector import MarketRegimeDetector, RegimeDetector, MarketRegime, RegimeInfo

        return {
            "MarketRegimeDetector": MarketRegimeDetector,
            "RegimeDetector": RegimeDetector,
            "MarketRegime": MarketRegime,
            "RegimeInfo": RegimeInfo,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
