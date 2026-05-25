"""BaseEvaluator 抽象基类"""

from abc import ABC, abstractmethod

from app.models.score import Score
from app.models.trace import Span, Trace


class BaseEvaluator(ABC):
    """评估器抽象基类"""

    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    async def evaluate(self, trace: Trace, spans: list[Span]) -> list[Score]:
        """评估一个 Trace，返回 Score 列表"""
        ...
