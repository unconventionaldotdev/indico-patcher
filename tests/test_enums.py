# This file is part of indico-patcher.
# Copyright (C) 2023 - 2026 UNCONVENTIONAL

from enum import Enum
from enum import EnumMeta

import pytest
from pytest import raises

from indico.util.enum import IndicoIntEnum
from indico.util.enum import RichIntEnum

from indico_patcher.enums import patch_enum


class Arcana(Enum):
    major = 1
    minor = 2


@pytest.fixture
def TarotCard():
    class TarotCard(Enum):
        the_fool = 0
        the_magician = 1
        the_high_priestess = 2

    return TarotCard


@pytest.fixture
def RichTarotCard():
    class RichTarotCard(RichIntEnum):
        __deck__ = "Rider-Waite Tarot"
        __titles__ = ["The Fool", "The Magician", "The High Priestess"]
        __arcana__ = [Arcana.major, Arcana.major, Arcana.major]
        the_fool = 0
        the_magician = 1
        the_high_priestess = 2

        @property
        def arcana(self):
            return self.__arcana__[self]

    return RichTarotCard


def test_patch_enum(TarotCard):
    @patch_enum(TarotCard)
    class _TarotCard(Enum):
        the_empress = 3
        the_emperor = 4

    assert TarotCard.the_magician.value == 1
    assert TarotCard.the_high_priestess.value == 2
    assert TarotCard.the_empress.value == 3
    assert TarotCard.the_emperor.value == 4


def test_patch_enum_with_padding(TarotCard):
    @patch_enum(TarotCard, padding=22)
    class _TarotCardB(Enum):
        the_one_of_wands = 1
        the_two_of_wands = 2

    assert TarotCard.the_one_of_wands.value == 23
    assert TarotCard.the_two_of_wands.value == 24


def test_patch_enum_with_negative_padding(TarotCard):
    with raises(ValueError):
        @patch_enum(TarotCard, padding=-1)
        class _TarotCardA(Enum):
            pass


def test_patch_enum_only_for_enums(TarotCard):
    with raises(TypeError):
        @patch_enum(TarotCard)
        class _TarotCard:
            pass

    with raises(TypeError):
        @patch_enum(type)
        class Foo(Enum):
            pass


def test_patch_enum_with_rich_attrs(TarotCard):
    with raises(ValueError):
        @patch_enum(TarotCard, rich_attrs=("__arcana__",))
        class _TarotCard(Enum):
            pass


def test_patch_richenum(RichTarotCard):
    @patch_enum(RichTarotCard, rich_attrs=("__arcana__",))
    class _TarotCard(Enum):
        __titles__ = ["The Empress", "The Emperor"]
        __arcana__ = [Arcana.major, Arcana.major]
        the_empress = 3
        the_emperor = 4

    assert RichTarotCard.the_fool.title == "The Fool"
    assert RichTarotCard.the_magician.title == "The Magician"
    assert RichTarotCard.the_high_priestess.title == "The High Priestess"
    assert RichTarotCard.the_empress.title == "The Empress"
    assert RichTarotCard.the_empress.arcana == Arcana.major
    assert RichTarotCard.the_emperor.title == "The Emperor"
    assert RichTarotCard.the_emperor.arcana == Arcana.major


def test_patch_richenum_with_padding(RichTarotCard):
    @patch_enum(RichTarotCard, padding=22, rich_attrs=("__arcana__",))
    class _TarotCard(Enum):
        __titles__ = [None, "The One of Wands", "The Two of Wands"]
        __arcana__ = [None, Arcana.minor, Arcana.minor]
        the_one_of_wands = 1
        the_two_of_wands = 2

    assert RichTarotCard.the_one_of_wands.title == "The One of Wands"
    assert RichTarotCard.the_one_of_wands.arcana == Arcana.minor
    assert RichTarotCard.the_two_of_wands.title == "The Two of Wands"
    assert RichTarotCard.the_two_of_wands.arcana == Arcana.minor


def test_patch_enum_with_extra_attrs(RichTarotCard):
    @patch_enum(RichTarotCard, extra_attrs=("__deck__", "__meanings__",))
    class _TarotCard(Enum):
        __deck__ = "Hermetic Tarot"
        __meanings__ = {
            "the_fool": "New beginnings. Innocence. Leap of faith.",
            "the_magician": "Mastery of skills. Power of manifestation. Elemental forces.",
            "the_high_priestess": "Intuition. Hidden knowledge. Spiritual insight.",
        }

    assert RichTarotCard.__deck__ == "Hermetic Tarot"
    assert hasattr(RichTarotCard, "__meanings__")


def test_patch_enum_with_extra_attrs_collision(RichTarotCard):
    with raises(ValueError):
        @patch_enum(RichTarotCard, extra_attrs=("__titles__",))
        class _TarotCard(Enum):
            pass


@pytest.fixture
def TitledColor():
    class TitledColor(IndicoIntEnum):
        __titles__ = ["Red", "Green"]
        red = 0
        green = 1

        def get_title(self):
            return self.__titles__[self.value]

    return TitledColor


def test_patch_enum_returns_patch(TarotCard):
    @patch_enum(TarotCard)
    class _TarotCard(Enum):
        the_empress = 3

    assert isinstance(_TarotCard, EnumMeta)
    assert _TarotCard.the_empress.value == 3


def test_patch_non_rich_enum_titles(TitledColor):
    @patch_enum(TitledColor)
    class _TitledColor(IndicoIntEnum):
        __titles__ = ["Blue"]
        blue = 2

    assert TitledColor.red.get_title() == "Red"
    assert TitledColor.blue.get_title() == "Blue"


def test_patch_non_rich_enum_titles_with_padding(TitledColor):
    @patch_enum(TitledColor, padding=10)
    class _TitledColor(IndicoIntEnum):
        __titles__ = ["Blue"]
        blue = 0

    assert TitledColor.blue.value == 10
    assert TitledColor.green.get_title() == "Green"
    assert TitledColor.blue.get_title() == "Blue"


def test_patch_non_rich_enum_titles_missing_in_original(TarotCard):
    @patch_enum(TarotCard)
    class _TarotCard(Enum):
        __titles__ = ["The Empress"]
        the_empress = 3

    assert not hasattr(TarotCard, "__titles__")


def test_patch_non_rich_enum_titles_not_defined_in_patch(TitledColor):
    @patch_enum(TitledColor)
    class _TitledColor(IndicoIntEnum):
        blue = 2

    assert TitledColor.red.get_title() == "Red"
    assert TitledColor.green.get_title() == "Green"
    assert TitledColor.blue.value == 2


def test_patch_non_rich_enum_titles_in_extra_attrs_collision(TitledColor):
    with raises(ValueError):
        @patch_enum(TitledColor, extra_attrs=("__titles__",))
        class _TitledColor(IndicoIntEnum):
            pass


def test_patch_richenum_css_classes():
    class Suit(RichIntEnum):
        __titles__ = ["Cups"]
        __css_classes__ = ["blue"]
        cups = 0

    @patch_enum(Suit, padding=5)
    class _Suit(RichIntEnum):
        __titles__ = ["Wands"]
        __css_classes__ = ["red"]
        wands = 0

    assert Suit.cups.css_class == "blue"
    assert Suit.wands.title == "Wands"
    assert Suit.wands.css_class == "red"
