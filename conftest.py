import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_session
from main import app
from models import Base, Penguin

TEST_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:motdepasse@localhost:5432/penguins_test",
)

engine_test = create_engine(TEST_URL)
SessionTest = sessionmaker(bind=engine_test, expire_on_commit=False)


@pytest.fixture
def session():
    Base.metadata.create_all(engine_test)
    with SessionTest() as s:
        yield s
    Base.metadata.drop_all(engine_test)


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def pingouin(session):
    p = Penguin(
        species="Adelie",
        island="Torgersen",
        bill_length_mm=39.1,
        bill_depth_mm=18.7,
        flipper_length_mm=181.0,
        body_mass_g=3750.0,
        sex="male",
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    return p