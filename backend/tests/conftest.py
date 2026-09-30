import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.models import Base
from app.core.database import get_db
from app.services.seed_service import seed_database_from_csv
from app.services.fixture_generator import generate_all_scenario_fixtures

# In-memory SQLite with StaticPool so all threads share the exact same database
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestingSessionLocal()
    try:
        seed_database_from_csv(db)
        generate_all_scenario_fixtures()
    finally:
        db.close()
    
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="session")
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
