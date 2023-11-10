# Indico Patcher

The Swiss Army knife for [Indico](https://getindico.io/) plugin development.

Indico plugin development primarily relies on [`flask-pluginengine`](https://github.com/indico/flask-pluginengine), [Jinja](https://github.com/pallets/jinja) template hooks or core [signals](https://github.com/indico/indico/tree/master/indico/core/signals) to extend and modify system functionality. This, however, falls short in many other cases. Indico Patcher offers a clean interface to patch Indico code at runtime, allowing for things such as:

- Adding or overriding properties and intercepting methods in classes
- Reordering, modifying and removing fields in WTForms forms
- Adding new columns and relationships to SQLAlchemy models
- Adding new members to Enums

For more examples and usage information, please refer to the [patching guide](doc/README.md). For general information about Indico plugin development, please refer to the [official guide](https://docs.getindico.io/en/stable/plugins/). Not yet supported cases are tracked in [TODO.md](TODO.md).

## Installation

Indico Patcher is available on PyPI as [`indico-patcher`](https://pypi.org/project/indico-patcher/) and can be installed with `pip`:

```sh
pip install indico-patcher
```

## Usage

Indico Patcher is a library designed to be used by Indico plugins. It provides a `patch` function that can be used as a decorator to patch Indico classes and enums.

```python
from indico_patcher import patch
```

The `@patch` decorator will inject the members defined in the decorated class into a given class or enum. Check below for some examples.

### Examples

Adding a new column and a relationship to an already existing SQLAlchemy model:

```python
@patch(User)
class _User:
    credit_card_id = db.Column(db.String, ForeignKey('credit_cards.id'))
    credit_card = db.relationship('CreditCard', backref=backref('user'))
```

Adding a new field to an already existing WTForms form:

```python
@patch(UserPreferencesForm)
class _UserPreferencesForm:
    credit_card = StringField('Credit Card')

    def validate_credit_card(self, field):
        ...
```

Adding a new member to an already defined Enum:

```python
@patch(UserTitle, padding=100)
class _UserTitle(RichIntEnum):
    __titles__ = [None, 'Madam', 'Sir', 'Rev.']
    madam = 1
    sir = 2
    rev = 3
```

For more examples and usage information, please refer to the [patching guide](doc/README.md).

### Caveats

> [!WARNING]
> With great power comes great responsibility.

Runtime patching is a powerful and flexible strategy but it will lead to code that may break without notice as the Indico project evolves. Indico Patcher makes patching Indico dangerously easy so keep in mind a few things when using it.

1. Think of Indico Patcher as a last resort tool that abuses Indico internal API. Indico developers may change or completely remove the classes and enums that you are patching at any time.
2. If you can achieve the same result with a signal or a template hook, you should probably do that instead. These are considered stable APIs that Indico developers will try to keep backwards compatible or communicate breaking changes.
3. If the signal or hook that you need doesn't exist, consider contributing it to Indico via [pull request](https://github.com/indico/indico/pulls) or asking for it in the [Indico forum](https://talk.getindico.io/) or the official [#indico channel](https://app.element.io/#/room/#indico:matrix.org).

## Development

In order to develop `indico-patcher`, install the project and its dependencies in a virtualenv. This guide assumes that you have the following tools installed and available in your path:

- [`git`](https://git-scm.com/) (available in most systems)
- [`make`](https://www.gnu.org/software/make/) (available in most systems)
- [`poetry`](https://python-poetry.org/) ([installation guide](https://python-poetry.org/docs/#installation))
- [`pyenv`](https://github.com/pyenv/pyenv) ([installation guide](https://github.com/pyenv/pyenv#installation))

First, clone the repository locally with:

```shell
git clone https://github.com/unconventionaldotdev/indico-patcher
cd indico-patcher
```

Before creating the virtualenv, make sure to be using the same version of Python that the development of the project is targeting. This is the first version specified in the `.python-version` file and you can install it with `pyenv`:

```sh
pyenv install
```

You may now create the virtualenv and install the project with its dependencies in it with `poetry`:

```sh
poetry install
```

### Contributing

This project uses GitHub Actions to run the tests and linter on every pull request. You are still encouraged to run the tests and linter locally before pushing your changes.

Run linter checks with:

```sh
poetry run -- make lint
```

Run tests with:

```sh
poetry run -- make test
```
