from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI application!"}
db = {
    1: {
        "id": 1,
        "title": "Computer is not on",
        "description": "Power button is not working",
        "category": "Hardware",
        "status": "NEW",
    },
    2: {
        "id": 2,
        "title": "internet is not working",
        "description": "wifi problem",
        "category": "Hardware",
        "status": "NEW",
    },
}


class TicketCreate(BaseModel):
    title: str
    description: str
    category: str
    status: str


class TicketResponse(TicketCreate):
    id: int


@app.get("/tickets/", response_model=list[TicketResponse])
def tickets_read_all():
    return list(db.values())


@app.get("/tickets/{id}", response_model=TicketResponse)
def tickets_read_by_id(id: int):
    if id not in db:
        raise HTTPException(detail="Ticket not found", status_code=404)
    return db[id]


@app.post("/tickets/", status_code=201, response_model=TicketResponse)
def tickets_create(ticket_payload: TicketCreate):
    new_id = max(db.keys(), default=0) + 1
    db[new_id] = {"id": new_id, **ticket_payload.model_dump()}
    return db[new_id]


@app.put("/tickets/{id}", response_model=TicketResponse)
def tickets_update(id: int, payload: TicketCreate):
    if id not in db:
        raise HTTPException(detail="Ticket not found", status_code=404)

    db[id] = {"id": id, **payload.model_dump()}
    return db[id]


@app.delete("/tickets/{id}")
def tickets_delete(id: int):
    if id not in db:
        raise HTTPException(detail="Ticket not found", status_code=404)
    del db[id]
    return {"message": "Ticket deleted successfully"}
