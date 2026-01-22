# This file is part of indico-patcher.
# Copyright (C) 2023 - 2026 UNCONVENTIONAL

from collections import defaultdict
from collections.abc import Callable
from typing import Any
from typing import cast

from .types import ClassWrapper
from .types import PatchedClass
from .util import get_members
from .util import patch_member

__all__ = ["patch_class"]

# Members that should not be overridden in the original class
SKIPPED_MEMBERS = {
    # Python internals
    "__dict__",
    "__doc__",
    "__module__",
    "__weakref__",
    # SQLAlchemy-related
    "__mapper__",
    "_sa_class_manager"
}


def patch_class(orig_class: type) -> ClassWrapper:
    """Decorator to patch a given class with members from the decorated class.

    :param orig_class: The class to patch.
    :return: A wrapper that takes the patch class.
    """
    if not isinstance(orig_class, type):
        raise TypeError("Cannot patch instance of classes")
    if orig_class.__module__ == "builtins":
        raise TypeError("Cannot patch built-in classes")
    # Hint type checker that the class becomes a PatchedClass
    cls = cast(PatchedClass, orig_class)
    # Store patches and original members of the class
    # XXX: We use `__dict__` instead of `getattr` to avoid retrieving patches
    #      from parent classes, which would cause infinite recursion when
    #      patching multiple classes in the same hierarchy.
    cls.__patches__ = cls.__dict__.get("__patches__", [])
    cls.__unpatched__ = cls.__dict__.get("__unpatched__",defaultdict(lambda: defaultdict(list)))
    # Reset patch storage for subclasses
    cls.__init_subclass__ = classmethod(_create_subclass_patch_reset(cls.__init_subclass__))  # type: ignore[assignment]

    def wrapper(patch_class: type) -> type:
        # Keep a reference to the patch class
        cls.__patches__.append(patch_class)
        # Inject members of the patch class into the original class
        for member_name, member in get_members(patch_class).items():
            if member_name in SKIPPED_MEMBERS:
                continue
            patch_member(cls, member_name, member)
        return patch_class

    return wrapper


def _create_subclass_patch_reset(orig_init_subclass: Callable) -> Callable:
    """Create an __init_subclass__ method that resets patch tracking for subclasses."""

    def __init_subclass__(subcls: PatchedClass, **kwargs: Any) -> None:
        orig_init_subclass(**kwargs)
        # Reset patch tracking for subclass
        subcls.__patches__ = []
        subcls.__unpatched__ = defaultdict(lambda: defaultdict(list))

    return __init_subclass__
