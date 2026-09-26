from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = None
SessionLocal = None

if settings.persistence_backend == "postgres" and settings.database_url:
    engine = create_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    if not SessionLocal:
        raise Exception("Database is not configured or persistence_backend is not 'postgres'")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
