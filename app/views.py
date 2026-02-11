# Aca crearemos las vistas

from flask import request, jsonify
from flask.views import MethodView
from marshmallow import ValidationError
from functools import wraps


from flask_jwt_extended import(
    create_access_token,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request,
    get_jwt
)

from . import db
from .models import User, Product, MenuDay, MenuItem, Order, OrderItem
from .schemas import UserSchema, ProductSchema, MenuDaySchema, MenuItemSchema, OrderSchema, OrderItemSchema

# Decorador para verificar el rol del usuario
def role_required(*allowed_roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt() or {}
            user_role = claims.get("role")
            if user_role not in allowed_roles:
                return jsonify({"msg": "No tenes permiso de realizar esta accion"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

class UserRegisterView(MethodView):
    def post(self):
        data = request.get_json() # Obtener datos del request
        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        user_schema = UserSchema() # Validar datos con Marshmallow
        try:
            user_data = user_schema.load(data)
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        # Normalizar campos
        username = user_data.get('username', '').lower() # Convertir a minusculas
        
        if User.query.filter_by(username=username).first(): # Verificar si ya existe el usuario
            return jsonify({"msg": "El nombre de usuario ya existe"}), 400
        
        new_user = User(
            username=username,
            phone=user_data.get('phone'),
            role = user_data.get('role', 'client')
        )

        new_user.set_password(user_data.get('password')) # Hashear la contraseña

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"msg": "Usuario registrado exitosamente"}), 201

class UserLoginView(MethodView):
    def post(self):
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        username = data.get('username', '').lower()
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"msg": "Usuario y contraseña requeridos"}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({"msg": "Credenciales invalidas"}), 401
        
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=user.id, additional_claims=additional_claims)

        return jsonify(access_token=access_token), 200
    
class MeView(MethodView):
    @jwt_required()
    def get(self):
        uid = int(get_jwt_identity())
        u = User.query.get(uid)
        if not u:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        user_schema = UserSchema()
        result = user_schema.dump(u)
        return jsonify(result), 200

# Vistas para menu y productos se implementaran luego

class MenuDayListView(MethodView):
    def get(self):
        # Listar todos los menus del dia
        menu_days = MenuDay.query.all()
        menu_day_schema = MenuDaySchema(many=True)
        result = menu_day_schema.dump(menu_days) # Serializar resultados
        return jsonify(result), 200
    
    @role_required("admin")
    # Crear un nuevo menu del dia
    def post(self):
        data = request.get_json() # Obtener datos del request
        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        menu_day_schema = MenuDaySchema() # Validar datos con Marshmallow
        try:
            menu_day_data = menu_day_schema.load(data) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        if MenuDay.query.filter_by(date=menu_day_data["date"]).first():
            return jsonify({"msg": "Ya existe un menú para esa fecha"}), 400
                
        new_menu_day = MenuDay(
            date = menu_day_data.get('date'),
            is_open = menu_day_data.get('is_open', True)
        )

        db.session.add(new_menu_day)
        db.session.commit()

        return jsonify({"msg": "Menu del día creado exitosamente"}), 201
    
