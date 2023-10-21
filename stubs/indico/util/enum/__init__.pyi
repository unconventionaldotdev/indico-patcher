# This file is part of indico-patcher.
# Copyright (C) 2023 UNCONVENTIONAL

from enum import Enum
from typing import Any

class IndicoEnum(Enum):
    @classmethod
    def get(cls, name: str, default: Any = None) -> Any: ...
    @classmethod
    def serialize(cls) -> dict[str, Any]: ...


class RichEnum(IndicoEnum):
    __titles__: list[str]
    __css_classes__: list[str]
    @property
    def title(self) -> str: ...
    @property
    def css_class(self) -> str: ...


class RichIntEnum(int, RichEnum): ...
