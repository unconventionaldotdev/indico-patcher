# Patching Enums

Enums in Indico are commonly used to define valid values in certain database columns and choices in form fields. This page of the guide explains how to patch Indico Enums to add members and carry over extra attributes.

- [Add new members](#add-new-members)
- [Inject extra attributes](#inject-extra-attributes)

## Add new members

```python
@patch(SurveyState)
class _SurveyState(IndicoEnum):
    # Adds a new member with value 101
    disabled = 101
```

Add new members to the original Enum by defining them in the patch Enum. In this example, the `disabled` member is added to the `SurveyState` Enum with the value `101`.

> [!IMPORTANT]
> Make sure to set a high-enough value to guarantee that values of patched members will not conflict with the values of present AND future members defined in the original Enum. This is especially important when patching Enums used in `pyIntEnum` columns.

```python
@patch(SurveyState, padding=100)
class _SurveyState(IndicoEnum):
    # Also adds a new member with value 101
    disabled = 1
```

You can more easily guarantee that values of patched members will not conflict using the `padding` argument of the `@patch()` decorator. Specify this argument to pad the value of each member by that amount when patching them into the original Enum.

```python
@patch(UserTitle, padding=100)
class _UserTitle(RichIntEnum):
    # Adds new members and their associated human-readable titles
    __titles__ = [None, 'Madam', 'Sir', 'Rev.']
    madam = 1  # value is 101
    sir = 2  # value is 102
    rev = 3  # value is 103
```

You can also patch Indico-defined `RichEnum`s and their variants. In this example, new user titles are added. The `__titles__` attribute defines how they should be displayed in the user interface and will be carried over to the original Enum.

## Inject extra attributes

```python
# Overrides the __page_sizes__ of the original PageSize Enum
@patch(PageSize, padding=100, extra_args=('__page_sizes__',))
class _PageSize:
    __page_sizes__ = {**PageSize.__page_sizes__, **{
        'A7': pagesizes.A7,
        'A8': pagesizes.A8,
    }}
    a7 = 1
    a8 = 2
```

By default, only the attributes used by `RichEnums` properties are carried over to the original Enum (e.g. `__titles__`, `__css_classes__`). Declare any extra attribute that needs to be carried over in the `extra_args` argument of the `@patch` decorator.
