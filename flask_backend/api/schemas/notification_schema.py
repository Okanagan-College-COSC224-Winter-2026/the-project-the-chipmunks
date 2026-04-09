from marshmallow import Schema, fields


class NotificationSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    type = fields.Str(dump_only=True)
    title = fields.Str(dump_only=True)
    message = fields.Str(dump_only=True)
    link = fields.Str(dump_only=True)
    is_read = fields.Bool()
    created_at = fields.DateTime(dump_only=True)


notification_schema = NotificationSchema()
notifications_schema = NotificationSchema(many=True)
