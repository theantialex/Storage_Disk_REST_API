import asyncpg
from marshmallow import ValidationError
from pyparsing import And
from .base import BaseView
from disk_app.utils.pg import MAX_QUERY_ARGS
from disk_app.db.schema import items_table
from disk_app.api.schema import ImportSchema

from http import HTTPStatus

from aiohttp.web_response import Response
from aiohttp_apispec import docs, request_schema
from aiomisc import chunk_list
import logging

log = logging.getLogger(__name__)


class ImportsView(BaseView):
    URL = '/imports'

    MAX_ITEMS_PER_INSERT = MAX_QUERY_ARGS // len(items_table.columns)

    @classmethod
    def rename_item_fields(cls, items_dict, date):
        items = {}
        for key, item in items_dict.items():
            if not item['size']:
                item['size'] = 0
            items[key] = {
                'item_id': item['id'],
                'url': item['url'],
                'date': date,
                'type': item['type'],
                'parent_id': item['parentId'],
                'size': item['size']
            }
        return items
    
    async def validate_types(self, items):
        imported_items = {}
        for item in items:
            query = items_table.select().where(items_table.c.item_id == item['id']).order_by(items_table.c.date.desc())
            db_item = await self.pg.fetchrow(self.get_sql(query))

            if db_item and db_item['type'] != item['type']:
                raise ValidationError('Validation Failed')

            # Adding info about previous parent for size calculations
            if db_item:
                item['ex_parent_id'] = db_item['parent_id']
                item['ex_size'] = db_item['size']

            if item['parentId']:
                parent_query = items_table.select().where(items_table.c.item_id == item['parentId']).order_by(items_table.c.date.desc())
                parent = await self.pg.fetchrow(self.get_sql(parent_query))
                
                if (not parent or parent['type'] != 'FOLDER') and \
                    (item['parentId'] not in imported_items or imported_items[item['parentId']]['type'] != 'FOLDER'):
                    raise ValidationError('Validation Failed')

            imported_items[item['id']] = item
        return imported_items

    async def get_ancestors(self, id):
        query = """ WITH RECURSIVE parents AS (
                            (SELECT item_id, url, date, type, size, parent_id
                                FROM items
                                WHERE item_id = $1::varchar ORDER BY date DESC LIMIT 1)
                            UNION
                            (SELECT op.item_id, op.url, op.date, op.type, op.size, op.parent_id
                                FROM items op
                                JOIN parents p ON op.item_id = p.parent_id))
                        SELECT DISTINCT ON (parents.item_id) parents.item_id, parents.url, parents.date, parents.type,
                                parents.size, parents.parent_id
                        FROM parents
                        ORDER BY parents.item_id, parents.date DESC;
                """

        rows = await self.pg.fetch(query, id)
        return rows
    
    @classmethod
    def calculate_folder_sizes(self, items):
        for value in items.values():
            if not value['size']:
                value['size'] = 0
            # Adding previous folder size if already present in db
            if value['type'] == 'FOLDER' and 'ex_parent_id' in value:
                value['size'] += value['ex_size']

            # Adding size to its current ancestors that are present in import
            if value['parentId'] and value['parentId'] in items:
                parent_id = value['parentId']

                while parent_id != None and parent_id in items:
                    if not items[parent_id]['size']:
                        items[parent_id]['size'] = 0

                    items[parent_id]['size'] += value['size']                    
                    parent_id = items[parent_id]['parentId']

            # Substracting size from its previous ancestors that are present in import
            if 'ex_parent_id' in value and value['ex_parent_id'] in items:
                parent_id = value['ex_parent_id']

                while parent_id != None and parent_id in items:
                    if not items[parent_id]['size']:
                        items[parent_id]['size'] = 0

                    items[parent_id]['size'] -= value['ex_size']                   
                    parent_id = items[parent_id]['parentId']

        return items
    
    async def get_ancestor_updates(self, items, date):
        ancestors = {}
        updates = {}
        for key, value in items.items():
            # Substracting item size from its previous parent
            if 'ex_parent_id' in value and value['ex_parent_id'] and value['ex_parent_id'] not in items \
            and (not value['parentId'] or value['ex_parent_id'] != value['parentId']):
                if value['ex_parent_id'] not in updates:
                    updates[value['ex_parent_id']] = -value['ex_size']
                else:
                    updates[value['ex_parent_id']] -= value['ex_size']

            # Adding item size to new parent
            if value['parentId'] and value['parentId'] not in items:
                if 'ex_size' not in value:
                    value['ex_size'] = 0
                if value['parentId'] not in updates:
                    updates[value['parentId']] = value['size'] - value['ex_size']
                else:
                    updates[value['parentId']] += value['size'] - value['ex_size']

        for key, value in updates.items():
            parents = await self.get_ancestors(key)
            if not parents:
                raise ValidationError('Validation Failed')

            for parent in parents:
                parent = dict(parent)
                # If ancestor not in import add to ancestors
                if parent['item_id'] not in ancestors:
                    parent['date'] = date
                    ancestors[parent['item_id']] = parent
                ancestors[parent['item_id']]['size'] += value

        return items, ancestors



    @docs(summary='Добавить выгрузку с информацией о файлах папках')
    @request_schema(ImportSchema())
    async def post(self):
        async with self.pg.acquire() as conn:
            async with conn.transaction():

                items = self.request['data']['items']
                date = self.request['data']['updateDate']

                items_dict = await self.validate_types(items)
                items_dict = self.calculate_folder_sizes(items_dict)
                items_dict, ancestors_dict = await self.get_ancestor_updates(items_dict, date)
                items_dict = self.rename_item_fields(items_dict, date)
    
                chunked_insert_rows = chunk_list(ancestors_dict.values(), self.MAX_ITEMS_PER_INSERT)
                for chunk in chunked_insert_rows:
                    query = items_table.insert().values(chunk)
                    await conn.execute(self.get_sql(query))

                chunked_insert_rows = chunk_list(items_dict.values(), self.MAX_ITEMS_PER_INSERT)
                for chunk in chunked_insert_rows:
                    query = items_table.insert().values(chunk)
                    await conn.execute(self.get_sql(query))

                return Response(status=HTTPStatus.OK)


