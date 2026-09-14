# Restaurante MVP — Paso 1

Prototipo inicial de una WebApp para registrar pedidos.

## Incluye
- Formulario de nuevo pedido.
- Cliente, teléfono y dirección.
- Milanesa y choripán.
- Cantidades.
- Forma de pago.
- Observaciones.
- Generación automática de número de pedido.
- Confirmación.
- Tablero inicial de pedidos.

## Ejecutar localmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Abrir:
http://127.0.0.1:5000

## Próxima etapa
Sustituir la memoria temporal por PostgreSQL y agregar clientes, productos, estados y persistencia.
