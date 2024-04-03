# This file is part of indico-patcher.
# Copyright (C) 2023 - 2024 UNCONVENTIONAL

from enum import EnumMeta

def extend_enum(enumeration: EnumMeta, name: str, value: int) -> EnumMeta: ...
