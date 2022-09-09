
from http import HTTPStatus
from typing import Generator
from marshmallow import ValidationError

from aiohttp.web_response import Response
from aiohttp_apispec import docs, request_schema
from aiomisc import chunk_list

from disk_app.api.schema import ImportSchema
from disk_app.db.schema import items_table
from disk_app.utils.pg import MAX_QUERY_ARGS

from .base import BaseView


class ImportsView(BaseView):
    URL = '/imports'

    MAX_ITEMS_PER_INSERT = MAX_QUERY_ARGS // len(items_table.columns)

    @classmethod
    def make_table_rows(cls, items, date) -> Generator:
        for item in items:
            yield {
                'item_id': item['id'],
                'url': item['url'],
                'size': item['size'],
                'date': date,
                'type': item['type'],
                'parent_id': item['parentId'],
            }
    
    async def validate_items(self, items):
        ids = {item['id']:item['type'] for item in items}

        for item in items:
            if item['parentId']:
                if item['parentId'] in ids:
                    if ids[item['parentId']] != 'FOLDER':
                        raise ValidationError('Validation Failed')
                else:
                    query = items_table.select().where(items_table.c.item_id == item['parentId']).order_by(items_table.c.date.desc())
                    parent = await self.pg.fetchrow(self.get_sql(query))
                    if not parent or parent['type'] != 'FOLDER':
                        raise ValidationError('Validation Failed')

            query = items_table.select().where(items_table.c.item_id == item['id']).order_by(items_table.c.date.desc())
            db_item = await self.pg.fetchrow(self.get_sql(query))
            if db_item and db_item['type'] != item['type']:
                raise ValidationError('Validation Failed')



    @docs(summary='Добавить выгрузку с информацией о файлах и папках')
    @request_schema(ImportSchema())
    async def post(self):
        async with self.pg.acquire() as conn:
            async with conn.transaction():

                items = self.request['data']['items']
                date = self.request['data']['updateDate']

                await self.validate_items(items)

                items_rows = self.make_table_rows(items, date)
                chunked_citizen_rows = chunk_list(items_rows,
                                                self.MAX_ITEMS_PER_INSERT)


                for chunk in chunked_citizen_rows:
                    query = items_table.insert().values(chunk)
                    await conn.execute(self.get_sql(query))

                return Response(status=HTTPStatus.OK)
