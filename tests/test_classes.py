# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

from unittest.mock import MagicMock

import pytest
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.orm.attributes import QueryableAttribute
from sqlalchemy.sql.elements import ClauseElement

from indico_patcher.classes import SKIPPED_MEMBERS
from indico_patcher.classes import patch_class


@pytest.fixture
def Fool(db_base):
    class Fool(db_base):
        """Original docstring of the class."""

        __tablename__ = "fools"
        __probe__ = MagicMock()

        id = Column(Integer, primary_key=True)
        other_id = Column(Integer, ForeignKey("fools.id"))
        other = relationship("Fool", remote_side=[id])
        attr = "attr"

        @property
        def prop(self):
            return "prop"

        @hybrid_property
        def hprop(self):
            return "hprop"

        @staticmethod
        def smeth():
            Fool.__probe__()

        @classmethod
        def cmeth(cls):
            cls.__probe__()

        def meth(self):
            self.__probe__()

    return Fool


# -- decorator -----------------------------------------------------------------

@pytest.mark.parametrize("cls", (
    object(), int(), str(), float(), list(), dict(), tuple(), set(), frozenset(),  # noqa: UP018
))
def test_patch_class_for_instances(cls):
    with pytest.raises(TypeError):
        @patch_class(cls)
        class _Fool:
            pass


@pytest.mark.parametrize("cls", (
    object, int, str, float, list, dict, tuple, set, frozenset, type,
))
def test_patch_class_for_builtins(cls):
    with pytest.raises(TypeError):
        @patch_class(cls)
        class _Fool:
            pass


def test_patch_class_for_skipped_members(Fool):
    # Simulate class being defined in a different module
    Fool.__module__ = "not_test_class"

    @patch_class(Fool)
    class _Fool:
        __mapper__ = None
        _sa_class_manager = None

    for member in SKIPPED_MEMBERS:
        assert getattr(Fool, member) is not getattr(_Fool, member)


def test_patch_class_multiple_times(Fool):
    orig_attr = Fool.attr
    orig_meth = Fool.meth

    @patch_class(Fool)
    class Foo:
        attr = None

    @patch_class(Fool)
    class Bar:
        def meth(self):
            pass

    assert Fool.__patches__ == [Foo, Bar]
    assert Fool.__unpatched__["attributes"]["attr"] == orig_attr
    assert Fool.__unpatched__["methods"]["meth"] == orig_meth


def test_patch_class_with_subclass(Fool):
    class Foo:
        foo = None

    @patch_class(Fool)
    class Bar(Foo):
        bar = None

    assert Fool.__patches__ == [Bar]
    assert hasattr(Fool, "foo")
    assert hasattr(Fool, "bar")


# -- attributes ----------------------------------------------------------------

def test_patch_class_for_attribute(Fool):
    @patch_class(Fool)
    class _Fool:
        attr = "patched"
        foo = "foo"

    assert Fool.attr != "attr"
    assert Fool.foo == "foo"


# -- properties ----------------------------------------------------------------

def test_patch_class_for_property_with_new(Fool):
    @patch_class(Fool)
    class _Fool:
        @property
        def foo(self):
            return self.__probe__()

        @foo.setter
        def foo(self, value):
            self.__probe__()

        @foo.deleter
        def foo(self):
            self.__probe__()

    assert isinstance(Fool.foo, property)
    assert hasattr(Fool.foo, "fget")
    assert hasattr(Fool.foo, "fset")
    assert hasattr(Fool.foo, "fdel")
    fool = Fool()
    fool.foo  # noqa: B018
    fool.foo = None
    del fool.foo
    assert fool.__probe__.call_count == 3


def test_patch_class_for_property_with_super(Fool):
    @patch_class(Fool)
    class _Fool:
        @property
        def prop(self):
            return super().prop + "prop"

    fool = Fool()
    assert fool.prop == "propprop"


# -- hybrid properties ---------------------------------------------------------

def test_patch_class_for_hybrid_property_with_new(Fool):
    @patch_class(Fool)
    class _Fool:
        @hybrid_property
        def foo(self):
            return "foo"

        @foo.expression
        def foo(cls):
            return ClauseElement()

    fool = Fool()
    assert fool.foo == "foo"
    assert isinstance(Fool.foo, QueryableAttribute)
    assert hasattr(Fool.foo, "expression")


def test_patch_class_for_hybrid_property_with_super(Fool):
    @patch_class(Fool)
    class _Fool:
        @hybrid_property
        def hprop(self):
            return super().hprop + "hprop"

    fool = Fool()
    assert fool.hprop == "hprophprop"


