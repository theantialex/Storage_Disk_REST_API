from datetime import datetime, timedelta
from http import HTTPStatus

import pytest

from disk_app.utils.testing import (
    import_data, generate_import_item, get_updates
)

async def test_updates(api_client):
    # Файл в subfolder. Файл в main_folder. Subfolder в main_folder. 
    main_folder = generate_import_item(item_id='main_folder', type='FOLDER')
    subfolder = generate_import_item(item_id='subfolder', type='FOLDER', parent_id='main_folder')
    file = generate_import_item(item_id='file', type='FILE', url='/url1', parent_id='subfolder', size=10)
    new_file = generate_import_item(item_id='file2', type='FILE', url='/url2', parent_id='main_folder', size=1000)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(hours=1), timespec='seconds'))
    await import_data(api_client, [main_folder, subfolder, file, new_file], HTTPStatus.OK, updateDate)

    file['date'] = updateDate +'Z'
    new_file['date'] = updateDate +'Z'

    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=30), timespec='seconds'))
    data = await get_updates(api_client, updateDate, HTTPStatus.OK)
    assert data == {'items': [file, new_file]}

    # Обновление первого файла.
    file['size'] = 100
    del file['date']

    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=20), timespec='seconds'))
    await import_data(api_client, [file], HTTPStatus.OK, updateDate)

    file['date'] = updateDate +'Z'

    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=5), timespec='seconds'))
    data = await get_updates(api_client, updateDate, HTTPStatus.OK)

    assert data == {'items':[file, new_file]}

    # Получение пустого списка если файл не обновлялись в ту дату.
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(hours=36), timespec='seconds'))
    data = await get_updates(api_client, updateDate, HTTPStatus.OK)

    assert data == {'items':[]}


async def test_updates_errors(api_client):
    # Дата в будующем
    updateDate = str(datetime.isoformat(datetime.now()+timedelta(minutes=5), timespec='seconds'))
    await get_updates(api_client, updateDate, HTTPStatus.BAD_REQUEST)
