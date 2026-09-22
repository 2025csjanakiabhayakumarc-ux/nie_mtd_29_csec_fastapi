from fastapi import FastAPI, HTTPException

app = FastAPI() 

@app.get("/")
def home():
    return {"message": "E-commerce Customer Support System - Server"}

db = {
    1: {
        "id": 1,
        "title": "Order not received",
        "description": "My laptop order has not been delivered yet",
        "category": "ORDER_NOT_RECEIVED",
        "status": "NEW",
        "customer": "JANAKI",
        "assigned_to": None,
        "resolved_by": None,
        "order_id": "ORD1001"
    }
}

@app.get("/tickets/")
def tickets_read_all():
    return list(db.values())

@app.get("/tickets/{id}")
def tickets_read_by_id(id: int):

    if id not in db:
        raise HTTPException(
            detail="Ticket not found",
            status_code=404
        )

    return db[id]