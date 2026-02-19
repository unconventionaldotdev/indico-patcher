# This file is part of indico-patcher.
# Copyright (C) 2023 - 2026 UNCONVENTIONAL

# mypy: disable-error-code=misc
# XXX: mypy warns on zero-member enums. These base enums are intentionally
#      empty as they are simply used as stubs.
#      See https://typing.readthedocs.io/en/latest/spec/enums.html#defining-members

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
