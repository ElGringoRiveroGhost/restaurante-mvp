from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "demo-secret"

PRODUCTS = {
    1: {"name": "Sándwich de Milanesa", "price": 20.00},
    2: {"name": "Choripán", "price": 18.00},
}

orders = []
next_order_id = 1

@app.route("/")
def index():
    return render_template("pedido.html", products=PRODUCTS)

@app.post("/pedido")
def crear_pedido():
    global next_order_id

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    payment = request.form.get("payment", "")
    notes = request.form.get("notes", "").strip()

    if not name or not phone:
        flash("El nombre y teléfono son obligatorios.")
        return redirect(url_for("index"))

    items = []
    total = 0

    for product_id, product in PRODUCTS.items():
        qty_raw = request.form.get(f"qty_{product_id}", "0")
        try:
            qty = max(0, int(qty_raw))
        except ValueError:
            qty = 0

        if qty:
            subtotal = qty * product["price"]
            items.append({
                "product_id": product_id,
                "name": product["name"],
                "qty": qty,
                "price": product["price"],
                "subtotal": subtotal
            })
            total += subtotal

    if not items:
        flash("Agrega al menos un producto.")
        return redirect(url_for("index"))

    order = {
        "id": next_order_id,
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "name": name,
        "phone": phone,
        "address": address,
        "payment": payment,
        "notes": notes,
        "items": items,
        "total": total,
        "status": "Pendiente"
    }

    orders.append(order)
    next_order_id += 1

    return render_template("confirmacion.html", order=order)

@app.route("/pedidos")
def pedidos():
    return render_template("pedidos.html", orders=orders)

if __name__ == "__main__":
    app.run(debug=True)
