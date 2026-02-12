from marshmallow import Schema, fields, validate

# Esquemas de validación y serialización con Marshmallow
# Sirven para validar los datos de entrada y formatear los datos de salida en las respuestas JSON
class UserSchema(Schema):

    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    role = fields.Str(validate=validate.OneOf(["client", "admin"]), load_default="client")
    phone = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

class ProductSchema(Schema):

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    price = fields.Float(required=True)
    active = fields.Bool(load_default=True)
    image_url = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

class MenuDaySchema(Schema):

    id = fields.Int(dump_only=True)
    date = fields.Date(required=True)
    is_open = fields.Bool(load_default=True)
    created_at = fields.DateTime(dump_only=True)

class MenuItemSchema(Schema):

    id = fields.Int(dump_only=True)
    menu_day_id = fields.Int(required=True)
    products_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)

class OrderSchema(Schema):

    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    menu_day_id = fields.Int(required=True)
    total_price = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class OrderItemSchema(Schema):

    id = fields.Int(dump_only=True)
    order_id = fields.Int(required=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    price = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

