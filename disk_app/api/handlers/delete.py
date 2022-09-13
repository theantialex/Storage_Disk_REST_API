from http import HTTPStatus
from sqlite3 import connect
from aiohttp.web_response import Response
from aiohttp_apispec import docs
from .base import BaseView
from disk_app.db.schema import items_table
from aiohttp.web_exceptions import HTTPNotFound
from sqlalchemy import delete
from dateutil import parser
from marshmallow import ValidationError
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.dialects import postgresql


class DeleteView(BaseView):
    URL = r'/delete/{id}'

    @property
    def id(self):
        return str(self.request.match_info.get('id'))

    async def update_ancestors(self, conn, item, relevant_items, date):
        parent_id = item['parent_id']
        while parent_id != None:
            query = items_table.select().where(and_(items_table.c.item_id == parent_id, items_table.c.id.in_(relevant_items)))
            parent = await conn.fetchrow(self.get_sql(query))
    
            parent = dict(parent)
            parent['size'] -= item['size']
            parent['date'] = date
            del parent['id']

            query = items_table.insert().values(parent)
            await conn.execute(self.get_sql(query))
            parent_id = parent['parent_id']


    async def delete_recursive(self, conn, item, relevant_items):
        query = delete(items_table).where(items_table.c.item_id == item['item_id'])
        await conn.execute(self.get_sql(query))

        if item['type'] == 'FOLDER':
            query = items_table.select().where(and_(items_table.c.parent_id == item['item_id'], items_table.c.id.in_(relevant_items)))
            items = await conn.fetch(self.get_sql(query))

            for item in items:
                await self.delete_recursive(conn, item, relevant_items)


    docs(summary='Удалить папку или файл')
    async def delete(self):
        async with self.pg.acquire() as conn:
            async with conn.transaction():
                try:
                    date = self.request.rel_url.query.get('date', '')
                    date = parser.isoparse(date)
                    if date.timestamp() > datetime.now().timestamp():
                        raise ValidationError
                except:
                    raise ValidationError('Validation Failed')
                
                query = items_table.select().where(items_table.c.item_id == self.id).order_by(items_table.c.date.desc())
                item = await conn.fetchrow(self.get_sql(query))
                if not item:
                    raise HTTPNotFound(text="Item not found")
                
                relevant_items = await conn.fetch(self.get_sql(self.get_relevant_ids_query(), postgresql.dialect()))
                relevant_ids = [r[0] for r in relevant_items]

                await self.update_ancestors(conn, item, relevant_ids, date)
                await self.delete_recursive(conn, item, relevant_ids)

                return Response(status=HTTPStatus.OK)