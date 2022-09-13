from datetime import datetime, timedelta
from http import HTTPStatus

import pytest

from disk_app.utils.testing import (
    delete_item, get_item, import_data, generate_import_item, delete_item
)

async def test_delete_items(api_client):
    # Файл в subfolder. Subfolder в main_folder. Удаление файла - папка subfolder пустая. Размеры папок поменялись.
    main_folder = generate_import_item(item_id='main_folder', type='FOLDER')
    subfolder = generate_import_item(item_id='subfolder', type='FOLDER', parent_id='main_folder')
    file = generate_import_item(item_id='file', type='FILE', url='/url1', parent_id='subfolder', size=10)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(hours=1), timespec='seconds'))


    await import_data(api_client, [main_folder, subfolder, file], HTTPStatus.OK, updateDate)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=20), timespec='seconds'))
    await delete_item(api_client, file['id'], updateDate, HTTPStatus.OK)

    await get_item(api_client, file['id'], HTTPStatus.NOT_FOUND)
    data = await get_item(api_client, main_folder['id'], HTTPStatus.OK)

    subfolder['date'] = updateDate +'Z'
    subfolder['size'] = 0
    subfolder['children'] = []
    main_folder['date'] = updateDate +'Z'
    main_folder['size'] = 0
    main_folder['children'] = [subfolder]

    assert data == main_folder

    # Новый файл в subfolder. Удаление main_folder - удаление всего.
    new_file = generate_import_item(item_id='file2', type='FILE', url='/url2', parent_id='subfolder', size=1000)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=10), timespec='seconds'))

    await import_data(api_client, [new_file], HTTPStatus.OK, updateDate)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=5), timespec='seconds'))
    await delete_item(api_client, main_folder['id'], updateDate, HTTPStatus.OK)

    await get_item(api_client, new_file['id'], HTTPStatus.NOT_FOUND)
    await get_item(api_client, subfolder['id'], HTTPStatus.NOT_FOUND)
    await get_item(api_client, main_folder['id'], HTTPStatus.NOT_FOUND)


async def test_delete_item_errors(api_client):
    # Удаление несуществующей item
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=5), timespec='seconds'))
    await delete_item(api_client, 'id', updateDate, HTTPStatus.NOT_FOUND)

    # Дата в будующем
    updateDate = str(datetime.isoformat(datetime.now()+timedelta(minutes=5), timespec='seconds'))
    await delete_item(api_client, 'id', updateDate, HTTPStatus.BAD_REQUEST)
