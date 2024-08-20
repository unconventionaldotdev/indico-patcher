# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

from collections import defaultdict
from unittest import mock

import pytest
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import ClauseElement

from indico_patcher.util import SUPER_ENABLED_DESCRIPTORS
from indico_patcher.util import SuperProxy
from indico_patcher.util import _inject_super_proxy
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


@pytest.fixture
def _Fool():
    class _Fool:
        @property
        def prop(self):
            pass

        @prop.setter
        def prop(self, value):
            pass

        @prop.deleter
        def prop(self):
            pass

        @hybrid_property
        def hprop(self):
            pass

        @hprop.setter
        def hprop(self, value):
            pass

        @hprop.deleter
        def hprop(self):
            pass

        @hprop.expression
        def hprop(cls):
            return ClauseElement()

        @staticmethod
        def smeth():
            pass

        @classmethod
        def cmeth(cls):
            pass

        def meth(self):
            pass

    return _Fool

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
    prop = Fool.__dict__["prop"]
    patch_member(Fool, "prop", Fool.prop)
    _patch_propertylike.assert_called_with(Fool, "prop", prop, "properties", ("fget", "fset", "fdel"))
    hprop = Fool.__dict__["hprop"]
    patch_member(Fool, "hprop", hprop)
    _patch_propertylike.assert_called_with(Fool, "hprop", hprop, "hybrid_properties", ("fget", "fset", "fdel", "expr"))


@mock.patch("indico_patcher.util._patch_methodlike")
def test_patch_member_for_methodlike(_patch_methodlike, Fool):
    meth = Fool.__dict__["meth"]
    patch_member(Fool, "meth", Fool.meth)
    _patch_methodlike.assert_called_with(Fool, "meth", meth, "methods")
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


@mock.patch("indico_patcher.util._store_unpatched")
@mock.patch("indico_patcher.util._inject_super_proxy")
def test_patch_propertylike_for_property(_inject_super_proxy, _store_unpatched, Fool, _Fool):
    mock_func = mock.Mock()
    _inject_super_proxy.return_value = mock_func
    fnames = ("fget", "fset", "fdel")
    prop = _Fool.__dict__["prop"]
    _patch_propertylike(Fool, "prop", prop, "properties", fnames)
    new_prop = Fool.__dict__["prop"]
    _store_unpatched.assert_called_with(Fool, "prop", "properties")
    expected_calls = []
    for fname in fnames:
        func = getattr(prop, fname)
        if fname in SUPER_ENABLED_DESCRIPTORS:
            expected_calls.append(mock.call(func, Fool))
            assert getattr(new_prop, fname) == mock_func
        else:
            assert getattr(new_prop, fname) == func
    _inject_super_proxy.assert_has_calls(expected_calls)


@mock.patch("indico_patcher.util._store_unpatched")
@mock.patch("indico_patcher.util._inject_super_proxy")
def test_patch_propertylike_for_hybrid_property(_inject_super_proxy, _store_unpatched, Fool, _Fool):
    mock_func = mock.Mock()
    _inject_super_proxy.return_value = mock_func
    fnames = ("fget", "fset", "fdel", "expr")
    hprop = _Fool.__dict__["hprop"]
    _patch_propertylike(Fool, "hprop", hprop, "hybrid_properties", fnames)
    new_hprop = Fool.__dict__["hprop"]
    _store_unpatched.assert_called_with(Fool, "hprop", "hybrid_properties")
    expected_calls = []
    for fname in fnames:
        func = getattr(hprop, fname)
        if fname in SUPER_ENABLED_DESCRIPTORS:
            expected_calls.append(mock.call(func, Fool))
            assert getattr(new_hprop, fname) == mock_func
        else:
            assert getattr(new_hprop, fname) == func
    _inject_super_proxy.assert_has_calls(expected_calls)


# -- method-like ---------------------------------------------------------------

def test_patch_methodlike_for_invalid_values(Fool):
    with pytest.raises(ValueError):
        _patch_methodlike(Fool, None, None, "properties")


@mock.patch("indico_patcher.util._store_unpatched")
@mock.patch("indico_patcher.util._inject_super_proxy")
def test_patch_methodlike_for_method(_inject_super_proxy, _store_unpatched, Fool, _Fool):
    mock_func = mock.Mock()
    _inject_super_proxy.return_value = mock_func
    meth = _Fool.__dict__["meth"]
    _patch_methodlike(Fool, "meth", meth, "methods")
    _store_unpatched.assert_called_with(Fool, "meth", "methods")
    _inject_super_proxy.assert_called_with(meth, Fool)
    assert Fool.meth == mock_func



@mock.patch("indico_patcher.util._store_unpatched")
@mock.patch("indico_patcher.util._inject_super_proxy")
def test_patch_methodlike_for_classmethod(_inject_super_proxy, _store_unpatched, Fool, _Fool):
    mock_func = mock.Mock()
    _inject_super_proxy.return_value = mock_func
    cmeth = _Fool.__dict__["cmeth"]
    _patch_methodlike(Fool, "cmeth", cmeth, "classmethods")
    _store_unpatched.assert_called_with(Fool, "cmeth", "classmethods")
    _inject_super_proxy.assert_called_with(cmeth.__func__, Fool)
    assert Fool.cmeth.__func__ == mock_func


@mock.patch("indico_patcher.util._store_unpatched")
@mock.patch("indico_patcher.util._inject_super_proxy")
def test_patch_methodlike_for_staticmethod(_inject_super_proxy, _store_unpatched, Fool, _Fool):
    mock_func = mock.Mock()
    _inject_super_proxy.return_value = mock_func
    smeth = _Fool.__dict__["smeth"]
    _patch_methodlike(Fool, "smeth", smeth, "staticmethods")
    _store_unpatched.assert_called_with(Fool, "smeth", "staticmethods")
    _inject_super_proxy.assert_called_with(smeth.__func__, Fool)
    assert Fool.smeth == mock_func


# -- store unpatched member ----------------------------------------------------

@pytest.mark.parametrize(("member_name", "category"), [
    ("attr", "attributes"),
    ("prop", "properties"),
    ("hprop", "hybrid_properties"),
    ("meth", "methods"),
    ("cmeth", "classmethods"),
    ("smeth", "staticmethods"),
])
def test_store_unpatched_member(member_name, category, Fool):
    _store_unpatched(Fool, member_name, category)
    assert Fool.__unpatched__[category][member_name] == Fool.__dict__[member_name]


# -- inject super proxy --------------------------------------------------------

def test_inject_super_proxy(Fool):
    orig_meth = Fool.meth

    class _Fool:
        def meth(self):
            pass

    new_func = _inject_super_proxy(_Fool.meth, Fool)
    super_proxy = new_func.__globals__["super"]
    assert "super" not in orig_meth.__globals__
    assert isinstance(super_proxy, SuperProxy)
    assert super_proxy.orig_class == Fool
    assert new_func.__code__ == _Fool.meth.__code__
    assert new_func.__name__ == _Fool.meth.__name__
    assert new_func.__defaults__ == _Fool.meth.__defaults__
    assert new_func.__closure__ == _Fool.meth.__closure__
