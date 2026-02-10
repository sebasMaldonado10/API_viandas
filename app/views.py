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
            role=user_data.get('role', 'client')
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
        result.pop("password_hash", None) # Eliminar el hash de la contraseña del resultado
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
    
    @role_required("admin")
    def delete(self, menu_day_id): # Eliminar item de un menu del dia
        menu_day = MenuDay.query.get(menu_day_id)

        if not menu_day:
            return jsonify({"msg": "Menu del día no encontrado"}), 404
        
        data = request.get_json()

        if not data:
            return jsonify({"msg": "Datos invalidos"}), 400
        
        menu_itmem_schema = MenuItemSchema()
        try:
            menu_item_data = menu_itmem_schema.load(data) # Validar datos con Marshmallow
        except ValidationError as err:
            return jsonify(err.messages), 400
        
        item = MenuItem.query.filter_by(menu_day_id=menu_day_id, products_id=menu_item_data.get('products_id')).first()
        if not item:
            return jsonify({"msg": "Item no encontrado en el menú del día"}), 404
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({"msg": "Item eliminado del menú del día exitosamente"}), 200

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









