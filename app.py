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


app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url or
    "sqlite:///restaurante.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


# ============================================================
# ESTADOS DE PEDIDOS
# ============================================================

ORDER_STATUSES = {

    "Pendiente": {
        "label": "Pendiente",
        "next": "En preparación"
    },

    "En preparación": {
        "label": "En preparación",
        "next": "Listo"
    },

    "Listo": {
        "label": "Listo",
        "next": "Enviado"
    },

    "Enviado": {
        "label": "Enviado",
        "next": "Entregado"
    },

    "Entregado": {
        "label": "Entregado",
        "next": None
    },

    "Cancelado": {
        "label": "Cancelado",
        "next": None
    }

}


# ============================================================
# MODELO PRODUCTO
# ============================================================

class Product(db.Model):

    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )


# ============================================================
# MODELO INGREDIENTE
# ============================================================

class Ingredient(db.Model):

    __tablename__ = "ingredients"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    unit = db.Column(
        db.String(30),
        nullable=False
    )

    stock = db.Column(
        db.Numeric(12, 3),
        nullable=False,
        default=0
    )

    minimum_stock = db.Column(
        db.Numeric(12, 3),
        nullable=False,
        default=0
    )

    cost = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

class ProductIngredient(db.Model):
    __tablename__ = "product_ingredients"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredients.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Numeric(12, 3),
        nullable=False,
        default=0
    )

    product = db.relationship(
        "Product",
        backref=db.backref(
            "recipe_items",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    ingredient = db.relationship(
        "Ingredient",
        backref=db.backref(
            "recipe_items",
            lazy=True
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "product_id",
            "ingredient_id",
            name="uq_product_ingredient"
        ),
    )
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
# MODELO DETALLE PEDIDO
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
# PRODUCTOS INICIALES
# ============================================================

def inicializar_productos():

    productos_iniciales = [

        {
            "id": 1,
            "name": "Sándwich de Milanesa",
            "price": 20.00
        },

        {
            "id": 2,
            "name": "Choripán",
            "price": 18.00
        }

    ]


    for data in productos_iniciales:

        product = db.session.get(
            Product,
            data["id"]
        )


        if not product:

            product = Product(

                id=data["id"],

                name=data["name"],

                price=data["price"],

                active=True

            )

            db.session.add(product)


    db.session.commit()


with app.app_context():

    inicializar_productos()


# ============================================================
# CONVERTIR PEDIDO A DICCIONARIO
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

    products = Product.query.filter_by(
        active=True
    ).order_by(
        Product.id
    ).all()


    return render_template(

        "pedido.html",

        products=products

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


    if not name or not phone:

        flash(
            "El nombre y teléfono son obligatorios."
        )

        return redirect(
            url_for("index")
        )


    products = Product.query.filter_by(
        active=True
    ).all()


    items = []

    total = 0


    for product in products:

        qty_raw = request.form.get(
            f"qty_{product.id}",
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

            price = float(product.price)

            subtotal = qty * price


            items.append({

                "product_id": product.id,

                "name": product.name,

                "qty": qty,

                "price": price,

                "subtotal": subtotal

            })


            total += subtotal


    if not items:

        flash(
            "Agrega al menos un producto."
        )

        return redirect(
            url_for("index")
        )


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


    db.session.commit()


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

        orders=orders,

        order_statuses=ORDER_STATUSES

    )


# ============================================================
# CAMBIAR ESTADO DEL PEDIDO
# ============================================================

@app.post("/pedido/<int:order_id>/estado")
def cambiar_estado(order_id):

    order = db.session.get(
        Order,
        order_id
    )


    if not order:

        flash(
            "El pedido no existe."
        )

        return redirect(
            url_for("pedidos")
        )


    new_status = request.form.get(
        "status"
    )


    if new_status not in ORDER_STATUSES:

        flash(
            "Estado no válido."
        )

        return redirect(
            url_for("pedidos")
        )


    order.status = new_status

    db.session.commit()


    flash(
        f"Pedido #{order.id} actualizado a: {new_status}"
    )


    return redirect(
        url_for("pedidos")
    )


# ============================================================
# PRODUCTOS
# ============================================================

@app.route("/productos")
def productos():

    products = Product.query.order_by(
        Product.id
    ).all()


    return render_template(

        "productos.html",

        products=products

    )


# ============================================================
# CREAR PRODUCTO
# ============================================================

@app.post("/productos/nuevo")
def nuevo_producto():

    name = request.form.get(
        "name",
        ""
    ).strip()

    price_raw = request.form.get(
        "price",
        "0"
    )


    if not name:

        flash(
            "El nombre del producto es obligatorio."
        )

        return redirect(
            url_for("productos")
        )


    try:

        price = float(price_raw)

    except ValueError:

        flash(
            "El precio no es válido."
        )

        return redirect(
            url_for("productos")
        )


    if price < 0:

        flash(
            "El precio no puede ser negativo."
        )

        return redirect(
            url_for("productos")
        )


    existing = Product.query.filter_by(
        name=name
    ).first()


    if existing:

        flash(
            "Ya existe un producto con ese nombre."
        )

        return redirect(
            url_for("productos")
        )


    product = Product(

        name=name,

        price=price,

        active=True

    )


    db.session.add(product)

    db.session.commit()


    flash(
        f"Producto '{name}' creado correctamente."
    )


    return redirect(
        url_for("productos")
    )


# ============================================================
# ACTIVAR / DESACTIVAR PRODUCTO
# ============================================================

@app.post("/productos/<int:product_id>/estado")
def estado_producto(product_id):

    product = db.session.get(
        Product,
        product_id
    )


    if not product:

        flash(
            "El producto no existe."
        )

        return redirect(
            url_for("productos")
        )


    product.active = not product.active

    db.session.commit()


    estado = (
        "activado"
        if product.active
        else "desactivado"
    )


    flash(
        f"Producto '{product.name}' {estado}."
    )


    return redirect(
        url_for("productos")
    )


# ============================================================
# INGREDIENTES
# ============================================================

@app.route("/ingredientes")
def ingredientes():

    ingredients = Ingredient.query.order_by(
        Ingredient.name
    ).all()


    return render_template(

        "ingredientes.html",

        ingredients=ingredients

    )


# ============================================================
# CREAR INGREDIENTE
# ============================================================

@app.post("/ingredientes/nuevo")
def nuevo_ingrediente():

    name = request.form.get(
        "name",
        ""
    ).strip()

    unit = request.form.get(
        "unit",
        ""
    ).strip()

    stock_raw = request.form.get(
        "stock",
        "0"
    )

    minimum_raw = request.form.get(
        "minimum_stock",
        "0"
    )

    cost_raw = request.form.get(
        "cost",
        "0"
    )


    if not name or not unit:

        flash(
            "Nombre y unidad son obligatorios."
        )

        return redirect(
            url_for("ingredientes")
        )


    try:

        stock = float(stock_raw)

        minimum_stock = float(minimum_raw)

        cost = float(cost_raw)

    except ValueError:

        flash(
            "Los valores numéricos no son válidos."
        )

        return redirect(
            url_for("ingredientes")
        )


    if stock < 0 or minimum_stock < 0 or cost < 0:

        flash(
            "Los valores no pueden ser negativos."
        )

        return redirect(
            url_for("ingredientes")
        )


    existing = Ingredient.query.filter_by(
        name=name
    ).first()


    if existing:

        flash(
            "Ya existe un ingrediente con ese nombre."
        )

        return redirect(
            url_for("ingredientes")
        )


    ingredient = Ingredient(

        name=name,

        unit=unit,

        stock=stock,

        minimum_stock=minimum_stock,

        cost=cost,

        active=True

    )


    db.session.add(ingredient)

    db.session.commit()


    flash(
        f"Ingrediente '{name}' creado correctamente."
    )


    return redirect(
        url_for("ingredientes")
    )


# ============================================================
# ACTIVAR / DESACTIVAR INGREDIENTE
# ============================================================

@app.post("/ingredientes/<int:ingredient_id>/estado")
def estado_ingrediente(ingredient_id):

    ingredient = db.session.get(
        Ingredient,
        ingredient_id
    )


    if not ingredient:

        flash(
            "El ingrediente no existe."
        )

        return redirect(
            url_for("ingredientes")
        )


    ingredient.active = not ingredient.active

    db.session.commit()


    estado = (
        "activado"
        if ingredient.active
        else "desactivado"
    )


    flash(
        f"Ingrediente '{ingredient.name}' {estado}."
    )


    return redirect(
        url_for("ingredientes")
    )

@app.route("/productos/<int:product_id>/receta")
def receta_producto(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        flash("El producto no existe.")
        return redirect(url_for("productos"))

    ingredients = Ingredient.query.filter_by(
        active=True
    ).order_by(
        Ingredient.name
    ).all()

    recipe_items = ProductIngredient.query.filter_by(
        product_id=product_id
    ).order_by(
        ProductIngredient.id
    ).all()

    return render_template(
        "receta.html",
        product=product,
        ingredients=ingredients,
        recipe_items=recipe_items
    )


@app.post("/productos/<int:product_id>/receta/agregar")
def agregar_ingrediente_receta(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        flash("El producto no existe.")
        return redirect(url_for("productos"))

    ingredient_id_raw = request.form.get("ingredient_id", "")
    quantity_raw = request.form.get("quantity", "0")

    try:
        ingredient_id = int(ingredient_id_raw)
    except ValueError:
        flash("El ingrediente seleccionado no es válido.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    try:
        quantity = float(quantity_raw)
    except ValueError:
        flash("La cantidad no es válida.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    if quantity <= 0:
        flash("La cantidad debe ser mayor a cero.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    ingredient = db.session.get(Ingredient, ingredient_id)

    if not ingredient or not ingredient.active:
        flash("El ingrediente seleccionado no existe o está inactivo.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    existing = ProductIngredient.query.filter_by(
        product_id=product_id,
        ingredient_id=ingredient_id
    ).first()

    if existing:
        flash(
            f"El ingrediente '{ingredient.name}' ya forma parte de la receta."
        )
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    recipe_item = ProductIngredient(
        product_id=product_id,
        ingredient_id=ingredient_id,
        quantity=quantity
    )

    db.session.add(recipe_item)
    db.session.commit()

    flash(
        f"'{ingredient.name}' agregado a la receta de '{product.name}'."
    )

    return redirect(
        url_for("receta_producto", product_id=product_id)
    )


@app.post("/productos/<int:product_id>/receta/<int:recipe_item_id>/eliminar")
def eliminar_ingrediente_receta(product_id, recipe_item_id):
    recipe_item = db.session.get(
        ProductIngredient,
        recipe_item_id
    )

    if not recipe_item or recipe_item.product_id != product_id:
        flash("El ingrediente de la receta no existe.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    db.session.delete(recipe_item)
    db.session.commit()

    flash("Ingrediente eliminado de la receta.")

    return redirect(
        url_for("receta_producto", product_id=product_id)
    )


@app.post("/productos/<int:product_id>/receta/<int:recipe_item_id>/actualizar")
def actualizar_ingrediente_receta(product_id, recipe_item_id):
    recipe_item = db.session.get(
        ProductIngredient,
        recipe_item_id
    )

    if not recipe_item or recipe_item.product_id != product_id:
        flash("El ingrediente de la receta no existe.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    quantity_raw = request.form.get("quantity", "0")

    try:
        quantity = float(quantity_raw)
    except ValueError:
        flash("La cantidad no es válida.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    if quantity <= 0:
        flash("La cantidad debe ser mayor a cero.")
        return redirect(
            url_for("receta_producto", product_id=product_id)
        )

    recipe_item.quantity = quantity

    db.session.commit()

    flash("Cantidad actualizada correctamente.")

    return redirect(
        url_for("receta_producto", product_id=product_id)
    )
# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
