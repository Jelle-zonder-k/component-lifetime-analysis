# database/session_factory.py
from sqlalchemy.orm import sessionmaker
# Adjust the import based on your folder structure
from .engine_config import engine

SessionFactory = sessionmaker(bind=engine)
