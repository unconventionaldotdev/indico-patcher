# Patching SQLAlchemy models

Indico defines its database schema using [SQLAlchemy](https://www.sqlalchemy.org/) model classes. This page of the guide explains how to patch the SQLAlchemy models defined in Indico. Apply techniques covered in the [Patching Indico classes](./classes.md) page of this guide to add new columns and relationships to existing models or constraints to existing tables.

- [Add new columns and relationships](#add-new-columns-and-relationships)
- [Add and modify hybrid properties](#add-and-modify-hybrid-properties)
- [Add, remove and replace table constraints](#add-remove-and-replace-table-constraints)
- [Generate Alembic migration scripts for patched models](#generate-alembic-migration-scripts-for-patched-models)

## Add new columns and relationships

```python
@patch(User)
class _User:
    # Adds new column and relationship
    credit_card_id = db.Column(db.String, ForeignKey('credit_cards.id'))
    credit_card = db.relationship('CreditCard', backref=backref('user'))
```

Define columns and relationships in the patch model class to have them added to the original model. In this example, a `credit_card_id` column and a `credit_card` relationship are added to the `User` model.

```python
user = User.query.filter_by(id=1).one()
user.credit_card = CreditCard('XXXX-XXXX-XXXX-XXXX')
```

```python
users = User.query.filter(User.credit_card == None).all()
```

You can then use the new column and relationship to insert, update and query rows in the database as if they were defined in the original model class.

> [!IMPORTANT]
> You will still need to apply the changes to the database schema via Alembic migration script. This is [done differently](#generate-alembic-migration-scripts-for-patched-models) for patched models than for Indico-defined and plugin-defined models.

## Add and modify hybrid properties

```python
@patch(Event)
class _Event:
    # Adds a new hybrid property
    @hybrid_property
    def is_in_series(self):
        return self.series_id is not None

    # Adds the expression for the new hybrid property
    @is_in_series.expression
    def is_in_series(self):
        return ~self.series_id.is_(None)
```

Add new hybrid properties to the original model class by defining them in the patch class. In this example, a new `is_in_series` hybrid property is added to the `Event` model.

```python
@patch(Event)
class _Event:
    # Overrides an existing hybrid property
    @hybrid_property
    def event_message(self):
        return ''

    # Overrides the setter for an existing hybrid property
    @event_message.setter
    def event_message(self, value):
        pass

    # Overrides the expression for an existing hybrid property
    @event_message.expression
    def event_message(self):
        return ''
```

You will override existing hybrid properties in the original model class by redefining them in the patch class. This also works for hybrid property setters, deleters and expressions. In this example, the `event_message` hybrid property is overridden to always return an empty string.

## Add, remove and replace table constraints

```python
@patch(RegistrationForm)
class _RegistrationForm:
    RegistrationForm.__table__.append_constraint(
        db.CheckConstraint(...)
    )
```

Add new constraints by calling the `append_constraint()` method of the `__table__` attribute in the original model class.

```python
@patch(RegistrationForm)
class _RegistrationForm:
    RegistrationForm.__table__.constraints -= {
        c for c in RegistrationForm.__table__.constraints
        if c.name == '<constraint_name>'
    }
```

You can also remove constraints by reassigning the `constraints` attribute of the `__table__` attribute in the original model class. In this example, the constraint with name `<constraint_name>` is removed. The easiest way to find the name of the constraint to remove is to inspect the database schema directly (e.g. via `psql` command).

```python
@patch(RegistrationForm)
class _RegistrationForm:
    RegistrationForm.__table__.constraints -= {
        c for c in RegistrationForm.__table__.constraints
        if c.name == '<constraint_name>'
    }
    RegistrationForm.__table__.append_constraint(
        db.CheckConstraint(..., '<constraint_name>')
    )
```

Apply both steps to replace a constraint. In this example, the constraint with name `<constraint_name>` is first removed and a new one with the same name is then added.

> [!IMPORTANT]
> You will still need to apply the changes to the database schema via Alembic migration script. This is [done differently](#generate-alembic-migration-scripts-for-patched-models) for patched models than for Indico-defined and plugin-defined models.

> [!NOTE]
> Patching for modifying table constraints is not necessary, as you are calling `__table__` directly the original model class directly. Altering table constraints on the original form class from a patch class may still be a good idea to keep all modifications in the same code block.

## Generate Alembic migration scripts for patched models

Once new patches are defined in the plugin, generate the Alembic migration script that will record the database schema changes. Since the new columns and table constraints are defined in Indico core model classes, run this command:

```sh
indico db migrate
```

The new Alembic migration script will be placed in the `indico/migrations/versions/` directory of the `indico` package. Now, move the new script to the migrations directory of the plugin, adjust its `down_revision` to point to the latest revision and run the migration script:

```sh
indico db --plugin <plugin-name> upgrade
```
