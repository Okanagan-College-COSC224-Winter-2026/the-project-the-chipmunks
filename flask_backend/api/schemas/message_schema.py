from marshmallow import Schema, fields

class MessageSchema(Schema):
    id          = fields.Int(dump_only=True)
    group_id    = fields.Int(attribute="groupID", dump_only=True)
    sender_id   = fields.Int(attribute="senderID", dump_only=True)
    sender_name = fields.Method("get_sender_name")
    content     = fields.Str(required=True)
    created_at  = fields.DateTime(dump_only=True)
    is_read     = fields.Bool(dump_only=True)

    def get_sender_name(self, obj):
        return obj.sender.name if obj.sender else "Unknown"

message_schema  = MessageSchema()
messages_schema = MessageSchema(many=True)