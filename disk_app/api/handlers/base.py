from aiohttp.web_urldispatcher import View
from asyncpg import Pool
from disk_app.db.schema import items_table

class BaseView(View):
    URL: str

    @property
    def pg(self) -> Pool:
        return self.request.app['pg']

    @classmethod
    def get_sql(self, query, dialect=None):
        return str(query.compile(compile_kwargs={"literal_binds": True}, dialect=dialect))
    
    @classmethod
    def get_relevant_ids_query(self):
        return items_table.select().distinct(items_table.c.item_id).order_by(items_table.c.item_id, items_table.c.date.desc())
