from datetime import datetime, timedelta
from http import HTTPStatus

import pytest

from disk_app.utils.testing import (
    import_data, generate_import_item, get_history
)

async def test_history(api_client):
    startDate = str(datetime.isoformat(datetime.now()-timedelta(hours=10), timespec='seconds'))
    endDate = str(datetime.isoformat(datetime.now(), timespec='seconds'))

    # Файл в subfolder. Файл в main_folder. Subfolder в main_folder. 
    main_folder = generate_import_item(item_id='main_folder', type='FOLDER')
    subfolder = generate_import_item(item_id='subfolder', type='FOLDER', parent_id='main_folder')
    file = generate_import_item(item_id='file', type='FILE', url='/url1', parent_id='subfolder', size=10)
    new_file = generate_import_item(item_id='file2', type='FILE', url='/url2', parent_id='main_folder', size=1000)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(hours=1), timespec='seconds'))
    await import_data(api_client, [main_folder, subfolder, file, new_file], HTTPStatus.OK, updateDate)

    file['date'] = updateDate +'Z'
    subfolder['size'] = file['size']
    subfolder['date'] = updateDate +'Z'
    main_folder['size'] = file['size'] + new_file['size']
    main_folder['date'] = updateDate +'Z'

    data = await get_history(api_client, main_folder['id'], startDate, endDate, HTTPStatus.OK)
    print(data)
    print({'items': [main_folder]})
    assert data == {'items': [main_folder]}

    # Обновление файла.
    historical_folder = main_folder.copy()

    file['size'] = 1000
    del file['date']
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=30), timespec='seconds'))
    await import_data(api_client, [file], HTTPStatus.OK, updateDate)

    file['date'] = updateDate +'Z'
    subfolder['size'] = file['size']
    subfolder['date'] = updateDate +'Z'
    main_folder['size'] = file['size'] + new_file['size']
    main_folder['date'] = updateDate +'Z'

    data = await get_history(api_client, main_folder['id'], startDate, endDate, HTTPStatus.OK)
    assert data == {'items': [historical_folder, main_folder]}



async def test_history_errors(api_client):
    file = generate_import_item(item_id='file', type='FILE', url='/url1', size=10)
    updateDate = str(datetime.isoformat(datetime.now()-timedelta(hours=1), timespec='seconds'))
    await import_data(api_client, [file], HTTPStatus.OK, updateDate)

    # Дата в будующем
    startDate = str(datetime.isoformat(datetime.now()+timedelta(minutes=5), timespec='seconds'))
    endDate = str(datetime.isoformat(datetime.now()+timedelta(minutes=10), timespec='seconds'))
    await get_history(api_client, file['id'], startDate, endDate, HTTPStatus.BAD_REQUEST)

    # Получение несуществующей item
    endDate = str(datetime.isoformat(datetime.now()-timedelta(minutes=10), timespec='seconds'))
    await get_history(api_client, 'id', updateDate, endDate, HTTPStatus.NOT_FOUND)


