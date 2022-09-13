from enum import EnumMeta
from http import HTTPStatus
from random import choice, randint
from typing import Any, Dict, List, Mapping, Optional, Union

import faker
from aiohttp.test_utils import TestClient
from aiohttp.web_urldispatcher import DynamicResource
from datetime import datetime
from disk_app.api.handlers import (
    ImportsView, NodesView, DeleteView, UpdatesView, HistoryView
)

from disk_app.utils.pg import MAX_INTEGER


fake = faker.Faker('ru_RU')


def url_for(path: str, **kwargs) -> str:
    """
    Генерирует URL для динамического aiohttp маршрута с параметрами.
    """
    kwargs = {
        key: str(value)  # Все значения должны быть str (для DynamicResource)
        for key, value in kwargs.items()
    }
    return str(DynamicResource(path).url_for(**kwargs))


def generate_import_item(
        item_id: Optional[str] = None,
        url: Optional[str] = None,
        parent_id: Optional[str] = None,
        type: Optional[str] = None,
        size: Optional[int] = None,
) -> Dict[str, Any]:

    if item_id is None:
        item_id = fake.unique.ssn()

    if type is None:
        type = choice(('FOLDER', 'FILE'))

    if url is None:
        url = fake.url() if type == 'FILE' else None

    if size is None:
        size = randint(1, MAX_INTEGER) if type == 'FILE' else None

    return {
        'id': item_id,
        'url': url,
        'parentId': parent_id,
        'type': type,
        'size': size,
    }


async def import_data(
        client: TestClient,
        items: List[Mapping[str, Any]],
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        updateDate: str = str(datetime.now()),
        **request_kwargs
) -> Optional[int]:
    response = await client.post(
        ImportsView.URL, json={'items': items, 'updateDate': updateDate}, **request_kwargs
    )
    assert response.status == expected_status


async def get_item(
        client: TestClient,
        item_id: str,
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        **request_kwargs
) -> List[dict]:
    response = await client.get(
        url_for(NodesView.URL, id=item_id),
        **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        return data


async def delete_item(
        client: TestClient,
        item_id: str,
        date: str = str(datetime.now()),
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        **request_kwargs
) -> List[dict]:
    response = await client.delete(
        url_for(DeleteView.URL, id=item_id), params={'date': date}, **request_kwargs
    )
    assert response.status == expected_status


async def get_updates(
        client: TestClient,
        date: str = str(datetime.now()),
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        **request_kwargs
) -> List[dict]:
    response = await client.get(
        url_for(UpdatesView.URL), params={'date': date}, **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        return data

async def get_history(
        client: TestClient,
        item_id: str,
        startDate: str,
        endDate: str,
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        **request_kwargs
) -> List[dict]:
    response = await client.get(
        url_for(HistoryView.URL, id=item_id), params={'dateStart': startDate, 'dateEnd': endDate}, **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        return data
