# This file is part of indico-patcher.
# Copyright (C) 2023 - 2026 UNCONVENTIONAL

from typing import Any

class classproperty(property):
    def __init__(
        self,
        fget: Any = ...,
        fset: Any = ...,
        fdel: Any = ...,
        doc: str | None = ...,
    ) -> None: ...

class strict_classproperty(classproperty): ...
