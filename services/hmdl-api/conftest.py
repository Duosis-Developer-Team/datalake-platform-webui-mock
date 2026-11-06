"""Run from this directory: ``cd services/hmdl-api && python -m pytest tests``.

The repo root has an ``app.py`` (the Dash app); this directory goes first on sys.path so
``app`` is the hmdl-api mock package here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
