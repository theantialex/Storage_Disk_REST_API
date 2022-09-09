from http import HTTPStatus
from aiohttp.web_response import Response
from aiohttp_apispec import docs
from .base import BaseView
from disk_app.db.schema import items_table
from aiohttp.web_exceptions import HTTPNotFound
from sqlalchemy import delete
from dateutil import parser
from marshmallow import ValidationError
from datetime import datetime



class DeleteView(BaseView):
    URL = r'/delete/{id}'

    @property
    def id(self):
        return str(self.request.match_info.get('id'))

    async def delete_recursive(self, item):
        print(item)
        query = delete(items_table).where(items_table.c.item_id == item['item_id'])
        await self.pg.execute(self.get_sql(query))

        if item['type'] == 'FOLDER':
            query = items_table.select().where(items_table.c.parent_id == item['item_id']).order_by(items_table.c.date.desc())
            items = await self.pg.fetch(self.get_sql(query))

            for item in items:
                await self.delete_recursive(item)


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
                
                await self.delete_recursive(item)

                return Response(status=HTTPStatus.OK)