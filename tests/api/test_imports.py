from http import HTTPStatus
from webbrowser import get
import pytest

from disk_app.utils.testing import generate_import_item, import_data, get_item


CASES = (
    # Файлы и папки без родителей
    # Обработчик должен корректно добавлять файлы/папки.
    (
        [
            generate_import_item(),
            generate_import_item(),
            generate_import_item(),
        ],
        HTTPStatus.OK
    ),

    # Файл в папке 1. Папка 1 в папке 2. 
    # Обработчик должен корректно добавлять файл и папки.
    (
        [
            generate_import_item(item_id='folder2', type='FOLDER'),
            generate_import_item(item_id='folder1', type='FOLDER', parent_id='folder2'),
            generate_import_item(item_id='file', type='FILE', parent_id='folder2'),
        ],
        HTTPStatus.OK
    ),

    # Удаление родителя добавленного элемента.
    # Обработчик должен корректно добавлять файл.
    (
        [
            generate_import_item(item_id='file', type='FILE', parent_id=None),
        ],
        HTTPStatus.OK
    ),

    # Пустая выгрузка
    # Обработчик не должен падать на таких данных.
    (
        [],
        HTTPStatus.OK
    ),

    # Родителем файла является файл.
    # Обработчик не должен добавлять такие данные.
    (
        [
            generate_import_item(item_id='file1', type='FILE'),
            generate_import_item(item_id='file', type='FILE', parent_id='file1'),
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # Не существующий родитель.
    # Обработчик не должен добавлять такие данные.
    (
        [
            generate_import_item(item_id='file1', type='FILE'),
            generate_import_item(item_id='file', type='FILE', parent_id='file145'),
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # item_id не уникален в рамках выгрузки
    # Обработчик не должен добавлять такие данные.
    (
        [
            generate_import_item(item_id=1),
            generate_import_item(item_id=1),
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # Папка передается с размером != null
    # Обработчик не должен добавлять такие данные.
    (
        [
            generate_import_item(size=1, type='FOLDER'),
        ],
        HTTPStatus.BAD_REQUEST
    ),

    # Папка передается с url != null
    # Обработчик не должен добавлять такие данные.
    (
        [
            generate_import_item(type='FOLDER', url='/FOLDER'),
        ],
        HTTPStatus.BAD_REQUEST
    ),
)


@pytest.mark.parametrize('items,expected_status', CASES)
async def test_import(api_client, items, expected_status):
    await import_data(api_client, items, expected_status)

