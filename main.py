import requests
from fastapi import FastAPI, HTTPException, status
from typing import List
from pydantic import BaseModel
import sqlalchemy
from database import database, orders, order_items
from datetime import datetime, timedelta

# --- Моделі Pydantic (контракт API) ---
class OrderItemPayload(BaseModel):
    product_id: int
    quantity: int


class OrderItemResponse(OrderItemPayload):
    id: int
    order_id: int


class OrderResponse(BaseModel):
    id: int
    total_amount: float
    items: List


app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


PRODUCT_SERVICE_URL = "http://localhost:8080/products"


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_items_payload: List[OrderItemPayload]):
    total_amount = 0.0

    for item in order_items_payload:
        try:
            response = requests.get(f"{PRODUCT_SERVICE_URL}/{item.product_id}")
            if response.status_code == 200:
                product_data = response.json()
                total_amount += product_data['price'] * item.quantity
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Product with id {item.product_id} not found.")
        except requests.exceptions.RequestException:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="Cannot connect to Product service.")

    # ⏱ deliveryDate = now + 5 дней
    delivery_date = (datetime.utcnow() + timedelta(days=5)).date()

    # Створення замовлення
    query = orders.insert().values(
        total_amount=total_amount,
        delivery_date=delivery_date
    )
    last_record_id = await database.execute(query)

    items_to_insert = [
        {
            "order_id": last_record_id,
            "product_id": item.product_id,
            "quantity": item.quantity
        }
        for item in order_items_payload
    ]

    query = order_items.insert().values(items_to_insert)
    await database.execute(query)

    # Отримуємо створені items
    query = order_items.select().where(order_items.c.order_id == last_record_id)
    created_items = await database.fetch_all(query)

    created_items = [dict(item) for item in created_items]

    return {
        "id": last_record_id,
        "total_amount": total_amount,
        "delivery_date": str(delivery_date),
        "items": created_items
    }


@app.get("/orders", response_model=List)
async def get_all_orders():
    query = orders.select()
    all_orders = await database.fetch_all(query)

    results = []
    for order in all_orders:
        query = order_items.select().where(order_items.c.order_id == order.id)
        items = await database.fetch_all(query)
        results.append({
            "id": order.id,
            "total_amount": order.total_amount,
            "items": items
        })
    return results