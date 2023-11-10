# Indico Patching Guide

This guide describes how to use `indico-patcher` for multiple use cases as well as considerations to keep in mind when patching Indico. In this page, you can read general information applicable in all the use cases described in the rest of the guide.

- [Terminology](#terminology)
- [Usage](#usage)
- [FAQs](#faqs)
- [Keep in mind](#keep-in-mind)

The guide covers in detail the following use cases in dedicated pages:

1. [Patching Indico classes](./classes.md)
2. [Patching SQLAlchemy models](./models.md)
3. [Patching WTForms forms](./forms.md)
4. [Patching Enums](./enums.md)

## Terminology

### Patch class

A class that is decorated with the `@patch` decorator. It is uniquely used to patch an existing class in Indico and never to be imported and used directly.

### Original class

The Indico class that is being patched by a patch class, passed as argument to the `@patch()` decorator.

### Patched class

The class that results from the application of a patch class to an original class.

### Patch

A collection of attributes, methods and properties defined in a patch class that are injected into the original class. A patch is applied when the patch class is imported.

## Usage

Import the `patch` decorator from the `indico_patcher` module:

```python
from indico_patcher import patch
```

Import also the original class to be patched:

```python
from indico.modules.users.models.users import User
from indico.modules.users.models.user_titles import UserTitle
```

Define a patch class and decorate it with the `@patch()` decorator. The original class is passed as argument to the decorator. Since the patch class is not meant to be used directly, it is recommended to prefix its name with an underscore:

```python
@patch(User)
class _User:
    ...
```

This differs a bit in the case of enums, as the patch class must inherit from `Enum` or a subclass of it:

```python
@patch(UserTitle)
class _UserTitle(RichIntEnum):
    ...
```

Once the patch class is imported in the plugin, the original class will be patched. New members can be accessed as if they had been defined in the original class. All calls to existing members will be redirected to the ones defined in the patch class. For more specific usage details, please refer to the different pages of the guide.

## FAQs

### When are patches applied?

The patches are applied when the patch classes are imported. This means that you need to import the patch classes in your plugin's `__init__.py` file or in any other file that is imported by it. In some cases, like having a `patches.py` file with only patch classes, your linter may complain that the import is unused. You can safely silence this warning.

### Can the same class be patched multiple times?

Yes, this is possible and it is useful or unavoidable in some cases. For instance, you may want to patch the same class in two different modules of your plugin. Or you may enable two different plugins that patch the same class. In both cases, the patches will be applied in the order in which the patch classes are imported. This means that if multiple patches are overriding the same class member, the last one will be applied.

### What are some built-in tools to avoid patching Indico?

Indico provides many signals that can be used to extend its functionality without patching it. You can find a list of all the available signals in [`indico/core/signals`](https://github.com/indico/indico/tree/v3.2.8/indico/core/signals). A particularly useful one is [`interceptable_function`](https://github.com/indico/indico/blob/v3.2.8/indico/core/signals/plugin.py#L121). You may also want to check [Flask signals](https://flask.palletsprojects.com/en/2.0.x/api/#signals) and [SQLAlchemy event hooks](https://docs.sqlalchemy.org/en/14/core/event.html).

## Keep in mind

> [!WARNING]
> Remember! With great power comes great responsibility. Patch Indico as little as possible and only when it is absolutely necessary. Always try to find a way to achieve what you want without patching Indico.

> [!NOTE]
> The code examples and links to APIs in this guide make reference to Indico classes and dependencies as they are defined in `v3.2.8` of the codebase. Some class names, class locations and APIs may differ if you are using a different version of Indico.
