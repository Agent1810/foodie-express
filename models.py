from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    role        = db.Column(db.String(20), default="customer")  # customer / owner / admin
    phone       = db.Column(db.String(20))
    address     = db.Column(db.String(300))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    orders      = db.relationship("Order", backref="customer", lazy=True, foreign_keys="Order.user_id")

class Restaurant(db.Model):
    __tablename__ = "restaurants"
    id            = db.Column(db.Integer, primary_key=True)
    owner_id      = db.Column(db.Integer, db.ForeignKey("users.id"))
    name          = db.Column(db.String(100), nullable=False)
    cuisine       = db.Column(db.String(50))
    description   = db.Column(db.String(300))
    address       = db.Column(db.String(300))
    city          = db.Column(db.String(100))
    phone         = db.Column(db.String(20))
    image_emoji   = db.Column(db.String(10), default="🍽️")
    rating        = db.Column(db.Float, default=4.0)
    delivery_time = db.Column(db.String(30), default="30-40 min")
    min_order     = db.Column(db.Integer, default=100)
    is_open       = db.Column(db.Boolean, default=True)
    lat           = db.Column(db.Float, default=12.9716)
    lng           = db.Column(db.Float, default=77.5946)
    menu_items    = db.relationship("MenuItem", backref="restaurant", lazy=True)
    orders        = db.relationship("Order", backref="restaurant", lazy=True)

class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id           = db.Column(db.Integer, primary_key=True)
    restaurant_id= db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    name         = db.Column(db.String(100), nullable=False)
    description  = db.Column(db.String(200))
    category     = db.Column(db.String(50))
    price        = db.Column(db.Float, nullable=False)
    emoji        = db.Column(db.String(10), default="🍽️")
    is_available = db.Column(db.Boolean, default=True)

class Order(db.Model):
    __tablename__ = "orders"
    id             = db.Column(db.Integer, primary_key=True)
    order_code     = db.Column(db.String(20), unique=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    restaurant_id  = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    items_json     = db.Column(db.Text)  # JSON string
    subtotal       = db.Column(db.Float, default=0)
    discount       = db.Column(db.Float, default=0)
    total          = db.Column(db.Float, default=0)
    status         = db.Column(db.String(30), default="Confirmed")
    delivery_agent = db.Column(db.String(100))
    address        = db.Column(db.String(300))
    coupon_used    = db.Column(db.String(20))
    agent_lat      = db.Column(db.Float)
    agent_lng      = db.Column(db.Float)
    placed_at      = db.Column(db.DateTime, default=datetime.utcnow)
    ratings        = db.relationship("Rating", backref="order", lazy=True)

class Rating(db.Model):
    __tablename__ = "ratings"
    id              = db.Column(db.Integer, primary_key=True)
    order_id        = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    restaurant_id   = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    food_rating     = db.Column(db.Integer)
    delivery_rating = db.Column(db.Integer)
    review          = db.Column(db.String(500))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

class Coupon(db.Model):
    __tablename__ = "coupons"
    id               = db.Column(db.Integer, primary_key=True)
    code             = db.Column(db.String(20), unique=True, nullable=False)
    discount_percent = db.Column(db.Float, default=0)
    flat_discount    = db.Column(db.Float, default=0)
    min_order        = db.Column(db.Float, default=0)
    max_uses         = db.Column(db.Integer, default=100)
    used_count       = db.Column(db.Integer, default=0)
    is_active        = db.Column(db.Boolean, default=True)
    description      = db.Column(db.String(200))
