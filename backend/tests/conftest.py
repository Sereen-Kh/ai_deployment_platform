# Backend Tests Configuration

import pytest
import asyncio
from typing import AsyncGenerator

# Configure pytest for async tests
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
