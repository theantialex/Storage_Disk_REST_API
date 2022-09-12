from datetime import datetime, timedelta
from http import HTTPStatus

import pytest

from disk_app.utils.testing import (
    get_item, import_data, generate_import_item
)

async def test_get_items(api_client):
    # Файл в subfolder. Subfolder в main_folder. 
    main_folder = generate_import_item(item_id='main_folder', type='FOLDER')
    subfolder = generate_import_item(item_id='subfolder', type='FOLDER', parent_id='main_folder')
    file = generate_import_item(item_id='file', type='FILE', url='/url1', parent_id='subfolder', size=10)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(hours=1), timespec='seconds'))
    await import_data(api_client, [main_folder, subfolder, file], HTTPStatus.OK, updateDate)

    file['children'] = None
    file['date'] = updateDate +'Z'
    subfolder['children'] = [file]
    subfolder['size'] = 10
    subfolder['date'] = updateDate +'Z'
    main_folder['children'] = [subfolder]
    main_folder['size'] = 10
    main_folder['date'] = updateDate +'Z'

    data = await get_item(api_client, main_folder['id'], HTTPStatus.OK)
    assert data == main_folder

    # Новый файл в main_folder. Subfolder не меняется. Размер main_folder меняется.
    new_file = generate_import_item(item_id='file2', type='FILE', url='/url2', parent_id='main_folder', size=1000)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=20), timespec='seconds'))
    await import_data(api_client, [new_file], HTTPStatus.OK, updateDate)

    main_folder['date'] = updateDate +'Z'
    main_folder['size'] = file['size'] + new_file['size']

    data = await get_item(api_client, subfolder['id'], HTTPStatus.OK)
    assert data == subfolder

    new_file['children'] = None
    new_file['date'] = updateDate +'Z'
    main_folder['children'] = [subfolder, new_file]
    main_folder['date'] = updateDate + 'Z'

    data = await get_item(api_client, main_folder['id'], HTTPStatus.OK)
    assert data == main_folder

    # Меняем родителя первому файлу sub_folder -> main_folder. Теперь в subfolder ничего нет.
    file['parentId'] = 'main_folder'
    del file['children']
    del file['date']
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=10), timespec='seconds'))
    await import_data(api_client, [file], HTTPStatus.OK, updateDate)

    file['children'] = None
    file['date'] = updateDate +'Z'
    main_folder['children'] = [new_file, subfolder, file]
    main_folder['date'] = updateDate + 'Z'
    subfolder['size'] = 0
    subfolder['date'] = updateDate +'Z'
    subfolder['children'] = []

    data = await get_item(api_client, main_folder['id'], HTTPStatus.OK)
    assert data == main_folder

    # Удаляем родителя первому файлу. Меняется размер main_folder.
    file['parentId'] = None
    del file['children']
    del file['date']
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=5), timespec='seconds'))
    await import_data(api_client, [file], HTTPStatus.OK, updateDate)

    file['children'] = None
    file['date'] = updateDate +'Z'
    main_folder['children'] = [new_file, subfolder]
    main_folder['size'] = new_file['size']
    main_folder['date'] = updateDate +'Z'

    data = await get_item(api_client, main_folder['id'], HTTPStatus.OK)
    assert data == main_folder
