from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict
import threading
import requests
from datetime import date, timedelta

PRODUCT_SERVICE_URL = "http://localhost:8080/products"

# СF6BD9AAO 9>79@C?ODG FastAPI
app = FastAPI()
# --- МB89?і 8аA8х 7а 8BCB@B7BN Pydantic ---
class OrderItem(BaseModel):
    product_id: int
    quantity: int
class Order(BaseModel):
    id: int
    items: List[OrderItem]
    total_amount: float = 0.0
    deliveryDate: str

# --- СхBв8ще в Cа@'яFі ---
orders: Dict[int, Order] = {}
#order_id_counter = threading.local()
order_id_counter = 0

# GET /orders - BFD8@аF8 вEі 7а@Bв?еAAя
@app.get("/orders", response_model=List[Order])
def get_all_orders():
    return list(orders.values())

# GET /orders/{order_id} - BFD8@аF8 7а@Bв?еAAя 7а ID
@app.get("/orders/{order_id}", response_model=Order)
def get_order_by_id(order_id: int):
    if order_id not in orders:
        raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Order not found"
        )
    return orders[order_id]

@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(order_items: List[OrderItem]):
    total_amount = 0.0
    validated_items = []

    for item in order_items:
        try:
            response = requests.get(f"{PRODUCT_SERVICE_URL}/{item.product_id}")

            if response.status_code == 200:
                product_data = response.json()

                total_amount += product_data["price"] * item.quantity
                validated_items.append(item)
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with id {item.product_id} not found."
                )
            else:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Product service is unavailable.")

        except requests.exceptions.RequestException:

            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cannot connect to Product service.")


    global order_id_counter
    order_id_counter += 1
    new_id = order_id_counter

    delivery_date = (date.today() + timedelta(days=5)).isoformat()

    new_order = Order(id=new_id, items=validated_items, total_amount=total_amount,deliveryDate=delivery_date)
    orders[new_id] = new_order
    return new_order