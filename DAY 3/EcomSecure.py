from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from pymongo import MongoClient
from bson import ObjectId

import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone


app = FastAPI()


# Mongo
URL = "mongodb://127.0.0.1:27017/"
client = MongoClient(URL)

db = client["shopcare_support_db"]
tickets_collection = db["tickets"]
user_collection = db["users"]


# Security config
password_hash = PasswordHash.recommended()

SECRET_KEY = "ITServiceDeskSecurityKey-ChangeThis"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# Pydantic

class TicketCreate(BaseModel):
    title: str
    description: str
    category: str
    order_id: str
    status: str = "NEW"


class TicketResponse(TicketCreate):
    id: str
    customer: str
    assigned_to: str | None = None


class UserCreate(BaseModel):
    username: str
    password: str
    role: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# Helper

def ticket_helper(ticket):
    return {
        "id": str(ticket["_id"]),
        "title": ticket["title"],
        "description": ticket["description"],
        "category": ticket["category"],
        "customer": ticket["customer"],
        "order_id": ticket["order_id"],
        "status": ticket.get("status", "NEW"),
        "assigned_to": ticket.get("assigned_to")
    }


def user_helper(user):
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "role": user["role"]
        # 1 = Customer
        # 2 = Support Agent
        # 3 = Team Lead
        # 4 = Admin
    }


# JWT

def create_token(username: str, role: int):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_EXPIRE_MINS
    )

    payload = {
        "sub": username,
        "role": role,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        role = payload.get("role")

        if username is None or role is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = user_collection.find_one(
        {"username": username}
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User Not Found"
        )

    return user


def require_roles(*allowed_roles):

    def check_role(
        current_user=Depends(get_current_user)
    ):

        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )

        return current_user

    return check_role


# USERS

@app.post("/users", status_code=201)
def create_user(user: UserCreate):

    queried_user = user_collection.find_one(
        {"username": user.username}
    )

    if queried_user:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    hashed_pwd = password_hash.hash(user.password)

    user_data = {
        "username": user.username,
        "password": hashed_pwd,
        "role": user.role
    }

    result = user_collection.insert_one(user_data)

    new_user = user_collection.find_one(
        {"_id": result.inserted_id}
    )

    return user_helper(new_user)


# LOGIN

@app.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    user = user_collection.find_one(
        {"username": form_data.username}
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not password_hash.verify(
        form_data.password,
        user["password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_token(
        user["username"],
        user["role"]
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# TICKETS

# CREATE
@app.post(
    "/tickets",
    status_code=201,
    response_model=TicketResponse
)
def ticket_create(
    payload: TicketCreate,
    current_user=Depends(
        require_roles(1, 2, 3, 4)
    )
):

    ticket_dict = payload.model_dump()

    # Customer is taken from logged-in user
    ticket_dict["customer"] = current_user["username"]

    result = tickets_collection.insert_one(
        ticket_dict
    )

    new_ticket = tickets_collection.find_one(
        {"_id": result.inserted_id}
    )

    return ticket_helper(new_ticket)


# READ ALL
@app.get(
    "/tickets",
    response_model=list[TicketResponse]
)
def ticket_read_all(
    current_user=Depends(
        require_roles(1, 2, 3, 4)
    )
):

    # Customer sees only own tickets
    if current_user["role"] == 1:
        docs = tickets_collection.find({
            "customer": current_user["username"]
        })

    # Staff can see all tickets
    else:
        docs = tickets_collection.find()

    return [
        ticket_helper(doc)
        for doc in docs
    ]


# READ BY ID
@app.get(
    "/tickets/{id}",
    response_model=TicketResponse
)
def ticket_read_by_id(
    id: str,
    current_user=Depends(
        require_roles(1, 2, 3, 4)
    )
):

    if not ObjectId.is_valid(id):
        raise HTTPException(
            detail="Invalid ticket ID",
            status_code=400
        )

    doc = tickets_collection.find_one(
        {"_id": ObjectId(id)}
    )

    if not doc:
        raise HTTPException(
            detail="Ticket not found",
            status_code=404
        )

    # Customer can access only own ticket
    if (
        current_user["role"] == 1
        and doc["customer"] != current_user["username"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    return ticket_helper(doc)


# UPDATE
@app.put(
    "/tickets/{id}",
    response_model=TicketResponse
)
def ticket_update(
    id: str,
    payload: TicketCreate,
    current_user=Depends(
        require_roles(2, 3, 4)
    )
):

    if not ObjectId.is_valid(id):
        raise HTTPException(
            detail="Invalid ticket ID",
            status_code=400
        )

    ticket_dict = payload.model_dump()

    result = tickets_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": ticket_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(
            detail="Ticket not found",
            status_code=404
        )

    new_ticket = tickets_collection.find_one(
        {"_id": ObjectId(id)}
    )

    return ticket_helper(new_ticket)


# DELETE
@app.delete("/tickets/{id}")
def ticket_delete(
    id: str,
    current_user=Depends(
        require_roles(4)
    )
):

    if not ObjectId.is_valid(id):
        raise HTTPException(
            detail="Invalid ticket ID",
            status_code=400
        )

    result = tickets_collection.delete_one(
        {"_id": ObjectId(id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            detail="Ticket not found"
        )

    return {
        "message": "Ticket deleted successfully"
    }