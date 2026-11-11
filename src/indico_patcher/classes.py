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
    # Wrap once: a second wrap would chain into the first and reset this class' own storage
    if not getattr(cls.__dict__.get("__init_subclass__"), "__patch_reset__", False):
        cls.__init_subclass__ = classmethod(_create_subclass_patch_reset(cls))  # type: ignore[assignment]

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


def _create_subclass_patch_reset(cls: type) -> Callable:
    """Create an __init_subclass__ method that resets patch tracking for subclasses."""
    # Take the class' own hook, if any, from `__dict__`: reading it from the class
    # would give a method bound to `cls` instead of the new subclass.
    own = cls.__dict__.get("__init_subclass__")

    def __init_subclass__(subcls: PatchedClass, **kwargs: Any) -> None:
        if own is not None:
            own.__func__(subcls, **kwargs)
        else:
            super(cls, subcls).__init_subclass__(**kwargs)  # type: ignore[arg-type]
        # Reset patch tracking for subclass
        subcls.__patches__ = []
        subcls.__unpatched__ = defaultdict(lambda: defaultdict(list))

    __init_subclass__.__patch_reset__ = True  # type: ignore[attr-defined]
    return __init_subclass__
