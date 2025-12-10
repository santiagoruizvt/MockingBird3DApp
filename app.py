from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_migrate import Migrate


from config import Config
from models import db, User, Settings, Material, Order

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        action = request.form.get("action", "login")

        # Shared fields
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if action == "register":
            # Registration flow
            confirm = request.form.get("confirm_password", "")

            if not email:
                flash("El email es requerido para registrarse")
                return redirect(url_for("login"))
            if not password or not confirm:
                flash("La contraseña y su confirmación son requeridas")
                return redirect(url_for("login"))
            if password != confirm:
                flash("Las contraseñas no coinciden")
                return redirect(url_for("login"))
            if len(password) < 6:
                flash("La contraseña debe tener al menos 6 caracteres")
                return redirect(url_for("login"))
            # Basic email format check
            if "@" not in email or "." not in email:
                flash("Por favor ingrese un email válido")
                return redirect(url_for("login"))

            if User.query.filter_by(email=email).first():
                flash("Ya existe una cuenta con ese email")
                return redirect(url_for("login"))

            new_user = User(email=email, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("Cuenta creada y sesión iniciada")
            return redirect(url_for("dashboard"))

        else:
            # Login flow
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("dashboard"))
            flash("Credenciales inválidas")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    orders_in_progress = Order.query.filter_by(status="En proceso").all()
    orders_done = Order.query.filter_by(status="Terminado").all()
    return render_template("dashboard.html", in_progress=orders_in_progress, done=orders_done)

@app.route("/orders/new", methods=["GET", "POST"])
@login_required
def new_order():
    materials = Material.query.all()
    if request.method == "POST":
        material = Material.query.get(int(request.form["material_id"]))
        settings = Settings.query.first()
        order = Order(
            name=request.form["name"],
            client=request.form["client"],
            weight_grams=float(request.form["weight"]),
            material_id=material.id,
            print_time_hours=float(request.form["time"]),
            status="En proceso"
        )
        db.session.add(order)
        db.session.commit()
        flash("Pedido agregado correctamente")
        return redirect(url_for("dashboard"))
    return render_template("order_form.html", materials=materials)

@app.route("/materials", methods=["GET", "POST"])
@login_required
def materials():
    if request.method == "POST":
        # Validación lado servidor
        name = request.form.get("name", "").strip()
        price_raw = request.form.get("price", "").strip()

        if not name:
            flash("El nombre del material es requerido")
            return redirect(url_for("materials"))

        if not price_raw:
            flash("El precio por kg es requerido")
            return redirect(url_for("materials"))

        try:
            price = float(price_raw)
            if price < 0:
                flash("El precio debe ser un número mayor o igual a 0")
                return redirect(url_for("materials"))
        except ValueError:
            flash("Precio inválido. Ingrese un número (por ejemplo 12.50).")
            return redirect(url_for("materials"))

        db.session.add(Material(name=name, price_per_kg=price))
        db.session.commit()
        flash("Material agregado")
        return redirect(url_for("materials"))

    return render_template("materials.html", materials=Material.query.all())

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings = Settings.query.first()
    if request.method == "POST":
        settings.electricity_price = float(request.form["electricity_price"])
        settings.printer_power = float(request.form["printer_power"])
        settings.profit_margin = float(request.form["profit_margin"])
        db.session.commit()
        flash("Configuración actualizada")
        return redirect(url_for("settings"))
    return render_template("settings.html", settings=settings)

if __name__ == "__main__":
    with app.app_context():
        # Importar modelos ANTES de crear las tablas
        from models import User, Settings, Material, Order
        
        db.create_all()

        # Crear datos iniciales
        if not User.query.filter_by(email="admin@example.com").first():
            admin = User(
                email="admin@example.com",
                password=generate_password_hash("admin123")
            )
            db.session.add(admin)
        
        if not Settings.query.first():
            db.session.add(Settings(
                electricity_price=0.2,
                printer_power=0.5,
                profit_margin=20
            ))
        
        db.session.commit()

    app.run(debug=True, port=int(os.environ.get("PORT", 5001)))