# -- methods -------------------------------------------------------------------

def test_patch_class_for_method_with_new(Fool):
    assert hasattr(Fool, "meth")

    @patch_class(Fool)
    class _Fool:
        def meth(self):
            pass

    Fool().meth()
    assert Fool.__probe__.call_count == 0


def test_patch_class_for_method_with_super(Fool):
    @patch_class(Fool)
    class _Fool:
        def meth(self):
            super().meth()
            self.__probe__()

    Fool().meth()
    assert Fool.__probe__.call_count == 2


def test_patch_class_for_method_with_super_in_non_patched(Fool):
    @patch_class(Fool)
    class _Fool:
        def foo(self):
            super().meth()

    Fool().foo()
    assert Fool.__probe__.call_count == 1


# -- classmethods --------------------------------------------------------------

def test_patch_class_for_classmethod_with_new(Fool):
    assert hasattr(Fool, "cmeth")

    @patch_class(Fool)
    class _Fool:
        @classmethod
        def cmeth(cls):
            pass

    Fool.cmeth()
    assert Fool.__probe__.call_count == 0


def test_patch_class_for_classmethod_with_super(Fool):
    @patch_class(Fool)
    class _Fool:
        @classmethod
        def cmeth(cls):
            super().cmeth()
            cls.__probe__()

    Fool.cmeth()
    assert Fool.__probe__.call_count == 2


def test_patch_class_for_classmethod_with_super_in_non_patched(Fool):
    @patch_class(Fool)
    class _Fool:
        @classmethod
        def foo(cls):
            super().cmeth()

    Fool.foo()
    assert Fool.__probe__.call_count == 1


# -- staticmethods -------------------------------------------------------------

def test_patch_class_for_staticmethod_with_new(Fool):
    assert hasattr(Fool, "smeth")

    @patch_class(Fool)
    class _Fool:
        @staticmethod
        def smeth():
            pass

    Fool.smeth()
    assert Fool.__probe__.call_count == 0


def test_patch_class_for_staticmethod_with_super(Fool):
    @patch_class(Fool)
    class _Fool:
        @staticmethod
        def smeth():
            super().smeth()
            Fool.__probe__()

    Fool.smeth()
    assert Fool.__probe__.call_count == 2


def test_patch_class_for_staticmethod_with_super_in_non_patched(Fool):
    @patch_class(Fool)
    class _Fool:
        @staticmethod
        def foo():
            super().smeth()

    Fool.foo()
    assert Fool.__probe__.call_count == 1


# -- SQLAlchemy ----------------------------------------------------------------

def test_patch_class_for_db_column_with_new(Fool, db_base, db_session):
    @patch_class(Fool)
    class _Fool:
        name = Column(String)

    # Recreate tables with new columns
    connection = db_session.connection()
    db_base.metadata.drop_all(connection)
    db_base.metadata.create_all(connection)

    fool = Fool(name="fool")
    db_session.add(fool)
    db_session.flush()
    assert fool.name == "fool"


def test_patch_class_for_relationship_with_new(Fool, db_base, db_session):
    class Tag(db_base):
        __tablename__ = "tags"
        id = Column(Integer, primary_key=True)

    @patch_class(Fool)
    class _Fool:
        tag_id = Column(Integer, ForeignKey("tags.id"))
        tag = relationship("Tag", backref=backref("fools"))

    # Recreate tables with new columns
    connection = db_session.connection()
    db_base.metadata.drop_all(connection)
    db_base.metadata.create_all(connection)

    tag = Tag()
    fool1 = Fool(tag=tag)
    fool2 = Fool(tag=tag)
    db_session.add(tag)
    db_session.add(fool1)
    db_session.add(fool2)
    db_session.flush()
    assert fool1.tag == tag
    assert fool2.tag == tag
    assert tag.fools == [fool1, fool2]
    assert db_session.query(Fool).filter(Fool.tag == tag).all() == [fool1, fool2]


def test_patch_class_for_relationship_with_overwriting(Fool, db_session):
    @patch_class(Fool)
    class _Fool:
        other = relationship("Fool", remote_side=[Fool.id], backref=backref("others"))

    fool1 = Fool()
    fool2 = Fool(other=fool1)
    fool3 = Fool(other=fool1)
    db_session.add(fool1)
    db_session.add(fool2)
    db_session.add(fool3)
    db_session.flush()
    assert fool2.other == fool1
    assert fool3.other == fool1
    assert fool1.others == [fool2, fool3]
    assert db_session.query(Fool).filter(Fool.other == fool1).all() == [fool2, fool3]
