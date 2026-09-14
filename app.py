import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "demo-secret"
)


# ============================================================
# BASE DE DATOS
# ============================================================

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )

elif database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )


app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///restaurante.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


# ============================================================
# PRODUCTOS
# ============================================================

PRODUCTS = {
    1: {
        "name": "Sándwich de Milanesa",
        "price": 20.00
    },

    2: {
        "name": "Choripán",
        "price": 18.00
    },
}


# ============================================================
# MODELO PEDIDO
# ============================================================

class Order(db.Model):

    __tablename__ = "orders"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    phone = db.Column(
        db.String(50),
        nullable=False
    )

    address = db.Column(
        db.String(300),
        nullable=True
    )

    payment = db.Column(
        db.String(50),
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    total = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Pendiente"
    )


# ============================================================
# MODELO DETALLE DEL PEDIDO
# ============================================================

class OrderItem(db.Model):

    __tablename__ = "order_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        nullable=False
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    qty = db.Column(
        db.Integer,
        nullable=False
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )


# ============================================================
# CREAR TABLAS
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# FUNCIÓN PARA CONVERTIR PEDIDO A DICCIONARIO
# ============================================================

def order_to_dict(order):

    items = OrderItem.query.filter_by(
        order_id=order.id
    ).all()

    return {

        "id": order.id,

        "created_at": order.created_at.strftime(
            "%d/%m/%Y %H:%M"
        ),

        "name": order.name,

        "phone": order.phone,

        "address": order.address,

        "payment": order.payment,

        "notes": order.notes,

        "total": float(order.total),

        "status": order.status,

        "items": [

            {

                "product_id": item.product_id,

                "name": item.name,

                "qty": item.qty,

                "price": float(item.price),

                "subtotal": float(item.subtotal)

            }

            for item in items

        ]

    }


# ============================================================
# INICIO
# ============================================================

@app.route("/")
def index():

    return render_template(
        "pedido.html",
        products=PRODUCTS
    )


# ============================================================
# CREAR PEDIDO
# ============================================================

@app.post("/pedido")
def crear_pedido():

    name = request.form.get(
        "name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()

    payment = request.form.get(
        "payment",
        ""
    )

    notes = request.form.get(
        "notes",
        ""
    ).strip()


    # --------------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------------

    if not name or not phone:

        flash(
            "El nombre y teléfono son obligatorios."
        )

        return redirect(
            url_for("index")
        )


    # --------------------------------------------------------
    # PRODUCTOS
    # --------------------------------------------------------

    items = []

    total = 0


    for product_id, product in PRODUCTS.items():

        qty_raw = request.form.get(
            f"qty_{product_id}",
            "0"
        )


        try:

            qty = max(
                0,
                int(qty_raw)
            )

        except ValueError:

            qty = 0


        if qty:

            subtotal = (
                qty *
                product["price"]
            )


            items.append({

                "product_id": product_id,

                "name": product["name"],

                "qty": qty,

                "price": product["price"],

                "subtotal": subtotal

            })


            total += subtotal


    # --------------------------------------------------------
    # VALIDAR PRODUCTOS
    # --------------------------------------------------------

    if not items:

        flash(
            "Agrega al menos un producto."
        )

        return redirect(
            url_for("index")
        )


    # --------------------------------------------------------
    # CREAR PEDIDO
    # --------------------------------------------------------

    order = Order(

        name=name,

        phone=phone,

        address=address,

        payment=payment,

        notes=notes,

        total=total,

        status="Pendiente"

    )


    db.session.add(order)

    db.session.flush()


    # --------------------------------------------------------
    # CREAR DETALLE
    # --------------------------------------------------------

    for item in items:

        order_item = OrderItem(

            order_id=order.id,

            product_id=item["product_id"],

            name=item["name"],

            qty=item["qty"],

            price=item["price"],

            subtotal=item["subtotal"]

        )

        db.session.add(order_item)


    # --------------------------------------------------------
    # GUARDAR TODO
    # --------------------------------------------------------

    db.session.commit()


    # --------------------------------------------------------
    # MOSTRAR CONFIRMACIÓN
    # --------------------------------------------------------

    return render_template(

        "confirmacion.html",

        order=order_to_dict(order)

    )


# ============================================================
# LISTAR PEDIDOS
# ============================================================

@app.route("/pedidos")
def pedidos():

    orders_db = Order.query.order_by(
        Order.created_at.desc()
    ).all()


    orders = [

        order_to_dict(order)

        for order in orders_db

    ]


    return render_template(

        "pedidos.html",

        orders=orders

    )


# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
