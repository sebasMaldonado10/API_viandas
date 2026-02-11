# Aca iran las rutas de la API

from app.views import (
    # AUTH
    UserRegisterView, UserLoginView, MeView,
    
    # MENU
    MenuDayListView, MenuDayDetailView, MenuItemListView, MenuItemDetailView,

    # PRODUCTOS
    ProductListView, ProductDetailView,

    # ORDENES
    OrderListView, OrderDetailView, OrderItemListView, OrderItemDetailView
)

def register_routes(app):
    
    # --- AUT --- #
    app.add_url_rule("/auth/register", view_func= UserRegisterView.as_view("user_register"), methods=["POST"])
    app.add_url_rule("/auth/login", view_func= UserLoginView.as_view("user_login"), methods=["POST"])
    app.add_url_rule("/auth/me", view_func= MeView.as_view("me"), methods=["GET"])

    # --- MENU --- #
    app.add_url_rule("/menu_days", view_func= MenuDayListView.as_view("menu_day_list"), methods=["GET", "POST"])
    app.add_url_rule("/menu_days/<int:id>", view_func= MenuDayDetailView.as_view("menu_day_detail"), methods=["GET", "PUT", "DELETE"])
    app.add_url_rule("/menu_items/<int:menu_day_id>", view_func= MenuItemListView.as_view("menu_item_list"), methods=["GET", "POST"])  
    app.add_url_rule("/menu_items/<int:item_id>", view_func = MenuItemDetailView.as_view("menu_item_detail"), methods=["DELETE"])