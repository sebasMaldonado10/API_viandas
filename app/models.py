from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

# Modelo de Usuario
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("client", "admin"), nullable=False, default="client")
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# tabla productos para el menu
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

# tabla menu del dia para gestionar los menus diarios
class MenuDay(db.Model):
    __tablename__ = "menu_days"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    is_open = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default= datetime.now)

    # Relacion con MenuItem
    items = db.relationship("MenuItem", backref="menu_day", cascade="all, delete-orphan")
    # Relacion con Order
    orders = db.relationship("Order", back_populates="menu_day")

# tabla menu items que relaciona productos con el menu del dia
class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    menu_day_id = db.Column(db.Integer, db.ForeignKey("menu_days.id"), nullable=False)
    products_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relacion con Product
    product = db.relationship("Product")
    menu_day = db.relationship("MenuDay", back_populates="items")

# Tabla ordenes realizadas por los usuarios
class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    menu_day_id = db.Column(db.Integer, db.ForeignKey("menu_days.id"), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum("CREADO", "EN_PREPARACION", "LISTO", "ENTREGADO"), default="CREADO", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relacion con User
    user = db.relationship("User", backref="orders")
    # Relacion con MenuDay
    menu_day = db.relationship("MenuDay", back_populates="orders")
    # Relacion con OrderItem
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

# Tabla order items que relaciona productos con las ordenes realizadas
class OrderItem(db.Model): 
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relacion con orden
    order = db.relationship("Order", back_populates="items")
    # Relacion con producto
    product = db.relationship("Product")


