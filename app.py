import os
from datetime import datetime
from decimal import Decimal

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_sqlalchemy import SQLAlchemy


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


# ============================================================
# MODELO RECETA
# ============================================================

class ProductIngredient(db.Model):

    __tablename__ = "product_ingredients"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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
# MODELO COMPRA
# ============================================================

class Purchase(db.Model):

    __tablename__ = "purchases"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    supplier = db.Column(
        db.String(150),
        nullable=False
    )

    invoice_number = db.Column(
        db.String(100),
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    total = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Confirmada"
    )


# ============================================================
# MODELO DETALLE DE COMPRA
# ============================================================

class PurchaseItem(db.Model):

    __tablename__ = "purchase_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    purchase_id = db.Column(
        db.Integer,
        db.ForeignKey("purchases.id"),
        nullable=False
    )

    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredients.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Numeric(12, 3),
        nullable=False
    )

    unit_cost = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    purchase = db.relationship(
        "Purchase",
        backref=db.backref(
            "items",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    ingredient = db.relationship(
        "Ingredient"
    )
# ============================================================
# MODELO MOVIMIENTO DE INVENTARIO / KARDEX
# ============================================================

class InventoryMovement(db.Model):

    __tablename__ = "inventory_movements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredients.id"),
        nullable=False
    )

    movement_type = db.Column(
        db.String(30),
        nullable=False
    )

    reference_id = db.Column(
        db.Integer,
        nullable=True
    )

    reference_type = db.Column(
        db.String(30),
        nullable=True
    )

    quantity = db.Column(
        db.Numeric(12, 3),
        nullable=False
    )

    unit_cost = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    total_cost = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    stock_before = db.Column(
        db.Numeric(12, 3),
        nullable=False,
        default=0
    )

    stock_after = db.Column(
        db.Numeric(12, 3),
        nullable=False,
        default=0
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    ingredient = db.relationship(
        "Ingredient",
        backref=db.backref(
            "inventory_movements",
            lazy=True
        )
    )

# ============================================================
# CREAR TABLAS
# ============================================================

with app.app_context():
    db.create_all()

# ============================================================
# REGISTRAR MOVIMIENTO DE INVENTARIO
# ============================================================

def registrar_movimiento_inventario(
    ingredient,
    movement_type,
    quantity,
    unit_cost=Decimal("0"),
    reference_id=None,
    reference_type=None,
    notes=None
):

    quantity = Decimal(str(quantity))
    unit_cost = Decimal(str(unit_cost))

    if quantity <= 0:

        raise ValueError(
            "La cantidad del movimiento debe ser mayor a cero."
        )

    stock_before = Decimal(
        str(ingredient.stock)
    )

    # --------------------------------------------------------
    # DETERMINAR SI ES ENTRADA O SALIDA
    # --------------------------------------------------------

    entradas = {
        "COMPRA",
        "AJUSTE_ENTRADA",
        "DEVOLUCION"
    }

    salidas = {
        "VENTA",
        "AJUSTE_SALIDA"
    }

    if movement_type in entradas:

        stock_after = (
            stock_before + quantity
        )

    elif movement_type in salidas:

        if stock_before < quantity:

            raise ValueError(
                f"No hay suficiente stock de "
                f"'{ingredient.name}'. "
                f"Disponible: {stock_before:.3f} "
                f"{ingredient.unit}. "
                f"Necesario: {quantity:.3f} "
                f"{ingredient.unit}."
            )

        stock_after = (
            stock_before - quantity
        )

    else:

        raise ValueError(
            f"Tipo de movimiento no válido: "
            f"{movement_type}"
        )

    total_cost = (
        quantity * unit_cost
    )

    movement = InventoryMovement(
        ingredient_id=ingredient.id,
        movement_type=movement_type,
        reference_id=reference_id,
        reference_type=reference_type,
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=total_cost,
        stock_before=stock_before,
        stock_after=stock_after,
        notes=notes
    )

    ingredient.stock = stock_after

    db.session.add(movement)

    return movement
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
    total = Decimal("0")

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

        except (ValueError, TypeError):
            qty = 0

        if qty:

            price = Decimal(str(product.price))
            subtotal = price * qty

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
# DESCONTAR INVENTARIO SEGÚN LA RECETA
# ============================================================

def descontar_inventario_pedido(order):

    order_items = OrderItem.query.filter_by(
        order_id=order.id
    ).all()

    # --------------------------------------------------------
    # ACUMULAR TODO EL CONSUMO POR INGREDIENTE
    # --------------------------------------------------------

    consumos = {}

    for order_item in order_items:

        recipe_items = ProductIngredient.query.filter_by(
            product_id=order_item.product_id
        ).all()

        for recipe_item in recipe_items:

            ingredient = recipe_item.ingredient

            required_quantity = (
                Decimal(str(recipe_item.quantity))
                * order_item.qty
            )

            key = ingredient.id

            if key not in consumos:

                consumos[key] = {
                    "ingredient": ingredient,
                    "quantity": Decimal("0"),
                    "items": []
                }

            consumos[key]["quantity"] += required_quantity

            consumos[key]["items"].append({
                "order_item": order_item,
                "recipe_item": recipe_item,
                "quantity": required_quantity
            })

    # --------------------------------------------------------
    # VERIFICAR TODO EL STOCK ANTES DE DESCONTAR
    # --------------------------------------------------------

    for data in consumos.values():

        ingredient = data["ingredient"]
        required_quantity = data["quantity"]

        current_stock = Decimal(
            str(ingredient.stock)
        )

        if current_stock < required_quantity:

            raise ValueError(
                f"No hay suficiente stock de "
                f"'{ingredient.name}'. "
                f"Disponible: {current_stock:.3f} "
                f"{ingredient.unit}. "
                f"Necesario: {required_quantity:.3f} "
                f"{ingredient.unit}."
            )

    # --------------------------------------------------------
    # DESCONTAR INVENTARIO
    # --------------------------------------------------------

    for data in consumos.values():

        ingredient = data["ingredient"]
        total_quantity = data["quantity"]

        ingredient.stock = (
            Decimal(str(ingredient.stock))
            - total_quantity
        )

        # Registrar cada producto/ingrediente
        # consumido por el pedido

        for item_data in data["items"]:

            order_item = item_data["order_item"]
            recipe_item = item_data["recipe_item"]
            quantity = item_data["quantity"]
        
            ingredient = recipe_item.ingredient
        
            registrar_movimiento_inventario(
                ingredient=ingredient,
                movement_type="VENTA",
                quantity=quantity,
                unit_cost=ingredient.cost,
                reference_id=order.id,
                reference_type="PEDIDO",
                notes=f"Consumo por Pedido #{order.id}"
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

    # --------------------------------------------------------
    # DESCONTAR INVENTARIO AL PASAR A EN PREPARACIÓN
    # --------------------------------------------------------

    if (
        new_status == "En preparación"
        and order.status != "En preparación"
    ):

        try:

            # Comprobar si ya existe algún movimiento
            # para este pedido.

            existing_movement = (
                InventoryMovement.query
                .filter_by(
                    order_id=order.id
                )
                .first()
            )

            if not existing_movement:

                descontar_inventario_pedido(order)

        except ValueError as e:

            db.session.rollback()

            flash(
                str(e)
            )

            return redirect(
                url_for("pedidos")
            )

    # --------------------------------------------------------
    # ACTUALIZAR ESTADO
    # --------------------------------------------------------

    order.status = new_status

    db.session.commit()

    flash(
        f"Pedido #{order.id} actualizado a: {new_status}"
    )

    return redirect(
        url_for("pedidos")
    )

# ============================================================
# COMPRAS
# ============================================================

@app.route("/compras")
def compras():

    purchases = Purchase.query.order_by(
        Purchase.created_at.desc()
    ).all()

    return render_template(
        "compras.html",
        purchases=purchases
    )

# ============================================================
# NUEVA COMPRA
# ============================================================

@app.route("/compras/nueva", methods=["GET", "POST"])
def nueva_compra():

    ingredients = Ingredient.query.filter_by(
        active=True
    ).order_by(
        Ingredient.name
    ).all()

    if request.method == "GET":

        return render_template(
            "nueva_compra.html",
            ingredients=ingredients
        )

    supplier = request.form.get(
        "supplier",
        ""
    ).strip()

    invoice_number = request.form.get(
        "invoice_number",
        ""
    ).strip()

    notes = request.form.get(
        "notes",
        ""
    ).strip()

    if not supplier:

        flash(
            "El proveedor es obligatorio."
        )

        return redirect(
            url_for("nueva_compra")
        )

    items = []
    total = Decimal("0")

    for ingredient in ingredients:

        quantity_raw = request.form.get(
            f"quantity_{ingredient.id}",
            "0"
        )

        cost_raw = request.form.get(
            f"cost_{ingredient.id}",
            "0"
        )

        try:

            quantity = Decimal(
                str(quantity_raw)
            )

            unit_cost = Decimal(
                str(cost_raw)
            )

        except Exception:

            flash(
                f"Los valores de "
                f"'{ingredient.name}' no son válidos."
            )

            return redirect(
                url_for("nueva_compra")
            )

        if quantity < 0 or unit_cost < 0:

            flash(
                f"Los valores de "
                f"'{ingredient.name}' no pueden ser negativos."
            )

            return redirect(
                url_for("nueva_compra")
            )

        if quantity > 0:

            subtotal = quantity * unit_cost

            items.append({
                "ingredient": ingredient,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "subtotal": subtotal
            })

            total += subtotal

    if not items:

        flash(
            "Debes ingresar al menos un ingrediente."
        )

        return redirect(
            url_for("nueva_compra")
        )

    purchase = Purchase(
        supplier=supplier,
        invoice_number=invoice_number,
        notes=notes,
        total=total,
        status="Confirmada"
    )

    db.session.add(purchase)

    db.session.flush()

    for item in items:

        ingredient = item["ingredient"]

        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            ingredient_id=ingredient.id,
            quantity=item["quantity"],
            unit_cost=item["unit_cost"],
            subtotal=item["subtotal"]
        )

        db.session.add(purchase_item)

        # AUMENTAR INVENTARIO
        registrar_movimiento_inventario(
            ingredient=ingredient,
            movement_type="COMPRA",
            quantity=item["quantity"],
            unit_cost=item["unit_cost"],
            reference_id=purchase.id,
            reference_type="COMPRA",
            notes=f"Compra #{purchase.id}"
        )

        ingredient.cost = item["unit_cost"]

    db.session.commit()

    flash(
        f"Compra #{purchase.id} registrada correctamente. "
        f"Inventario actualizado."
    )

    return redirect(
        url_for("compras")
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

        price = Decimal(
            str(price_raw)
        )

    except Exception:

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

        stock = Decimal(
            str(stock_raw)
        )

        minimum_stock = Decimal(
            str(minimum_raw)
        )

        cost = Decimal(
            str(cost_raw)
        )

    except Exception:

        flash(
            "Los valores numéricos no son válidos."
        )

        return redirect(
            url_for("ingredientes")
        )

    if (
        stock < 0
        or minimum_stock < 0
        or cost < 0
    ):

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


# ============================================================
# RECETA DE PRODUCTO
# ============================================================

@app.route("/productos/<int:product_id>/receta")
def receta_producto(product_id):

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

    # --------------------------------------------------------
    # CALCULAR COSTOS DE LA RECETA
    # --------------------------------------------------------

    recipe_cost_items = []
    total_cost = Decimal("0")

    for item in recipe_items:

        quantity = Decimal(
            str(item.quantity)
        )

        unit_cost = Decimal(
            str(item.ingredient.cost)
        )

        item_cost = (
            quantity
            * unit_cost
        )

        recipe_cost_items.append({
            "id": item.id,
            "ingredient": item.ingredient,
            "quantity": float(quantity),
            "unit_cost": float(unit_cost),
            "cost": float(item_cost)
        })

        total_cost += item_cost

    sale_price = Decimal(
        str(product.price)
    )

    profit = (
        sale_price
        - total_cost
    )

    if sale_price > 0:

        margin = (
            profit
            / sale_price
        ) * 100

    else:

        margin = Decimal("0")

    return render_template(
        "receta.html",
        product=product,
        ingredients=ingredients,
        recipe_items=recipe_items,
        recipe_cost_items=recipe_cost_items,
        total_cost=float(total_cost),
        sale_price=float(sale_price),
        profit=float(profit),
        margin=float(margin)
    )


# ============================================================
# AGREGAR INGREDIENTE A RECETA
# ============================================================

@app.post(
    "/productos/<int:product_id>/receta/agregar"
)
def agregar_ingrediente_receta(product_id):

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

    ingredient_id_raw = request.form.get(
        "ingredient_id",
        ""
    )

    quantity_raw = request.form.get(
        "quantity",
        "0"
    )

    try:

        ingredient_id = int(
            ingredient_id_raw
        )

    except (ValueError, TypeError):

        flash(
            "El ingrediente seleccionado no es válido."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    try:

        quantity = Decimal(
            str(quantity_raw)
        )

    except Exception:

        flash(
            "La cantidad no es válida."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    if quantity <= 0:

        flash(
            "La cantidad debe ser mayor a cero."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    ingredient = db.session.get(
        Ingredient,
        ingredient_id
    )

    if not ingredient or not ingredient.active:

        flash(
            "El ingrediente seleccionado no existe o está inactivo."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    existing = ProductIngredient.query.filter_by(
        product_id=product_id,
        ingredient_id=ingredient_id
    ).first()

    if existing:

        flash(
            f"El ingrediente '{ingredient.name}' "
            "ya forma parte de la receta."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    recipe_item = ProductIngredient(
        product_id=product_id,
        ingredient_id=ingredient_id,
        quantity=quantity
    )

    db.session.add(recipe_item)
    db.session.commit()

    flash(
        f"'{ingredient.name}' agregado a la receta "
        f"de '{product.name}'."
    )

    return redirect(
        url_for(
            "receta_producto",
            product_id=product_id
        )
    )


# ============================================================
# ELIMINAR INGREDIENTE DE RECETA
# ============================================================

@app.post(
    "/productos/<int:product_id>/receta/"
    "<int:recipe_item_id>/eliminar"
)
def eliminar_ingrediente_receta(
    product_id,
    recipe_item_id
):

    recipe_item = db.session.get(
        ProductIngredient,
        recipe_item_id
    )

    if (
        not recipe_item
        or recipe_item.product_id != product_id
    ):

        flash(
            "El ingrediente de la receta no existe."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    db.session.delete(
        recipe_item
    )

    db.session.commit()

    flash(
        "Ingrediente eliminado de la receta."
    )

    return redirect(
        url_for(
            "receta_producto",
            product_id=product_id
        )
    )


# ============================================================
# ACTUALIZAR INGREDIENTE DE RECETA
# ============================================================

@app.post(
    "/productos/<int:product_id>/receta/"
    "<int:recipe_item_id>/actualizar"
)
def actualizar_ingrediente_receta(
    product_id,
    recipe_item_id
):

    recipe_item = db.session.get(
        ProductIngredient,
        recipe_item_id
    )

    if (
        not recipe_item
        or recipe_item.product_id != product_id
    ):

        flash(
            "El ingrediente de la receta no existe."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    quantity_raw = request.form.get(
        "quantity",
        "0"
    )

    try:

        quantity = Decimal(
            str(quantity_raw)
        )

    except Exception:

        flash(
            "La cantidad no es válida."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    if quantity <= 0:

        flash(
            "La cantidad debe ser mayor a cero."
        )

        return redirect(
            url_for(
                "receta_producto",
                product_id=product_id
            )
        )

    recipe_item.quantity = quantity

    db.session.commit()

    flash(
        "Cantidad actualizada correctamente."
    )

    return redirect(
        url_for(
            "receta_producto",
            product_id=product_id
        )
    )
    # ============================================================
    # CONTROL DE INVENTARIO
    # ============================================================
    
    @app.route("/inventario")
    def control_inventario():
    
        ingredients = Ingredient.query.order_by(
            Ingredient.name
        ).all()
    
        return render_template(
            "inventario_control.html",
            ingredients=ingredients
        )
    # ============================================================
    # KARDEX GENERAL
    # ============================================================
    
    @app.route("/kardex")
    def kardex():
    
        ingredient_id = request.args.get(
            "ingredient_id",
            type=int
        )
    
        movement_type = request.args.get(
            "movement_type",
            ""
        ).strip()
    
        ingredients = Ingredient.query.order_by(
            Ingredient.name
        ).all()
    
        query = InventoryMovement.query
    
        if ingredient_id:
    
            query = query.filter_by(
                ingredient_id=ingredient_id
            )
    
        if movement_type:
    
            query = query.filter_by(
                movement_type=movement_type
            )
    
        movements = query.order_by(
            InventoryMovement.created_at.desc()
        ).all()
    
        return render_template(
            "kardex.html",
            movements=movements,
            ingredients=ingredients,
            selected_ingredient=ingredient_id,
            selected_type=movement_type
        )

# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
