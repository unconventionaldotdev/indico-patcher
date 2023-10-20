# This file is part of indico-patcher.
# Copyright (C) 2023 UNCONVENTIONAL

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def db_engine():
    return create_engine("sqlite:///:memory:")


@pytest.fixture
def db_base():
    return declarative_base()


@pytest.fixture
def db_session(db_engine, db_base):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    db_base.metadata.create_all(db_engine)
    yield session
    db_base.metadata.drop_all(db_engine)
    session.rollback()
    session.close()
