# This file is part of indico-patcher.
# Copyright (C) 2023 - 2026 UNCONVENTIONAL

class Mixin:
    def meth(self, arg):
        super().meth(f"{arg}>mixin")
