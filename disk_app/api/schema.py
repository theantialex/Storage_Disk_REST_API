from datetime import datetime
from email.policy import default

from marshmallow import Schema, ValidationError, validates, validates_schema
from marshmallow.fields import DateTime, Int, Nested, Str
from marshmallow.validate import Length, OneOf, Range

from disk_app.db.schema import ItemType

class ItemImportSchema(Schema):
    id = Str(validate=Length(min=1, max=256), required=True)
    url = Str(allow_none=True, validate=Length(min=1, max=255), missing=None)
    parentId = Str(allow_none=True, validate=Length(min=1, max=256), missing=None)
    size = Int(allow_none=True, validate=Range(min=0), strict=True, missing=None)
    type = Str(validate=OneOf([type.value for type in ItemType]), required=True)


class ImportSchema(Schema):
    items = Nested(ItemImportSchema, many=True, required=True)
    updateDate = DateTime(required=True)

    @validates('updateDate')
    def validate_update_date(self, value: datetime):
        if value.timestamp() > datetime.now().timestamp():
            raise ValidationError("Update date can't be in the future")

    @validates_schema
    def validate_items(self, data, **_):
        item_ids = set()
        for item in data['items']:
            if item['id'] in item_ids:
                raise ValidationError(
                    'item id %r is not unique' % item['id']
                )
            if item['parentId'] == item['id']:
                raise ValidationError(
                    'parent id {} cannot be the same as item id {}'.format(item['parentId'], item['id'])
                )
            if  not item['size'] and item['type'] != 'FOLDER':
                raise ValidationError(
                    'file size cannot be null'
                )
            if item['type'] == 'FOLDER' and (item['size'] or item['url']):
                raise ValidationError(
                    'folder size and url must be null'
                )
            item_ids.add(item['id'])
