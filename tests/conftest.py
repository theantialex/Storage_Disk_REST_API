import asyncio
import os
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy_utils import create_database, drop_database
from yarl import URL

from disk_app.utils.pg import DEFAULT_PG_URL, make_alembic_config


PG_URL = os.getenv('CI_DISK_PG_URL', DEFAULT_PG_URL)

@pytest.yield_fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def postgres():
    """
    Создает временную БД для запуска теста.
    """
    tmp_name = '.'.join([uuid.uuid4().hex, 'pytest'])
    tmp_url = str(URL(PG_URL).with_path(tmp_name))
    create_database(tmp_url)

    try:
        yield tmp_url
    finally:
        drop_database(tmp_url)


@pytest.fixture()
def alembic_config(postgres):
    """
    Создает объект с конфигурацией для alembic, настроенный на временную БД.
    """
    cmd_options = SimpleNamespace(config='alembic.ini', name='alembic',
                                  pg_url=postgres, raiseerr=False, x=None)
    return make_alembic_config(cmd_options)
