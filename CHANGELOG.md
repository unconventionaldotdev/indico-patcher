# Changelog

## v0.6.2 (unreleased)

- Required release tags to be signed.
- Fixed patching a rich enum with padding raising `IndexError` on `css_class` when neither the enum nor the patch has CSS classes.
- Fixed patched properties losing their type when it is a subclass of `property`.

## v0.6.1

- Fixed patches of a class being reset when subclassing it after patching it twice or patching one of its subclasses.
- Fixed `__init_subclass__` of patched classes receiving the patched class instead of the new subclass.

## v0.6.0

- Fixed patched members not seeing module globals bound or mocked after patching.
- Raised `TypeError` when patching a member that calls `super()` and uses `super` as another name.

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
