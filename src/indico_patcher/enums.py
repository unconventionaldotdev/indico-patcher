# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

from collections.abc import Iterable
from enum import Enum
from enum import EnumMeta
from typing import cast

from aenum import extend_enum

from indico.util.enum import RichIntEnum

from .types import EnumWrapper

__all__ = ["patch_enum"]

# Attributes used to store data for rich properties in RichEnum
RICH_ENUM_BASE_ATTRS = ("__titles__", "__css_classess__")


# TODO: Modify RichIntEnum upstream so that it's possible to programmatically
#       determine which attributes are used for rich properties. This will
#       avoid having to explicitly specify additional ones in the decorator.
def patch_enum(
    enum: EnumMeta, *,
    padding: int = 0,
    extra_attrs: tuple[str, ...] = (),
    rich_attrs: tuple[str, ...] = ()
) -> EnumWrapper:
    """Patch an Enum with members and attributes from a decorated one.

    :param padding: Value padding for patched enum members. Useful to avoid
                    collisions with future members in the original enum.
    :param extra_args: Additional attributes that should be carried over to the
                       original enum.
    :param rich_attrs: Additional attributes used for per-member rich information
                       in subclasses of RichIntEnum.
    """
    if not isinstance(enum, EnumMeta):
        raise TypeError("The 'enum' argument must be a subclass of Enum.")
    if padding < 0:
        raise ValueError("Padding value cannot be negative.")

    # Determine which rich attributes need to be patched
    _rich_attrs: set[str] = set()
    if rich_attrs and not issubclass(enum, RichIntEnum):
        raise ValueError("The argument 'rich_attrs' can only be used for subclasses of RichIntEnum.")
    if issubclass(enum, RichIntEnum):
        _rich_attrs.update(RICH_ENUM_BASE_ATTRS + rich_attrs)

    # Make sure that extra attributes don't override rich attributes in the original enum
    if collision := _rich_attrs.intersection(set(extra_attrs)):
        raise ValueError(f"The original Emum already defines a '{list(collision)[0]}' attribute for rich information.")

    def wrapper(patch: EnumMeta) -> None:
        if not isinstance(patch, EnumMeta):
            raise TypeError("The patch must be a subclass of Enum.")
        # Extend original enum with members from patch
        for x in cast(Iterable[Enum], patch):
            extend_enum(enum, x.name, x.value + padding)
        # Extend original enum with per-member rich values
        for attr in _rich_attrs:
            _patch_rich_attr(patch, attr)
        # Set extra attributes in the original enum
        for attr in extra_attrs:
            value = getattr(patch, attr)
            setattr(enum, attr, value)

    def _patch_rich_attr(patch: EnumMeta, attr: str) -> None:
        """Patch the rich attribute af a RichIntEnum."""
        if not all(hasattr(x, attr) for x in (enum, patch)):
            return
        orig_rich_values = getattr(enum, attr)
        patch_rich_values = getattr(patch, attr)
        # Determine padding for list of rich values
        padding_values = []
        if padding:
            idx = padding - len(orig_rich_values)
            padding_values = [None] * idx
        # Set the new list of rich values in the original enum
        setattr(enum, attr, orig_rich_values + padding_values + patch_rich_values)

    return wrapper
