"""Evaluator 注册表"""

from app.evaluators.base import BaseEvaluator


class EvaluatorRegistry:
    _evaluators: dict[str, type[BaseEvaluator]] = {}

    @classmethod
    def register(cls, name: str, evaluator_class: type[BaseEvaluator]) -> None:
        cls._evaluators[name] = evaluator_class

    @classmethod
    def get(cls, name: str) -> type[BaseEvaluator] | None:
        return cls._evaluators.get(name)

    @classmethod
    def get_all(cls) -> dict[str, type[BaseEvaluator]]:
        return cls._evaluators.copy()

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseEvaluator | None:
        cls_obj = cls.get(name)
        return cls_obj(**kwargs) if cls_obj else None
