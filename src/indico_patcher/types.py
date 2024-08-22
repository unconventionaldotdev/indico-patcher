# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

from collections.abc import Callable
from enum import EnumMeta
from types import FunctionType
from typing import Any
from typing import TypeAlias
from typing import TypedDict

from sqlalchemy.ext.hybrid import hybrid_property

# Attribute type aggregates
propertylike: TypeAlias = property | hybrid_property  # noqa: UP040
methodlike: TypeAlias = FunctionType | classmethod | staticmethod  # noqa: UP040

# Decorator wrapper aliases
ClassWrapper: TypeAlias = Callable[[type], type]  # noqa: UP040
EnumWrapper: TypeAlias = Callable[[EnumMeta], None]  # noqa: UP040
PatchWrapper: TypeAlias = ClassWrapper | EnumWrapper  # noqa: UP040

# Annotations for extra attributes in patched classes
class PatchedClass(type):
    __patches__: list[type]
    __unpatched__: dict[str, dict[str, Any]]


# Dictionary of property descriptor functions
class PropertyDescriptors(TypedDict, total=False):
    fget: FunctionType | None
    fset: FunctionType | None
    fdel: FunctionType | None


# Dictionary of hybrid_property descriptor functions
class HybridPropertyDescriptors(PropertyDescriptors, total=False):
    expr: FunctionType | None
