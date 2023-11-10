# Patching WTForms

Forms in Indico are defined using the [WTForms](https://wtforms.readthedocs.io/) library and most of them get rendered based on the fields defined in the form classes. Apply techniques covered in the [Patching Indico classes](./classes.md) page of this guide to add, modify, remove or reorder fields in forms, among other use cases.

- [Add new fields](#add-new-fields)
- [Modify existing fields](#modify-existing-fields)
- [Remove existing fields](#remove-existing-fields)
- [Reorder fields](#reorder-fields)
- [Alter field validators](#alter-field-validators)
- [Alter field choices](#alter-field-choices)

## Add new fields

```python
@patch(EventDataForm)
class _EventDataForm:
    # Adds new field (this usually requires adding a new column to the database)
    is_sponsored = BooleanField(_('Sponsored'), [DataRequired()], widget=SwitchWidget())
```

Define new fields in the patch class as you would in the original form class. You can add custom validation functions and `@genereated_data` methods like in non-patched form classes.

> [!IMPORTANT]
> If the field is used to populate an SQLAlchemy model object, you will need to add the corresponding column in the database. For more information, please refer to the [Patching SQLAlchemy models](./models.md) page of the guide.

> [!NOTE]
> New fields will be rendered by default at the end of the form. To customize the order of fields, please refer to the [reordering fields](#reorder-fields) section.

## Modify existing fields

```python
@patch(EventDataForm)
class _EventDataForm:
    # Replaces the original field
    description = StringField(_('Description'), EventDataForm.description.validators)
```

Redefine existing fields in the patch class, for instance, to change the type of a field. In this example, the original `TextAreaField` field is replaced by a `StringField` and the original validators are preserved.

## Remove existing fields

```python
@patch(EventDataForm)
class _EventDataForm:
    # Removes the original field
    del EventDataForm.url_shortcut
```

Remove fields by simply deleting them from the original form class.

> [!IMPORTANT]
> If the field is used to populate an SQLAlchemy model object, you may need to remove the corresponding column in the database, to alter the column to be nullable, or to set a default value in the column definition. For more information, please refer to the [Patching SQLAlchemy models](./models.md) page of this guide.

> [!NOTE]
> Patching for removing fields is not necessary, as you are deleting the attributes in the original form class directly. Deleting the attributes in the original form class from a patch class may still be a good idea to keep all modifications in the same code block.

## Reorder fields

```python
@patch(EventDataForm)
class _EventDataForm:
    # Specifies the order of fields
    def __iter__(self):
        for field_name in self._fields:
            if field_name in ('is_sponsored',):
                continue
            if field_name == 'title':
                yield self._fields['is_sponsored']
            yield self._fields[field_name]
```

You have all the flexibility to reorder fields in a form with the `__iter__()` method. In this example, the newly added `is_sponsored` field, which would be displayed as the last field, is moved before the `title` field.

## Alter field validators

```python
@patch(EventDataForm)
class _EventDataForm:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Removes all validators from title field
        self.title.validators = []
```

Override the `__init__()` method of the original form class to alter the validators of existing fields. In this example, all validators are removed from the `title` field.

```python
BANNED_SHORTCUTS = {'admin', 'indico', 'event', 'official'}

@patch(EventDataForm)
class _EventDataForm:
    # Overrides validator function
    def validate_url_shortcut(self, field):
        super().validate_url_shortcut(field)
        if field.data in BANNED_SHORTCUTS:
            raise ValidationError(_('This URL shortcut is not allowed.'))
```

Override custom validator functions to replace or extend validation conditions. In this example, the `validate_url_shortcut()` function is overridden to add an additional check for banned shortcuts.

## Alter field choices

```python
@patch(EventLanguagesForm)
class _EventLanguagesForm:
    __disabled_locales__ = {'en_US', 'fr_FR'}

    # Overrides field choices
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_locale.choices = [
            (id_, title) for id_, title in EventLanguagesForm.default_locale.choices
            if id_ not in self.__disabled_locales__
        ]
```

Override the `__init__()` method of the form class to alter the choices of existing fields. In this example, some locales are removed from the list of choices in the `default_locale` field.

> [!IMPORTANT]
> Choices are defined from Enums in `IndicoEnumSelectField`. You can more reliably alter available choices in those fields by patching the Enum class. For more information, please refer to the [Patching Enums](./enums.md) page of this guide.
