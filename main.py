from fastapi import FastAPI, HTTPException, Header
from typing import Optional
from pydantic import BaseModel

app = FastAPI(title="Shop API")


class Item(BaseModel):
    name: str
    price: float


class ItemInDB(Item):
    id: int


db: dict[int, ItemInDB] = {
    1: ItemInDB(id=1, name="Макбук", price=189900),
    2: ItemInDB(id=2, name="Айфон", price=99900),
    3: ItemInDB(id=3, name="Айпад", price=69900),
    4: ItemInDB(id=4, name="Эйрподс", price=19900),
}


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.get("/items", response_model=list[ItemInDB])
def list_items():
    return db.values()


@app.get("/items/search", response_model=list[ItemInDB])
def search_items(name: str):
    return [item for item in db.values() if name.lower() in item.name.lower()]


@app.get("/items/expensive", response_model=list[ItemInDB])
def get_expensive_items(min_price: float):
    return [item for item in db.values() if item.price >= min_price]


@app.get("/items/{item_id}", response_model=ItemInDB)
def get_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]


@app.post("/items", response_model=ItemInDB, status_code=201)
def create_item(item: Item, authorization: Optional[str] = Header(None)):
    require_admin(get_user_from_token(authorization))
    new_id = max(db.keys(), default=0) + 1
    new_item = ItemInDB(id=new_id, name=item.name, price=item.price)
    db[new_id] = new_item
    return new_item


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, authorization: Optional[str] = Header(None)):
    require_admin(get_user_from_token(authorization))
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    del db[item_id]


@app.put("/items/{item_id}", response_model=ItemInDB)
def update_item(item_id: int, item: Item, authorization: Optional[str] = Header(None)):
    require_admin(get_user_from_token(authorization))
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    db[item_id].name = item.name
    db[item_id].price = item.price
    return db[item_id]


@app.get("/stats")
def get_stats(authorization: Optional[str] = Header(None)):
    require_admin(get_user_from_token(authorization))
    return {
        "total_items": len(db),
        "total_value": sum(item.price for item in db.values())
    }


# --- Пользователи ---

class User(BaseModel):
    name: str
    email: str
    password: str
    is_admin: bool = False


class UserInDB(User):
    id: int


users_db: dict[int, UserInDB] = {
    1: UserInDB(id=1, name="Админ", email="admin@shop.com", password="admin123", is_admin=True),
    2: UserInDB(id=2, name="Клиент", email="customer@shop.com", password="user123", is_admin=False),
}


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Авторизация ---

def get_user_from_token(authorization: Optional[str]) -> Optional[UserInDB]:
    # Извлечь email из заголовка "Bearer <email>"
    if not authorization or not authorization.startswith("Bearer "):
        return None
    email = authorization[7:]  # убрать "Bearer "
    for user in users_db.values():
        if user.email == email:
            return user
    return None


def require_admin(user: Optional[UserInDB]):
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


# --- Пользователи ---

@app.get("/users", response_model=list[UserInDB])
def list_users():
    return list(users_db.values())


@app.get("/users/{user_id}", response_model=UserInDB)
def get_user(user_id: int, authorization: Optional[str] = Header(None)):
    require_admin(get_user_from_token(authorization))
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]


@app.post("/users", response_model=UserInDB, status_code=201)
def create_user(user: User):
    new_id = max(users_db.keys(), default=0) + 1
    new_user = UserInDB(id=new_id, name=user.name, email=user.email, password=user.password, is_admin=user.is_admin)
    users_db[new_id] = new_user
    return new_user


@app.post("/login")
def login(login_req: LoginRequest):
    for user in users_db.values():
        if user.email == login_req.email and user.password == login_req.password:
            return {"access_token": user.email, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/me", response_model=UserInDB)
def get_current_user(email: str):
    for user in users_db.values():
        if user.email == email:
            return user
    raise HTTPException(status_code=404, detail="User not found")


# --- Корзина ---

class CartItem(BaseModel):
    item_id: int
    quantity: int


class CartItemInDB(CartItem):
    id: int


cart_db: dict[int, CartItemInDB] = {}


@app.get("/cart", response_model=list[CartItemInDB])
def get_cart(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    return list(cart_db.values())


@app.post("/cart/items", response_model=CartItemInDB, status_code=201)
def add_to_cart(cart_item: CartItem, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    new_id = max(cart_db.keys(), default=0) + 1
    new_cart_item = CartItemInDB(id=new_id, item_id=cart_item.item_id, quantity=cart_item.quantity)
    cart_db[new_id] = new_cart_item
    return new_cart_item


@app.delete("/cart/items/{cart_item_id}", status_code=204)
def remove_from_cart(cart_item_id: int, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    if cart_item_id not in cart_db:
        raise HTTPException(status_code=404, detail="Cart item not found")
    del cart_db[cart_item_id]


@app.get("/cart/total")
def get_cart_total(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    total = 0
    for cart_item in cart_db.values():
        if cart_item.item_id in db:
            total += db[cart_item.item_id].price * cart_item.quantity
    return {"total": total}
