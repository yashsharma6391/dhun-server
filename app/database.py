# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from app.config import settings

# # Create engine
# engine = create_engine(
#     settings.DATABASE_URL,
#     connect_args={"check_same_thread": False}  # needed for SQLite
# )

# # Session factory
# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine
# )

# # Base class for all models
# Base = declarative_base()

# # Dependency - get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from app.config import settings

# # Create engine
# engine = create_engine(
#     settings.DATABASE_URL,
#     connect_args={"check_same_thread": False}  # needed for SQLite
# )

# # Session factory
# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine
# )

# # Base class for all models
# Base = declarative_base()

# # Dependency - get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# database.py - Kept minimal
# All data now in MongoDB
# This file exists only for backward compatibility

class FakeBase:
    """Fake SQLAlchemy Base - does nothing"""
    metadata = type('obj', (object,), {
        'create_all': staticmethod(lambda bind: None)
    })()

Base = FakeBase()

def get_db():
    """No-op - kept for backward compatibility"""
    yield None