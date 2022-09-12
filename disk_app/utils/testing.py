from enum import EnumMeta
from http import HTTPStatus
from random import choice, randint
from typing import Any, Dict, List, Mapping, Optional, Union

import faker
from aiohttp.test_utils import TestClient
from aiohttp.web_urldispatcher import DynamicResource
from datetime import datetime
from disk_app.api.handlers import (
    ImportsView, NodesView
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
        **request_kwargs
) -> Optional[int]:
    updateDate = str(datetime.now())
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
        return data['data']

"""
async def patch_citizen(
        client: TestClient,
        import_id: int,
        citizen_id: int,
        data: Mapping[str, Any],
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        str_or_url: StrOrURL = CitizenView.URL_PATH,
        **request_kwargs
):
    response = await client.patch(
        url_for(str_or_url, import_id=import_id,
                citizen_id=citizen_id),
        json=data,
        **request_kwargs
    )
    assert response.status == expected_status
    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = PatchCitizenResponseSchema().validate(data)
        assert errors == {}
        return data['data']


async def get_citizens_birthdays(
        client: TestClient,
        import_id: int,
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        **request_kwargs
):
    response = await client.get(
        url_for(CitizenBirthdaysView.URL_PATH, import_id=import_id),
        **request_kwargs
    )
    assert response.status == expected_status
    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = CitizenPresentsResponseSchema().validate(data)
        assert errors == {}
        return data['data']


async def get_citizens_ages(
        client: TestClient,
        import_id: int,
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        **request_kwargs
):
    response = await client.get(
        url_for(TownAgeStatView.URL_PATH, import_id=import_id),
        **request_kwargs
    )
    assert response.status == expected_status
    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = TownAgeStatResponseSchema().validate(data)
        assert errors == {}
        return data['data']
"""