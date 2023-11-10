# Patching Indico classes

This page of the guide explains the general mechanism to add and override attributes, methods and properties in Indico classes. For more specific use cases, like patching [SQLAlchemy models](./models.md) or [WTForms forms](./forms.md), please refer to their respective pages of the guide.

- [Add and override attributes](#add-and-override-attributes)
- [Add and override methods](#add-and-override-methods)
- [Add and override properties](#add-and-override-properties)

## Add and override attributes

```python
@patch(RHUserBlock)
class _RHUserBlock:
    # Adds new attribute
    error_message = L_('Action not allowed on this user.')
```

Add a new attribute to the original class by simply defining it in the patch class. In this example, an `error_message` attribute is added to `RHUserBlock`.

```python
@patch(LocalRegistrationHandler)
class _LocalRegistrationHandler:
    # Overrides existing attribute
    form = CustomLocalRegistrationForm
```

Override an existing attribute in the original class by assigning a new value to it in the patch class. In this example, a plugin-defined form is assigned to be used by `LocalRegistrationHandler` instead of the original `LocalRegistrationForm`.

## Add and override methods

```python
@patch(RHUserBlock)
class _RHUserBlock:
    # Adds new method
    def _can_block_user(self):
        return not self.user.merged_into_user
```

Add a new method to the original class by defining it in the patch class. For instance, a `_can_block_user` method is added to `RHUserBlock`.

```python
@patch(RHUserBlock)
class _RHUserBlock:
    # Overrides existing method
    def _process_PUT(self):
        if self._can_block_user():
            raise Forbidden(self.error_message)
        return super()._process_PUT()

    # Overrides existing method
    def _process_DELETE(self):
        if self._can_block_user():
            raise Forbidden(self.error_message)
        return super()._process_PUT()
```

Override an existing method in the original class by defining a method with the same name in the patch class. You can intercept calls to the original method and alter their result with `super()`.

In this example, the PUT and DELETE process methods of the class `RHUserBlock` are intercepted to check if the user can be blocked with the newly added `_can_block_user()`. If not, an exception is raised with `error_message`. Otherwise, the original method is called.

```python
@patch(User)
class _User:
    # Adds new classmethod
    @classmethod
    def get_academic_users(cls):
        return cls.query.filter(cls.title.in_({UserTitle.dr, UserTitle.prof}))

    # Overrides existing staticmethod
    @staticmethod
    def get_system_user():
        system_user = super().get_system_user()
        logger.info('System user was retrieved.')
        return system_user
```

Apply the same logic to add and override `@staticmethod`s and `@classmethod`s.

> [!IMPORTANT]
> Overriding a method in the original class is fragile and can break in future versions of Indico if the original method is changed. A more reliable way to override a method in the original class is to intercept calls via the [`interceptable_function`](https://github.com/indico/indico/blob/v3.2.8/indico/core/signals/plugin.py#L121) signal.

## Add and override properties

```python
@patch(User)
class _User:
    # Adds new property
    @property
    def is_academic(self):
        return self.title in {UserTitle.dr, UserTitle.prof}
```

Add a new property to the original class by defining it in the patch class. Above, a new `is_academic` property is added to the `User` class.

```python
@patch(Identity)
class _Identity:
    # Overrides existing property descriptor method
    @property
    def data(self):
        data = super().data
        data.update({'tag': 'plugin'})
        return data

    # Overrides existing property descriptor method
    @data.setter
    def data(self, value):
        raise RuntimeError('Cannot set data on identity')

    # Adds new property descriptor method
    @data.deleter
    def data(self):
        raise RuntimeError('Cannot delete data on identity')
```

Override a property as well as its setter and deleter descriptor methods by defining them in the patch class. Like within methods, you can access the original property descriptor method from the patch class by using `super()`.

In the example above, the `data` property of `Identity` is overridden to add a new key to the dictionary returned by the original property. The setter and deleter descriptors are also overridden.

> [!NOTE]
> It is not currently possible to call `super()` on the `setter` and `deleter` descriptor methods of properties.