class MenuDayDetailView(MethodView):
    def get(self, menu_day_id):
        # Obtener detalles del menu del dia
        menu_day = MenuDay.query.get(menu_day_id)
        if not menu_day:
            return jsonify({"msg": "Menu del día no encontrado"}), 404
        
        menu_day_schema = MenuDaySchema() # Validar datos con Marshmallow
        result = menu_day_schema.dump(menu_day) # Serializar resultados
        return jsonify(result), 200
    
    @role_required("admin")
    def put(self, menu_day_id): # Actualizar
        menu = MenuDay.query.get(menu_day_id)
        if not menu:
            return jsonify({"msg": "Menu del día no encontrado"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Datos invalidos"}), 400

        menu_day_schema = MenuDaySchema() # Validamos los datos

        try:
            menu_day_data = menu_day_schema.load(data, partial=True) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        menu.is_open = menu_day_data.get('is_open', menu.is_open)

        db.session.commit()
        return jsonify({"msg": "Menu del día actualizado exitosamente"}), 200
    
    @role_required("admin")
    def delete(self, menu_day_id): # Eliminar
        menu = MenuDay.query.get(menu_day_id)
        if not menu:
            return jsonify({"msg": "Menu del día no encontrado"}), 404
        
        db.session.delete(menu)
        db.session.commit()
        return jsonify({"msg": "Menu eliminado exitosamente"}), 200
    
class MenuItemListView(MethodView):
    def get(self, menu_day_id): # Listar items de un menu del dia
        menu_day = MenuDay.query.get(menu_day_id)
        if not menu_day:
            return jsonify({"msg": "Menu del día no encontrado"}), 404
        
        items = MenuItem.query.filter_by(menu_day_id=menu_day_id).all()
        menu_item_schema = MenuItemSchema(many=True) # Validar datos con Marshmallow
        result = menu_item_schema.dump(items) # Serializar resultados
        return jsonify(result), 200
    
    @role_required("admin")
    def post(self, menu_day_id): # Agregar item a un menu del dia
        menu_day = MenuDay.query.get(menu_day_id)
        if not menu_day:
            return jsonify({"msg": "Menu del día no encontrado"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        menu_item_schema = MenuItemSchema()
        try:
            menu_item_data = menu_item_schema.load(data) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        product = Product.query.get(menu_item_data.get('products_id'))
        if not product:
            return jsonify({"msg": "Producto no encontrado"}), 404
        
        # Validar duplicado
        existing = MenuItem.query.filter_by(
            menu_day_id=menu_day_id,
            products_id=menu_item_data.get('products_id')
        ).first()
        if existing:
            return jsonify({"msg": "Este producto ya está en el menú"}), 400
        
        new_item = MenuItem(
            menu_day_id=menu_day_id,
            products_id=menu_item_data.get('products_id')
        )

        db.session.add(new_item)
        db.session.commit()
        return jsonify(menu_item_schema.dump(new_item)), 201
    
    
class MenuItemDetailView(MethodView):
    @role_required("admin")
    def delete(self, item_id):
        """Eliminar item específico del menú"""
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({"msg": "Item no encontrado"}), 404
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({"msg": "Item eliminado del menú exitosamente"}), 200
    
# Vistas de los productos

class ProductListView(MethodView):
    def get(self):
        # Listar todos los productos
        product = Product.query.all()
        product_schema = ProductSchema(many=True)
        result = product_schema.dump(product) # Serializar resultados
        return jsonify(result), 200
    
    @role_required("admin")
    def post(self):
        data = request.get_json() # Obtener los datos del request

        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        product_schema = ProductSchema() # Validar datos con Marshmallow
        try:
            product_data = product_schema.load(data) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        new_product = Product(
            name = product_data.get('name'),
            description = product_data.get('description'),
            price = product_data.get('price'),
            active = product_data.get('active', True),
            image_url = product_data.get('image_url')
        )

        db.session.add(new_product)
        db.session.commit()
        return jsonify(product_schema.dump(new_product)), 201
    
class ProductDetailView(MethodView):
    def get(self, product_id):
        # Obtener detalles de un producto
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"msg": "Producto no encontrado"}), 404
        
        product_schema = ProductSchema()
        result = product_schema.dump(product) # Serializar resultados
        return jsonify(result), 200
    
    @role_required("admin")
    def put(self, product_id):
        product = Product.query.get(product_id) # Obtener el producto a actualizar
        if not product:
            return jsonify({"msg": "Producto no encontrado"}), 404
        
        data = request.get_json() # Obtener los datos del request
        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        product_schema = ProductSchema() # Validar datos con Marshmallow
        try:
            product_data = product_schema.load(data, partial=True) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        # Actualizar campos del producto
        product.name = product_data.get('name', product.name)
        product.description = product_data.get('description', product.description)
        product.price = product_data.get('price', product.price)
        product.active = product_data.get('active', product.active)
        product.image_url = product_data.get('image_url', product.image_url)

        db.session.commit()
        return jsonify(product_schema.dump(product)), 200
    
    @role_required("admin")
    def delete(self, product_id):
        product = Product.query.get(product_id) # Obtener el producto a eliminar

        if not product:
            return jsonify({"msg": "Producto no encontrado"}), 404
        
        db.session.delete(product)
        db.session.commit()
        return jsonify({"msg": "Producto eliminado exitosamente"}), 200
    
# Vistas para ordenes se implementaran luego

class OrderListView(MethodView):
    # ✅ Correcto: clients ven sus ordenes, admins ven todas
    @jwt_required()
    def get(self):
        uid = int(get_jwt_identity())
        user = User.query.get(uid)
        
        if user.role == "admin":
            orders = Order.query.all()
        else:
            orders = Order.query.filter_by(user_id=uid).all()
        
        order_schema = OrderSchema(many=True)
        result = order_schema.dump(orders)
        return jsonify(result), 200
    
    @jwt_required()
    # Para crear una orden (solo clientes)
    def post(self):
        uid = int(get_jwt_identity()) # Obtener el ID del usuario desde el token JWT
        user = User.query.get(uid) # Obtenemos el usuario

        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        data = request.get_json() # Obtener los datos del request
        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        order_schema = OrderSchema() # Validar datos con Marshmallow
        try:
            order_data = order_schema.load(data, partial=True) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        # Verificar que el menu del dia exista y este abierto
        menu_day = MenuDay.query.get(order_data.get('menu_day_id'))
        if not menu_day or not menu_day.is_open:
            return jsonify({"msg": "Menu del dia no disponible"}), 400
        
        new_order = Order(
            user_id = uid,
            menu_day_id = order_data.get('menu_day_id'),
            total_price = 0, # Se calculara luego
            status = "CREADO"
        )

        db.session.add(new_order)
        db.session.commit()
        return jsonify(order_schema.dump(new_order)), 201
    
class OrderDetailView(MethodView):
    # Para obtener los detalles de una orden
    @jwt_required()
    def get(self, order_id):
        uid = int(get_jwt_identity()) # Obtener el ID del usuario
        user = User.query.get(uid) # Obtener el usuario

        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        order = Order.query.get(order_id) # Obtener la orden
        if not order:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        # Verificar que el usuario sea el dueño de la orden o un admin
        if order.user_id != uid and user.role != "admin":
            return jsonify({"msg": "No tienes permiso para ver esta orden"}), 403
        
        order_schema = OrderSchema() # Validar datos con Marshmallow
        result = order_schema.dump(order) # Serializar resultados
        return jsonify(result), 200 # Retornar la orden
    
    @role_required("admin")
    def put(self, order_id):
        # Solo admins
        order = Order.query.get(order_id) # Obtener la orden
        if not order:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        data = request.get_json() # Obtener los datos del request
        if not data:
            return jsonify({"msg": "Datos inválidos"}), 400
        
        order_schema = OrderSchema()
        try:
            order_data = order_schema.load(data, partial=True) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        # Actualizar el estado de la orden
        order.status = order_data.get('status', order.status)
        valid_statuses = ["CREADO", "EN_PREPARACION", "LISTO", "ENTREGADO", "CANCELADO"]
        if order.status not in valid_statuses:
            return jsonify({"msg": "Estado de orden no válido"}), 400
        db.session.commit()
        return jsonify(order_schema.dump(order)), 200 # Retornar la orden actualizada
    
    @role_required("admin")
    def delete(self, order_id):
        order = Order.query.get(order_id) # Obtener la orden
        if not order:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        db.session.delete(order)
        db.session.commit()
        return jsonify({"msg": "Orden eliminada exitosamente"}), 200

# Vistas para items de orden se implementaran luego

class OrderItemListView(MethodView):
    @jwt_required()
    # Obtener los items de una orden (clientes solo pueden ver sus ordenes, admins pueden ver todas)
    def get(self, order_id):
        uid = int(get_jwt_identity())
        user = User.query.get(uid)

        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        order = Order.query.get(order_id)

        if not order:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        if order.user_id != uid and user.role != "admin":
            return jsonify({"msg": "No tienes permiso para ver los items de esta orden"}), 403
        
        items = OrderItem.query.filter_by(order_id=order_id).all()
        order_item_schema = OrderItemSchema(many=True)
        result = order_item_schema.dump(items)
        return jsonify(result), 200
    
    @jwt_required()
    # Agregar item a una orden (solo clientes pueden agregar a sus ordenes, admins pueden agregar a cualquier orden)
    def post(self, order_id):
        uid = int(get_jwt_identity())
        user = User.query.get(uid)

        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        order = Order.query.get(order_id)

        if not order:
            return jsonify({"msg": "Orden no encontrada"}), 404
        
        if order.user_id != uid and user.role != "admin":
            return jsonify({"msg": "No tienes permiso para agregar items a esta orden"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Datos invalidos"}), 400
        
        order_item_schema = OrderItemSchema()
        try:
            order_item_data = order_item_schema.load(data) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        # Verificar que el producto exista
        product = Product.query.get(order_item_data.get('product_id'))
        if not product:
            return jsonify({"msg": "Producto no encontrado"}), 404
        if not product.active:
            return jsonify({"msg": "Producto no disponible"}), 400
        
        # Verificar que el producto esté en el menú del día de la orden
        menu_item = MenuItem.query.filter_by(
            menu_day_id=order.menu_day_id,
            products_id=order_item_data.get('product_id')
        ).first()
        if not menu_item:
            return jsonify({"msg": "Este producto no está en el menú del día de la orden"}), 400
        # Crear el nuevo item de orden

        new_item = OrderItem(
            order_id = order_id,
            product_id = order_item_data.get('product_id'),
            quantity = order_item_data.get('quantity'),
            price = product.price * order_item_data.get('quantity') # Calcular el precio total del item
        )
        
        db.session.add(new_item)
        db.session.flush()  # Guardar el item antes de recalcular
        
        # Recalcular y guardar el total de la orden
        order.calculate_total_price()
        db.session.commit()
        return jsonify(order_item_schema.dump(new_item)), 201
    
class OrderItemDetailView(MethodView):
    @jwt_required()
    def delete(self, item_id):
        uid = int(get_jwt_identity())
        user = User.query.get(uid)

        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        item = OrderItem.query.get(item_id)

        if not item:
            return jsonify({"msg": "Item no encontrado"}), 404
        
        order = Order.query.get(item.order_id)

        if order.user_id != uid and user.role != "admin":
            return jsonify({"msg": "No tienes permiso para eliminar este item"}), 403
        
        db.session.delete(item)
        db.session.flush()  # Eliminar el item antes de recalcular
        
        # Recalcular y guardar el total de la orden
        order.calculate_total_price()
        db.session.commit()
        return jsonify({"msg": "Item eliminado exitosamente"}), 200
    
    @jwt_required()
    def put(self, item_id):
        uid = int(get_jwt_identity())
        user = User.query.get(uid)

        if not user:
            return jsonify({"msg": "Usuario no encontrado"}), 404
        
        item = OrderItem.query.get(item_id)

        if not item:
            return jsonify({"msg": "Item no encontrado"}), 404
        
        order = Order.query.get(item.order_id)

        if order.user_id != uid and user.role != "admin":
            return jsonify({"msg": "No tienes permiso para modificar este item"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Datos invalidos"}), 400
        
        order_item_schema = OrderItemSchema()
        try:
            order_item_data = order_item_schema.load(data, partial=True) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        # Verificar que el producto exista
        product = Product.query.get(order_item_data.get('product_id', item.product_id))
        if not product:
            return jsonify({"msg": "Producto no encontrado"}), 404
        if not product.active:
            return jsonify({"msg": "Producto no disponible"}), 400
        
        # Verificar que el producto esté en el menú del día de la orden
        menu_item = MenuItem.query.filter_by(
            menu_day_id=order.menu_day_id,
            products_id=order_item_data.get('product_id', item.product_id)
        ).first()
        if not menu_item:
            return jsonify({"msg": "Este producto no está en el menú del día de la orden"}), 400
        
        # Actualizar campos del item de orden
        item.product_id = order_item_data.get('product_id', item.product_id)
        item.quantity = order_item_data.get('quantity', item.quantity)
        item.price = product.price * item.quantity # Recalcular el precio total del item

        db.session.flush()  # Guardar cambios del item antes de recalcular
        
        # Recalcular y guardar el total de la orden
        order.calculate_total_price()
        db.session.commit()
        return jsonify(order_item_schema.dump(item)), 200
    
# fin de las vistas
    

    
























