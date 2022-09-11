from http import HTTPStatus
from aiohttp.web_response import Response
from aiohttp_apispec import docs, response_schema
from .base import BaseView
from disk_app.db.schema import items_table
from aiohttp.web_exceptions import HTTPNotFound
from disk_app.api.schema import ItemSchema
from datetime import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import and_

class NodesView(BaseView):
    URL = r'/nodes/{id}'

    @property
    def id(self):
        return str(self.request.match_info.get('id'))
    
    @classmethod
    def make_item_responce(self, item, children):        
        return {
            'id': item['item_id'],
            'url': item['url'],
            'type': item['type'],
            'parentId': item['parent_id'],
            'date': datetime.isoformat(item['date'], timespec='seconds') + 'Z',
            'size': item['size'],
            'children': children
        }
    
    async def get_children(self, item, relevant_items):
        if item['type'] == 'FILE':
            return None

        query = items_table.select().where(and_(items_table.c.parent_id == item['item_id'], items_table.c.id.in_(relevant_items)))
        rows = await self.pg.fetch(self.get_sql(query, postgresql.dialect()))

        children = []
        for row in rows:
            children.append(self.make_item_responce(row, None))

            if row['type'] == 'FOLDER':
                children[-1]['children'] = await self.get_children(row, relevant_items)

        return children

    @docs(summary='Получить информацию о файле/папке')
    @response_schema(ItemSchema())
    async def get(self):
        query = items_table.select().where(items_table.c.item_id == self.id).order_by(items_table.c.date.desc())

        db_item = await self.pg.fetchrow(self.get_sql(query))
        if not db_item:
            raise HTTPNotFound(text="Item not found")
        
        relevant_items = await self.pg.fetch(self.get_sql(self.get_relevant_ids_query(), postgresql.dialect()))
        relevant_ids = [r[0] for r in relevant_items]

        children = await self.get_children(db_item, relevant_ids)
        item = self.make_item_responce(db_item, children)

        return Response(status=HTTPStatus.OK, body=item)
