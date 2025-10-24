"""
Provides the declarative base class for all SQLAlchemy ORM models.

This file defines a single shared `Base` object that acts as the parent class for
all database models in the application. Any model that inherits from `Base` is
automatically registered in SQLAlchemy's metadata, enabling:

1. Centralized schema management:
   - All table definitions are stored in `Base.metadata`.
   - Schema creation can be handled by calling `Base.metadata.create_all(engine)`.

2. Model discovery:
   - Migrations tools (e.g., Alembic) rely on `Base` to detect and generate
     migration scripts for newly added models.

3. Consistent ORM behavior:
   - Inheriting from `Base` ensures all models have SQLAlchemy ORM capabilities
     such as object-relational mapping and query construction.

This file is intentionally minimal to:
- Avoid circular imports by not referencing any models directly.
- Provide a single source of truth for the ORM base class.

"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Consistent constraint/index names for Alembic diffs
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

class Base(DeclarativeBase):
    metadata = metadata
