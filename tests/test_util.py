# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

from collections import defaultdict
from unittest import mock

import pytest
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import ClauseElement

from indico_patcher.util import SuperProxy
from indico_patcher.util import _patch_attr
from indico_patcher.util import _patch_methodlike
from indico_patcher.util import _patch_propertylike
from indico_patcher.util import _store_unpatched
from indico_patcher.util import get_members
from indico_patcher.util import patch_member


@pytest.fixture
def Fool():
    class Fool:
        __unpatched__ = defaultdict(dict)
        attr = None

        @property
        def prop(self):
            pass

        @hybrid_property
        def hprop(self):
            pass

        @staticmethod
        def smeth():
            pass

        @classmethod
        def cmeth(cls):
            pass

        def meth(self):
            pass

    return Fool


# -- super proxy ---------------------------------------------------------------

def test_superproxy_repr(Fool):
    class _Fool:
        pass

    fool = Fool()
    classname = f"{_Fool.__module__}.{_Fool.__name__}"
    duper = SuperProxy(Fool)(_Fool, fool)
    assert repr(duper) == f"<duper: {classname}, {fool}>"
    duper = SuperProxy(Fool)(_Fool)
    assert repr(duper) == f"<duper: {classname}, None>"
    duper = SuperProxy(Fool)()
    assert repr(duper) == "<duper: None, None>"


# -- get full dict -------------------------------------------------------------

def test_get_members():
    class A:
        foo = "a"
        bar = "a"

    class B(A):
        foo = "b"

    class C(B):
        pass

    assert B.foo == get_members(B)["foo"]
    assert C.foo == get_members(C)["foo"]
    assert C.bar == get_members(C)["bar"]


def test_get_members_for_multiple_bases():
    class A:
        foo = "a"

    class B:
        foo = "b"

    class C(B, A):
        pass

    assert C.foo == get_members(C)["foo"]


def test_get_members_for_object():
    with pytest.raises(TypeError):
        get_members(object)


# -- members -------------------------------------------------------------------

def test_patch_member_for_attribute(Fool):
    obj = object()
    patch_member(Fool, "attr", obj)
    assert Fool.attr is obj


@mock.patch("indico_patcher.util._patch_propertylike")
def test_patch_member_for_propertylike(_patch_propertylike, Fool):
    patch_member(Fool, "prop", Fool.prop)
    _patch_propertylike.assert_called_with(Fool, "prop", Fool.prop, "properties", ("fget",))
    hprop = Fool.__dict__["hprop"]
    patch_member(Fool, "hprop", hprop)
    _patch_propertylike.assert_called_with(Fool, "hprop", hprop, "hybrid_properties", ("fget", "expression"))


@mock.patch("indico_patcher.util._patch_methodlike")
def test_patch_member_for_methodlike(_patch_methodlike, Fool):
    patch_member(Fool, "meth", Fool.meth)
    _patch_methodlike.assert_called_with(Fool, "meth", Fool.meth, "methods")
    smeth = Fool.__dict__["smeth"]
    patch_member(Fool, "smeth", smeth)
    _patch_methodlike.assert_called_with(Fool, "smeth", smeth, "staticmethods")
    cmeth = Fool.__dict__["cmeth"]
    patch_member(Fool, "cmeth", cmeth)
    _patch_methodlike.assert_called_with(Fool, "cmeth", cmeth, "classmethods")


# -- attribute -----------------------------------------------------------------

def test_patch_attr(Fool):
    orig_attr = Fool.attr
    obj = object()
    _patch_attr(Fool, "attr", obj)
    assert Fool.attr is obj
    assert Fool.__unpatched__["attributes"]["attr"] == orig_attr


# -- property-like -------------------------------------------------------------

def test_patch_propertylike_for_invalid_values(Fool):
    with pytest.raises(ValueError):
        _patch_propertylike(Fool, None, None, "methods", ("fget",))
    with pytest.raises(ValueError):
        _patch_propertylike(Fool, None, None, "properties", ("foo",))


def test_patch_propertylike_for_property(Fool):
    fnames = ("fget",)
    orig_prop = Fool.prop

    class _Fool:
        @property
        def prop(self):
            pass

    _patch_propertylike(Fool, "prop", _Fool.prop, "properties", fnames)
    assert Fool.prop == _Fool.prop
    assert Fool.__unpatched__["properties"]["prop"] == orig_prop
    for fname in fnames:
        func = getattr(Fool.prop, fname)
        assert isinstance(func.__globals__["super"], SuperProxy)


def test_patch_propertylike_for_hybrid_property(Fool):
    fnames = ("fget", "expression")
    orig_hprop = Fool.hprop

    class _Fool:
        @hybrid_property
        def hprop(self):
            pass

        @hprop.expression
        def hprop(cls):
            return ClauseElement()

    new_hprop = _Fool.__dict__["hprop"]
    _patch_propertylike(Fool, "hprop", new_hprop, "hybrid_properties", fnames)
    assert Fool.__dict__["hprop"] == new_hprop
    assert Fool.__unpatched__["hybrid_properties"]["hprop"] == orig_hprop
    for fname in fnames:
        func = getattr(new_hprop, fname)
        assert isinstance(func.__globals__["super"], SuperProxy)


# -- method-like ---------------------------------------------------------------

def test_patch_methodlike_for_invalid_values(Fool):
    with pytest.raises(ValueError):
        _patch_methodlike(Fool, None, None, "properties")


def test_patch_methodlike_for_method(Fool):
    orig_meth = Fool.meth

    class _Fool:
        def meth(self):
            pass

    _patch_methodlike(Fool, "meth", _Fool.meth, "methods")
    assert Fool.meth == _Fool.meth
    assert Fool.__unpatched__["methods"]["meth"] == orig_meth
    assert isinstance(Fool.meth.__globals__["super"], SuperProxy)


def test_patch_methodlike_for_classmethod(Fool):
    orig_cmeth = Fool.cmeth

    class _Fool:
        @classmethod
        def cmeth(cls):
            pass

    _patch_methodlike(Fool, "cmeth", _Fool.cmeth, "classmethods")
    assert Fool.cmeth == _Fool.cmeth
    assert Fool.__unpatched__["classmethods"]["cmeth"] == orig_cmeth
    assert isinstance(Fool.cmeth.__globals__["super"], SuperProxy)


def test_patch_methodlike_for_staticmethod(Fool):
    orig_smeth = Fool.smeth

    class _Fool:
        @staticmethod
        def smeth():
            pass

    _patch_methodlike(Fool, "smeth", _Fool.smeth, "staticmethods")
    assert Fool.smeth == _Fool.smeth
    assert Fool.__unpatched__["staticmethods"]["smeth"] == orig_smeth
    assert isinstance(Fool.smeth.__globals__["super"], SuperProxy)


# -- store unpatched member ----------------------------------------------------

def test_store_unpatched_member(Fool):
    _store_unpatched(Fool, "attr", "attributes")
    assert Fool.__unpatched__["attributes"]["attr"] == Fool.attr
