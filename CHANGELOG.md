# Changelog

## v0.4.0 (unreleased)

- *Nothing so far*

## v0.3.2

- Switched project packaging and workflows from Poetry to uv.
- Fixed infinite recursion when patched members call `super()`, covering
  methods, class/static methods, properties, and newly added members.
- Reset patch tracking per subclass to avoid inheriting parent
  `__patches__`/`__unpatched__` stacks when patching class hierarchies.
- Expanded test coverage for `super()` chaining (including argument passing) and
  safeguarded missing-member lookups.

## v0.2.1

- Fixed maximum recursion depth exceeded when calling the original method of a
  patched class calls `super()`.

## v0.2.0

- Added compatibility for Indico v3.3.

## v0.1.0

- Initial release
