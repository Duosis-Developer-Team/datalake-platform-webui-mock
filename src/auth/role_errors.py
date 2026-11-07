"""Role write errors shared by both client paths (DLP-023).

Mirror of the GUI's ``src/auth/role_errors.py`` so the mock raises the SAME exception class as the
real admin client (callers catch ``RoleNameTaken`` for a taken name, ``ValueError`` for an invalid one).
"""

from __future__ import annotations


class RoleNameTaken(Exception):
    """Another role already uses this name, compared case-insensitively after trimming (K5 / R8)."""
