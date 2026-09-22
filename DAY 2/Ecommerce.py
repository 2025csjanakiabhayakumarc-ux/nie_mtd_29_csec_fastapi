from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "E-commerce Customer Support System-Server"}


db = {
    1: {
        "id": 1,
        "title": "Order not received",
        "description": "My laptop order has not been delivered yet",
        "category": "ORDER_NOT_RECEIVED",
        "status": "NEW",
        "customer": "Janaki",
        "assigned_to": None,
        "order_id": "ORD1001",
    },
    2: {
        "id": 2,
        "title": "Wrong item received",
        "description": "I received a different product than the one I ordered",
        "category": "WRONG_ITEM",
        "status": "NEW",
        "customer": "Yavanika",
        "assigned_to": None,
        "order_id": "ORD1002",
    },
}


class TicketCreate(BaseModel):
    title: str
    description: str
    category: str
    status: str
    customer: str
    order_id: str

class TicketResponse(TicketCreate):
    id: int


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


@app.post("/tickets/", status_code=201, response_model=TicketResponse)
def tickets_create(ticket_payload: TicketCreate):
    new_id = max(db.keys(), default=0) + 1

    db[new_id] = {
        "id": new_id,
        **ticket_payload.model_dump()
    }

    return db[new_id]


@app.put("/tickets/{id}", response_model=TicketResponse)
def tickets_update(id: int, payload: TicketCreate):

    if id not in db:
        raise HTTPException(
            detail="Ticket not found",
            status_code=404
        )

    db[id] = {
        "id": id,
        **payload.model_dump()
    }

    return db[id]


@app.delete("/tickets/{id}")
def tickets_delete(id: int):

    if id not in db:
        raise HTTPException(
            detail="Ticket not found",
            status_code=404
        )

    del db[id]

    return {
        "message": "Ticket deleted successfully"
    }