# -*- coding: utf-8 -*-
"""Pytest configuration for Memory Compass tests"""
import pytest
import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
