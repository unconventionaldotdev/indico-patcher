# This file is part of indico-patcher.
# Copyright (C) 2023 - 2026 UNCONVENTIONAL

from __future__ import annotations

import sys
from functools import partial
from types import CellType
from types import CodeType
from types import FrameType
from types import FunctionType
from types import MappingProxyType
from typing import Any
from typing import cast

from sqlalchemy.ext.hybrid import hybrid_property

from indico.util.decorators import classproperty

from .types import HybridPropertyDescriptors
from .types import PatchedClass
from .types import PropertyDescriptors
from .types import methodlike
from .types import propertylike

# TODO: Add `fset` and `fdel` descriptors once SuperProxy supports them
SUPER_ENABLED_DESCRIPTORS = {"fget"}
SUPPORTED_DESCRIPTORS = {"fget", "fset", "fdel", "expr"}


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
                # Get the code object of the caller to identify which member is being accessed in super()
                current_code = self._get_caller_code()

                # TODO: Find out how to identify which property descriptor method the call is coming from.
                # XXX: We default to `fget` because calling `super()` on `fset` and `fdel` is broken in Python.
                #      Bug report: https://bugs.python.org/issue14965
                if prop := self._get_previous(self.orig_class, "properties", name, current_code):
                    return prop.fget(obj)

                if cprop := self._get_previous(self.orig_class, "classproperties", name, current_code):
                    # Preserve the subclass through which the class property was accessed.
                    target_class = obj if isinstance(obj, type) else self.orig_class
                    return cprop.__get__(None, target_class)

                # TODO: Find out how to identify which property descriptor method the call is coming from.
                # XXX: We currently default to `fget`.
                if hprop := self._get_previous(self.orig_class, "hybrid_properties", name, current_code):
                    return hprop.fget(obj)

                if method := self._get_previous(self.orig_class, "methods", name, current_code):
                    return partial(method, obj)

                if cmethod := self._get_previous(self.orig_class, "classmethods", name, current_code):
                    return partial(cmethod.__func__, self.orig_class)

                if smethod := self._get_previous(self.orig_class, "staticmethods", name, current_code):
                    return smethod

                # Avoid infinite recursion when the member is missing in the original class
                # (e.g. new member added in patch class)
                if name in self.orig_class.__unpatched__["missing"]:
                    raise AttributeError(f"duper object has no attribute '{name}'")

                # Fallback to the original class' member
                return getattr(obj, name) if obj else getattr(self.orig_class, name)

            def __repr__(self) -> str:
                classname = f"{patch_class.__module__}.{patch_class.__name__}" if patch_class else None
                return f"<duper: {classname}, {obj}>"

        return duper()

    @staticmethod
    def _get_caller_code() -> Any:
        """Get the code object of the caller."""
        frame: FrameType | None = sys._getframe(2)
        return frame.f_code if frame else None

    @staticmethod
    def _get_defaults() -> tuple[type | None, object | None]:
        """Get the class and instance of the caller."""
        frame: FrameType | None = sys._getframe(1)
        while frame:
            cls = frame.f_locals.get("__class__")
            obj = frame.f_locals.get("self", frame.f_locals.get("cls"))
            if cls:
                return cls, obj
            frame = frame.f_back
        return None, None

    @staticmethod
    def _get_previous(orig_class: PatchedClass, category: str, name: str, current_code: Any) -> Any:
        """Get the previous version of a member in a class."""
        stack = orig_class.__unpatched__[category].get(name, [])
        # Check if nothing was stored for this member/category
        if not stack:
            return None
        # Use the most recent stored version if the caller identity is unknown
        if current_code is None:
            return stack[-1]
        # Walk newest to oldest looking for the caller's code object
        for idx in range(len(stack) - 1, -1, -1):
            candidate = stack[idx]
            # The caller can be a function wrapped by a decorator
            if current_code in _get_codes(_unwrap_callable(candidate)):
                # If the caller is already the first entry, there's no prior version
                if idx == 0:
                    return None
                # Return the immediately previous version
                return stack[idx - 1]
        # Fallback to newest stored version if caller not found
        return stack[-1]


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
    if isinstance(member, classproperty):
        _patch_propertylike(orig_class, member_name, member, "classproperties", ("fget", "fset", "fdel"))
    elif isinstance(member, property):
        _patch_propertylike(orig_class, member_name, member, "properties", ("fget", "fset", "fdel"))
    elif isinstance(member, hybrid_property):
        _patch_propertylike(orig_class, member_name, member, "hybrid_properties", ("fget", "fset", "fdel", "expr"))
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
    :param category: The category of unpatched members to store the original member in
    :param fnames: The names of the property descriptor methods (e.g. fget, fset, fdel)
                   to override super() in
    """
    if category not in {"properties", "classproperties", "hybrid_properties"}:
        raise ValueError(f"Unsupported category '{category}'")
    if unsupported_fnames := set(fnames) - SUPPORTED_DESCRIPTORS:
        raise ValueError(f"Unsupported descriptor method '{list(unsupported_fnames)[0]}'")
    # Keep a reference to the original property-like member
    _store_unpatched(orig_class, prop_name, category)
    # Inject super() in the property descriptor methods
    # TODO: Figure out how to avoid casting
    funcs: PropertyDescriptors | HybridPropertyDescriptors = cast(PropertyDescriptors | HybridPropertyDescriptors, {
        fname: _inject_descriptor_super_proxy(getattr(prop, fname), orig_class)
        if fname in SUPER_ENABLED_DESCRIPTORS else
               getattr(prop, fname)
        for fname in fnames
    })
    new_prop: propertylike
    if isinstance(prop, classproperty):
        new_prop = type(prop)(**funcs)
    elif isinstance(prop, property):
        new_prop = property(**funcs)
    else:
        new_prop = hybrid_property(**funcs)
    # Replace the original property-like member
    setattr(orig_class, prop_name, new_prop)


def _patch_methodlike(orig_class: PatchedClass, method_name: str, method: methodlike, category: str) -> None:
    """Patch a method-like member in a class.

    :param orig_class: The class to patch
    :param method_name: The name of the method-like member to patch in the class
    :param method: The method-like object to replace the original member with
    :param category: The category of unpatched members to store the original member in
    """
    if category not in {"methods", "classmethods", "staticmethods"}:
        raise ValueError(f"Unsupported category '{category}'")
    # Keep a reference to the original method-like member
    _store_unpatched(orig_class, method_name, category)
    # Override super() in the method globals
    # XXX: Type is casted and type checking is disabled because mypy infers the wrong types
    #      for __func__ in classmethods (https://github.com/python/mypy/issues/3482)
    func = method if isinstance(method, FunctionType) else cast(FunctionType, method.__func__)
    new_func = _inject_super_proxy(func, orig_class)
    new_method = classmethod(new_func) if isinstance(method, classmethod) else new_func
    # Replace the original method
    setattr(orig_class, method_name, new_method)


def _store_unpatched(orig_class: PatchedClass, member_name: str, category: str) -> None:
    """Store a reference to the original member of a class.

    :param orig_class: The class to store the reference in
    :param member_name: The name of the member to store the reference for
    :param category: The category of unpatched members to store the original member in
    """
    # TODO: Fail if the member was already patched in any other category
    orig_members = get_members(orig_class)
    # None can be a valid value for the member, so we need to check if the member is in the class dict
    if member_name in orig_members:
        orig_class.__unpatched__[category][member_name].append(orig_members[member_name])
    else:
        # Since new members are patched into the original class, we need to keep track
        # if members are missing in the original class to avoid infinite recursion with super().
        orig_class.__unpatched__["missing"][member_name].append(None)


def _inject_super_proxy(func: FunctionType, orig_class: PatchedClass) -> FunctionType:
    """Return a new function from which super() will call SuperProxy().

    :param func: The function that will get SuperProxy injected
    :param orig_class: The original class that will be passed to SuperProxy
    """
    super_proxy = SuperProxy(orig_class)
    patch_classes = {cls for patch_class in orig_class.__patches__ for cls in patch_class.__mro__}
    copies: dict[FunctionType, FunctionType] = {}

    def copy(fn: FunctionType, inject: bool) -> FunctionType:
        if fn in copies:
            return copies[fn]
        globals = {**fn.__globals__, "super": super_proxy} if inject else fn.__globals__
        # Decorated functions are called from the closure of their wrappers, so copy the functions there too
        cells = [CellType() if isinstance(_get_cell_contents(cell), FunctionType) else cell
                 for cell in fn.__closure__ or ()]
        # Store the copy before filling its closure since functions can reference themselves
        copies[fn] = new_func = _copy_function(fn, globals, tuple(cells) or None)
        for cell, new_cell in zip(fn.__closure__ or (), cells, strict=True):
            if new_cell is not cell:
                new_cell.cell_contents = copy(cell.cell_contents, _calls_patch_super(cell.cell_contents, patch_classes))
        return new_func

    return copy(func, inject=True)


def _inject_descriptor_super_proxy(func: Any, orig_class: PatchedClass) -> Any:
    """Inject SuperProxy into a property descriptor function."""
    if isinstance(func, classmethod):
        return classmethod(_inject_super_proxy(cast(FunctionType, func.__func__), orig_class))
    return _inject_super_proxy(func, orig_class)


def _unwrap_callable(member: Any) -> Any:
    """Return the underlying function used for identity comparisons."""
    if isinstance(member, (property, hybrid_property)):
        member = member.fget
    if isinstance(member, classmethod):
        return member.__func__
    if isinstance(member, staticmethod):
        return member.__func__
    return member


def _get_codes(func: Any, seen: set[FunctionType] | None = None) -> set[CodeType]:
    """Return the code objects of a function and the functions in its closure."""
    seen = set() if seen is None else seen
    if not isinstance(func, FunctionType) or func in seen:
        return set()
    seen.add(func)
    return {func.__code__}.union(*(_get_codes(_get_cell_contents(cell), seen) for cell in func.__closure__ or ()))


def _get_cell_contents(cell: CellType) -> Any:
    """Return the contents of a closure cell or None if the cell is empty."""
    try:
        return cell.cell_contents
    except ValueError:
        return None


def _calls_patch_super(func: FunctionType, patch_classes: set[type]) -> bool:
    """Check whether a function calls super() from one of the patch classes."""
    # Functions referencing super in a class body get a __class__ cell with that class
    cells = dict(zip(func.__code__.co_freevars, func.__closure__ or (), strict=True))
    return "__class__" in cells and _get_cell_contents(cells["__class__"]) in patch_classes


def _copy_function(func: FunctionType, globals: dict[str, Any], closure: tuple[CellType, ...] | None) -> FunctionType:
    """Return a copy of a function with the given globals and closure."""
    new_func = FunctionType(func.__code__, globals, func.__name__, func.__defaults__, closure)
    # FunctionType() only takes the code, globals, name, defaults and closure, so copy the
    # rest, which includes what functools.wraps sets on wrappers
    for attr in ("__kwdefaults__", "__qualname__", "__module__", "__doc__", "__annotations__", "__type_params__"):
        setattr(new_func, attr, getattr(func, attr))
    new_func.__dict__.update(func.__dict__)
    return new_func
