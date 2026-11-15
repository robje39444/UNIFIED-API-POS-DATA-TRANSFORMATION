
# pyright: reportMissingImports=false
import random
from datetime import datetime, timedelta
from decimal import Decimal as PyDecimal

from flask import Flask, Response, request

try:
    from spyne import Application, Array, ComplexModel, ServiceBase, Unicode, rpc
    from spyne.model.primitive import Integer, Decimal as SpyneDecimal
    from spyne.protocol.soap import Soap11
    from spyne.server.wsgi import WsgiApplication
except ImportError:  # pragma: no cover - optional dependency for SOAP support
    class ComplexModel:
        def __init__(self, *args, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class ServiceBase:
        pass

    class Array(list):
        pass

    class Unicode(str):
        pass

    class Integer(int):
        pass

    class SpyneDecimal(PyDecimal):
        pass

    class Application:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class Soap11:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class WsgiApplication:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def __call__(self, *args, **kwargs):
            raise RuntimeError("spyne is not installed; SOAP support is unavailable")

    def rpc(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


app = Flask(__name__)

SKU_LIST = [
    {
        "id": 1,
        "name": "Laptop",
        "description": "Gaming laptop",
        "price": 999.99,
        "currency": "USD",
        "quantity_on_hand": 25,
        "created": datetime.now().isoformat(),
    },
    {
        "id": 2,
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse",
        "price": 39.5,
        "currency": "USD",
        "quantity_on_hand": 80,
        "created": datetime.now().isoformat(),
    },
    {
        "id": 3,
        "name": "Mechanical Keyboard",
        "description": "RGB mechanical keyboard",
        "price": 89.0,
        "currency": "USD",
        "quantity_on_hand": 55,
        "created": datetime.now().isoformat(),
    },
]
SKU_BY_ID = {sku["id"]: sku for sku in SKU_LIST}


# --------------------------------------------------------------------
# 3. Spyne SOAP service
# --------------------------------------------------------------------


class SKUSchema(ComplexModel):
    id = Integer
    name = Unicode
    description = Unicode
    price_per_unit = SpyneDecimal
    currency = Unicode
    quantity_on_hand = Integer
    created = Unicode


# NEW: Schema for SOAP order responses
class OrderSchema(ComplexModel):
    id = Integer
    sku_id = Integer
    sku_name = Unicode
    quantity = Integer
    unit_price = SpyneDecimal
    total_price = SpyneDecimal
    currency = Unicode
    status = Unicode
    transaction_date = Unicode


class OrderResponse(ComplexModel):
    id = Integer
    name = Unicode
    description = Unicode
    total_price = SpyneDecimal
    currency = Unicode
    quantity_requested = Integer
    created = Unicode
    transaction_date = Unicode


class ECommerceService(ServiceBase):
    @rpc(_returns=Array(SKUSchema))
    def list_items(ctx):
        return [
            SKUSchema(
                id=sku["id"],
                name=sku["name"],
                description=sku["description"],
                price_per_unit=PyDecimal(str(sku["price"])),
                currency=sku["currency"],
                quantity_on_hand=sku["quantity_on_hand"],
                created=sku["created"],
            )
            for sku in SKU_LIST
        ]

    # NEW: SOAP endpoint to list orders
    @rpc(_returns=Array(OrderSchema))
    def list_orders(ctx):
        """SOAP operation – return a list of prefilled fake orders."""
        orders = []
        current_time = datetime.now()
        two_months_ago = current_time - timedelta(days=60)
        seconds_in_range = int((current_time - two_months_ago).total_seconds())
        for _ in range(100):
            sku = random.choice(SKU_LIST)
            qty = random.randint(1, 10)
            random_seconds_offset = random.randint(0, seconds_in_range)
            txn_date = current_time - timedelta(seconds=random_seconds_offset)
            orders.append(
                OrderSchema(
                    id=random.randint(100000, 999999),
                    sku_id=sku["id"],
                    sku_name=sku["name"],
                    quantity=qty,
                    unit_price=PyDecimal(str(sku["price"])),
                    total_price=PyDecimal(str(sku["price"] * qty)),
                    currency="USD",
                    status=random.choice(["completed", "pending", "shipped", "failed"]),
                    transaction_date=txn_date.isoformat(),
                )
            )
        return orders

    @rpc(Integer, Integer, Unicode, _returns=OrderResponse)
    def request_item(ctx, item_id, qty_requested, currency_req):
        sku = SKU_BY_ID.get(item_id)
        if not sku:
            raise ValueError(f"SKU id {item_id} not found")
        total_price = round(sku["price"] * qty_requested, 2)
        txn_date = datetime.now().isoformat()
        return OrderResponse(
            id=sku["id"],
            name=sku["name"],
            description=sku["description"],
            total_price=PyDecimal(str(total_price)),
            currency=currency_req,
            quantity_requested=qty_requested,
            created=sku["created"],
            transaction_date=txn_date,
        )


soap_app = Application(
    [ECommerceService],
    tns="http://localhost:5000/service",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)
wsgi_soap = WsgiApplication(soap_app)


@app.route("/service", methods=["GET", "POST"])
def soap_service():
    status_code = 200
    headers = {}

    def start_response(status, response_headers):
        nonlocal status_code, headers
        status_code = int(status.split(" ")[0])
        headers = dict(response_headers)

    body_iter = wsgi_soap(request.environ, start_response)
    body = b"".join(body_iter).decode()
    return Response(body, status=status_code, headers=headers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)