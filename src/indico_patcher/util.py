# This file is part of indico-patcher.
# Copyright (C) 2023 UNCONVENTIONAL

from __future__ import annotations

import sys
from collections.abc import Callable
from functools import partial
from types import FrameType
from types import FunctionType
from types import MappingProxyType
from typing import Any

from sqlalchemy.ext.hybrid import hybrid_property

from .types import PatchedClass
from .types import methodlike
from .types import propertylike


class SuperProxy:
    """A proxy for super that allows calling the original class' methods."""

    def __init__(self, orig_class: PatchedClass) -> None:
        self.orig_class = orig_class

    def __call__(self, patch_class: type | None = None, obj: object | None = None) -> Any:
        """Wrapper for calls to super() in the patch class.

        :param patch_class: The class to call super() on. Defaults to the class of the caller.
        :param obj: The instance to call super() on. Defaults to the instance of the caller.
        """
        # Simulate the behavior of super() when called without arguments
        if patch_class is None:
            patch_class, obj = self._get_defaults()

        class duper:
            """Interceptor for calls to super().getattr() in the patch class."""

            def __getattribute__(self_, name: str) -> Any:
                # TODO: Find out how to identify which property descriptor method the call is coming from.
                # XXX: We default to `fget` because calling `super()` on `fset` and `fdel` is broken in Python.
                #      Bug report: https://bugs.python.org/issue14965
                if prop := self.orig_class.__unpatched__["properties"].get(name):
                    return prop.fget(obj)

                # TODO: Find out how to identify which property descriptor method the call is coming from.
                # XXX: We currently default to `fget`.
                if hprop := self.orig_class.__unpatched__["hybrid_properties"].get(name):
                    return hprop.fget(obj)

                if method := self.orig_class.__unpatched__["methods"].get(name):
                    return partial(method, obj)

                if classmethod := self.orig_class.__unpatched__["classmethods"].get(name):
                    return classmethod

                if staticmethod := self.orig_class.__unpatched__["staticmethods"].get(name):
                    return staticmethod

                # Fallback to the original class' member
                return getattr(obj, name) if obj else getattr(self.orig_class, name)

            def __repr__(self) -> str:
                classname = f"{patch_class.__module__}.{patch_class.__name__}" if patch_class else None
                return f"<duper: {classname}, {obj}>"

        return duper()

    @staticmethod
    def _get_defaults() -> tuple[type | None, object | None]:
        """Get the class and instance of the caller."""
        frame: FrameType | None = sys._getframe(1)
        while frame:
            cls = frame.f_locals.get("__class__")
            self = frame.f_locals.get("self")
            if cls:
                return cls, self
            frame = frame.f_back
        return None, None


def get_members(cls: type) -> MappingProxyType[str, Any]:
    """Get a dictionary of all the members of the base classes up to object."""
    if cls is object:
        raise TypeError("Cannot get members for object")
    dicts = [cls.__dict__]
    for base in cls.__bases__:
        if base is object:
            continue
        dicts.insert(0, get_members(base))
    return MappingProxyType({k: v for d in dicts for k, v in d.items()})


def patch_member(orig_class: PatchedClass, member_name: str, member: Any) -> None:
    """Patch a member in a class.

    :param orig_class: The class to patch
    :param member_name: The name of the member to patch in the class
    :param member: The member object to replace the original member with
    """
    # TODO: Patch relationship
    # TODO: Patch deferred columns
    if isinstance(member, property):
        # TODO: Add `fset` and `fdel` descriptors once SuperProxy supports them
        _patch_propertylike(orig_class, member_name, member, "properties", ("fget",))
    elif isinstance(member, hybrid_property):
        _patch_propertylike(orig_class, member_name, member, "hybrid_properties", ("fget", "expression"))
    elif isinstance(member, FunctionType):
        _patch_methodlike(orig_class, member_name, member, "methods")
    elif isinstance(member, classmethod):
        _patch_methodlike(orig_class, member_name, member, "classmethods")
    elif isinstance(member, staticmethod):
        _patch_methodlike(orig_class, member_name, member, "staticmethods")
    else:
        _patch_attr(orig_class, member_name, member)


def _patch_attr(orig_class: PatchedClass, attr_name: str, attr: Any) -> None:
    """Patch an attribute in a class.

    :param orig_class: The class to patch
    :param attr_name: The name of the attribute to patch in the class
    :param attr: The attribute object to replace the original attribute with
    """
    _store_unpatched(orig_class, attr_name, "attributes")
    setattr(orig_class, attr_name, attr)


def _patch_propertylike(orig_class: PatchedClass, prop_name: str, prop: propertylike,
                        category: str, fnames: tuple[str, ...]) -> None:
    """Patch a property-like member in a class.

    :param orig_class: The class to patch
    :param prop_name: The name of the property-like member to patch in the class
    :param prop: The property-like object to replace the original member with
    :param category: The category of unpached members to store the original member in
    :param fnames: The names of the property descriptor methods (e.g. fget, fset, fdel)
                   to override super() in
    """
    if category not in {"properties", "hybrid_properties"}:
        raise ValueError(f"Unsupported category '{category}'")
    if unsupported_fnames := set(fnames) - {"fget", "expression"}:
        raise ValueError(f"Unsupported descriptor method '{list(unsupported_fnames)[0]}'")
    # Keep a reference to the original property-like member
    _store_unpatched(orig_class, prop_name, category)
    # Replace the original property-like member
    setattr(orig_class, prop_name, prop)
    # Override super() in the property descriptor methods
    for fname in fnames:
        if func := getattr(prop, fname, None):
            func.__globals__["super"] = SuperProxy(orig_class)


def _patch_methodlike(orig_class: PatchedClass, method_name: str, method: methodlike, category: str) -> None:
    """Patch a method-like member in a class.

    :param orig_class: The class to patch
    :param method_name: The name of the method-like member to patch in the class
    :param method: The method-like object to replace the original member with
    :param category: The category of unpached members to store the original member in
    """
    if category not in {"methods", "classmethods", "staticmethods"}:
        raise ValueError(f"Unsupported category '{category}'")
    # Keep a reference to the original method
    _store_unpatched(orig_class, method_name, category)
    # Replace the original method
    setattr(orig_class, method_name, method)
    # Override super() in the method
    # XXX: Type is declared explicitly and type checking is disabled because mypy
    #      infers wrong types for classmethods and staticmethods (https://github.com/python/mypy/issues/3482)
    func: Callable = method if isinstance(method, FunctionType) else method.__func__
    func.__globals__["super"] = SuperProxy(orig_class)


def _store_unpatched(orig_class: PatchedClass, member_name: str, category: str) -> None:
    """Store a reference to the original member of a class.

    :param orig_class: The class to store the reference in
    :param member_name: The name of the member to store the reference for
    """
    if hasattr(orig_class, member_name):
        # TODO: Log warning if member is already patched
        orig_class.__unpatched__[category][member_name] = getattr(orig_class, member_name)
