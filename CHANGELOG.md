# Changelog

## v0.6.0 (unreleased)

- Fixed patched members using a snapshot of their module globals, which missed names bound or mocked later and broke `super(_Patch, self)` in module-level patch classes.
- Added a `super` global to the modules where patch classes call `super()`, which behaves like the built-in outside patched members but makes `super()` calls there slower.
- Copied the code of patch class members that use `super` into patched members, so their code can't be marshalled anymore.

## v0.5.1

- Fixed explicit `super(cls, self)` calls on non-patch classes to behave like the built-in.

## v0.5.0

- Added support for patching `declared_attr` members in models.
- Added support for patching hybrid methods.
- Allowed `rich_attrs` on any enum, not only `RichIntEnum` subclasses.
- Returned the patch enum from the decorator when patching enums.
- Fixed merging of CSS classes in rich enums.
- Fixed `super()` in patched methods wrapped by other decorators.
- Kept keyword-only defaults and other function attributes in patched functions.
- Deleted the draft GitHub release when publishing to PyPI fails.

## v0.4.2

- Updated the PyPI publish GitHub Action to v1.14.2 (Twine 7) to support wheel metadata version 2.5.

## v0.4.1

- Updated the PyPI publish GitHub Action to support wheel metadata version 2.5.

## v0.4.0

- Added support for patching `@classproperty` and `@strict_classproperty` members.
- Preserved subclass-aware classproperty resolution when patched implementations call `super()`.
- Added type stubs and extensive test coverage for classproperty patching scenarios.

## v0.3.2

- Switched project packaging and workflows from Poetry to uv.
- Fixed infinite recursion when patched members call `super()`, covering methods, class/static methods, properties, and newly added members.
- Reset patch tracking per subclass to avoid inheriting parent `__patches__`/`__unpatched__` stacks when patching class hierarchies.
- Expanded test coverage for `super()` chaining (including argument passing) and safeguarded missing-member lookups.

## v0.2.1

- Fixed maximum recursion depth exceeded when calling the original method of a patched class calls `super()`.

## v0.2.0

- Added compatibility for Indico v3.3.

## v0.1.0

- Initial release
