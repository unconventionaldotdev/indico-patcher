# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

# TODO: Use explicit TypeAlias and | when support for Python 3.9 is dropped

from collections.abc import Callable
from enum import EnumMeta
from types import FunctionType
from typing import Any
from typing import TypedDict
from typing import Union

from sqlalchemy.ext.hybrid import hybrid_property

# Attribute type aggregates
propertylike = Union[property, hybrid_property]  # noqa: UP007
methodlike = Union[FunctionType, classmethod, staticmethod]  # noqa: UP007

# Decorator wrapper aliases
ClassWrapper = Callable[[type], type]
EnumWrapper = Callable[[EnumMeta], None]
PatchWrapper = Union[ClassWrapper, EnumWrapper]  # noqa: UP007

# Annotations for extra attributes in patched classes
class PatchedClass:
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
