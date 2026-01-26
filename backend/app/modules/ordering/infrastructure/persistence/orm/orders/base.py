"""Shared Base for ordering ORM models."""

from sqlalchemy.ext.declarative import declarative_base

# Shared Base for all ordering models
Base = declarative_base()
