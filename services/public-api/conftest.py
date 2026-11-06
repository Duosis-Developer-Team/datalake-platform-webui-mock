"""Run from this directory: ``cd services/public-api && python -m pytest tests``.

This directory and the hmdl-api mock (``app`` package, the upstream of /v1/monitoring/*) go
first on sys.path; the repo root's ``app.py`` would otherwise shadow ``app``.
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [_here, os.path.join(os.path.dirname(_here), "hmdl-api")]
