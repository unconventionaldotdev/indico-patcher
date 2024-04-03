# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

from __future__ import annotations

from enum import EnumMeta
from typing import Any

from .classes import patch_class
from .enums import patch_enum
from .types import PatchWrapper


def patch(target: type | EnumMeta, *args: Any, **kwargs: Any) -> PatchWrapper:
    """Patch a given class or enum."""
    if isinstance(target, EnumMeta):
        return patch_enum(target, *args, **kwargs)
    else:
        return patch_class(target, *args, **kwargs)
