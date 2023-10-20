# This file is part of indico-patcher.
# Copyright (C) 2023 UNCONVENTIONAL

from enum import Enum
from unittest import mock

from indico_patcher.main import patch


@mock.patch("indico_patcher.main.patch_class")
def test_patch_for_class(patch_class):
    class Fool:
        pass

    patch(Fool)
    patch_class.assert_called_once_with(Fool)


@mock.patch("indico_patcher.main.patch_enum")
def test_patch_for_enum(patch_enum):
    class TarotCard(Enum):
        pass

    patch(TarotCard, padding=22, rich_attrs=("__arcana__",))
    patch_enum.assert_called_once_with(TarotCard, padding=22, rich_attrs=("__arcana__",))
