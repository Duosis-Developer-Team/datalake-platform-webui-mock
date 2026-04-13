"""Pytest / test defaults so DatabaseService can initialize a pool when patched."""

import os

# Required for src.services.db_service.DatabaseService.__init__ when not fully mocked.
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PASS", "test-secret")

# Avoid live auth DB during unit tests; middleware impersonates admin when DB is unreachable.
os.environ.setdefault("AUTH_DISABLED", "true")
os.environ.setdefault("APP_MODE", "mock")
