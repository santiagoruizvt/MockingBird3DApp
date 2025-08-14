from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    electricity_price = db.Column(db.Float, nullable=False, default=0.0)
    printer_power = db.Column(db.Float, nullable=False, default=0.0)  # kW
    profit_margin = db.Column(db.Float, nullable=False, default=0.0)  # %

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    client = db.Column(db.String(120), nullable=False)
    weight_grams = db.Column(db.Float, nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    print_time_hours = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="En proceso")

    material = db.relationship("Material")

    def calculate_price(self, settings):
        cost_material = (self.weight_grams / 1000) * self.material.price_per_kg
        cost_electricity = (self.print_time_hours * settings.printer_power) * settings.electricity_price
        subtotal = cost_material + cost_electricity
        return round(subtotal * (1 + settings.profit_margin / 100), 2)
