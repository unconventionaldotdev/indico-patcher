# This file is part of indico-patcher.
# Copyright (C) 2023 UNCONVENTIONAL

from enum import EnumMeta

from .classes import patch_class
from .enums import patch_enum


def patch(target, *args, **kwargs):
    """Patch a given class or enum."""
    if isinstance(target, EnumMeta):
        return patch_enum(target, *args, **kwargs)
    else:
        return patch_class(target, *args, **kwargs)
