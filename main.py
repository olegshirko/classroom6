from fastapi import FastAPI, HTTPException, Header
from typing import Optional
from pydantic import BaseModel

app = FastAPI(title="Shop API")


# --- Категории (tuple — фиксированный набор) ---

CATEGORIES: tuple[str, ...] = ("Ноутбуки", "Телефоны", "Планшеты", "Аксессуары")


# --- Модели данных ---

class Item(BaseModel):
    name: str
    price: float
    category: str


class ItemInDB(Item):
    id: int


# --- Товары ---

db: dict[int, ItemInDB] = {
    1: ItemInDB(id=1, name="Макбук", price=189900, category="Ноутбуки"),
    2: ItemInDB(id=2, name="Айфон", price=99900, category="Телефоны"),
    3: ItemInDB(id=3, name="Айпад", price=69900, category="Планшеты"),
    4: ItemInDB(id=4, name="Эйрподс", price=19900, category="Аксессуары"),
}


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.get("/items", response_model=list[ItemInDB])
def list_items(category: Optional[str] = None):
    items = list(db.values())
    if category:
        items = [item for item in items if item.category == category]
    return items


@app.get("/items/search", response_model=list[ItemInDB])
def search_items(name: str):
    return [item for item in db.values() if name.lower() in item.name.lower()]


@app.get("/items/expensive", response_model=list[ItemInDB])
def get_expensive_items(min_price: float):
    return [item for item in db.values() if item.price >= min_price]


@app.get("/items/popular", response_model=list[ItemInDB])
def get_popular_items():
    # Сортируем по просмотрам (убывание), берём топ-5
    sorted_ids = sorted(view_counts.keys(), key=lambda item_id: view_counts[item_id], reverse=True)
    result = []
    for item_id in sorted_ids[:5]:
        if item_id in db:
            result.append(db[item_id])
    return result


@app.get("/items/{item_id}", response_model=ItemInDB)
def get_item(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    # Считаем просмотр
    view_counts[item_id] = view_counts.get(item_id, 0) + 1
    return db[item_id]


@app.post("/items", response_model=ItemInDB, status_code=201)
def create_item(item: Item, authorization: Optional[str] = Header(None)):
    require_admin(get_user_from_token(authorization))
    if item.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {CATEGORIES}")
    new_id = max(db.keys(), default=0) + 1
    new_item = ItemInDB(id=new_id, name=item.name, price=item.price, category=item.category)
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
    if item.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {CATEGORIES}")
    db[item_id].name = item.name
    db[item_id].price = item.price
    db[item_id].category = item.category
    return db[item_id]


@app.get("/stats")
def get_stats(authorization: Optional[str] = Header(None)):
    require_admin(get_user_from_token(authorization))
    return {
        "total_items": len(db),
        "total_value": sum(item.price for item in db.values())
    }


@app.get("/categories", response_model=list[str])
def get_categories():
    return list(CATEGORIES)


# --- Рейтинг товаров ---

# dict[int, list[int]] — item_id → список оценок
ratings: dict[int, list[int]] = {}

# dict[int, float] — item_id → средний балл
avg_ratings: dict[int, float] = {}


class RatingRequest(BaseModel):
    score: int  # 1-5


@app.post("/items/{item_id}/rate", status_code=201)
def rate_item(item_id: int, rating: RatingRequest):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    if rating.score < 1 or rating.score > 5:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 5")
    if item_id not in ratings:
        ratings[item_id] = []
    ratings[item_id].append(rating.score)
    avg_ratings[item_id] = sum(ratings[item_id]) / len(ratings[item_id])
    return {"item_id": item_id, "score": rating.score, "average": avg_ratings[item_id]}


@app.get("/items/{item_id}/rating")
def get_item_rating(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    if item_id not in ratings:
        return {"item_id": item_id, "average": 0, "count": 0}
    return {
        "item_id": item_id,
        "average": avg_ratings.get(item_id, 0),
        "count": len(ratings[item_id])
    }


# --- Просмотры ---

# dict[int, int] — item_id → количество просмотров
view_counts: dict[int, int] = {}


# --- Пользователи ---

class User(BaseModel):
    name: str
    email: str
    password: str
    roles: list[str] = ["customer"]


class UserInDB(User):
    id: int


# Основной словарь пользователей (по id)
users_db: dict[int, UserInDB] = {
    1: UserInDB(id=1, name="Админ", email="admin@shop.com", password="admin123", roles=["admin"]),
    2: UserInDB(id=2, name="Клиент", email="customer@shop.com", password="user123", roles=["customer"]),
}

# Второй индекс для быстрого поиска по email — dict[str, UserInDB]
users_by_email: dict[str, UserInDB] = {
    "admin@shop.com": users_db[1],
    "customer@shop.com": users_db[2],
}


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Авторизация ---

def get_user_from_token(authorization: Optional[str]) -> Optional[UserInDB]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    email = authorization[7:]
    # O(1) поиск по email вместо перебора всех пользователей
    return users_by_email.get(email)


def require_admin(user: Optional[UserInDB]):
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    if "admin" not in user.roles:
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
    if user.email in users_by_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    new_id = max(users_db.keys(), default=0) + 1
    new_user = UserInDB(id=new_id, name=user.name, email=user.email, password=user.password, roles=user.roles)
    users_db[new_id] = new_user
    users_by_email[user.email] = new_user
    return new_user


@app.post("/login")
def login(login_req: LoginRequest):
    # O(1) поиск по email
    user = users_by_email.get(login_req.email)
    if user and user.password == login_req.password:
        return {"access_token": user.email, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/me", response_model=UserInDB)
def get_current_user(email: str):
    # O(1) поиск по email
    user = users_by_email.get(email)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


# --- Корзина (привязана к email пользователя) ---

# dict[str, dict[int, int]] — email → {item_id: quantity}
carts: dict[str, dict[int, int]] = {}


class CartItem(BaseModel):
    item_id: int
    quantity: int


class CartItemOut(BaseModel):
    item_id: int
    quantity: int


@app.get("/cart", response_model=list[CartItemOut])
def get_cart(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    user_cart = carts.get(user.email, {})
    return [{"item_id": item_id, "quantity": qty} for item_id, qty in user_cart.items()]


@app.post("/cart/items", response_model=CartItemOut, status_code=201)
def add_to_cart(cart_item: CartItem, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    if cart_item.item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    if user.email not in carts:
        carts[user.email] = {}
    # Если товар уже в корзине — увеличиваем количество
    if cart_item.item_id in carts[user.email]:
        carts[user.email][cart_item.item_id] += cart_item.quantity
    else:
        carts[user.email][cart_item.item_id] = cart_item.quantity
    return {"item_id": cart_item.item_id, "quantity": carts[user.email][cart_item.item_id]}


@app.delete("/cart/items/{item_id}", status_code=204)
def remove_from_cart(item_id: int, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    user_cart = carts.get(user.email, {})
    if item_id not in user_cart:
        raise HTTPException(status_code=404, detail="Cart item not found")
    del carts[user.email][item_id]


@app.get("/cart/total")
def get_cart_total(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    user_cart = carts.get(user.email, {})
    total = 0
    for item_id, qty in user_cart.items():
        if item_id in db:
            total += db[item_id].price * qty
    return {"total": total}


# --- Избранное ---

# dict[str, set[int]] — email → set[item_id]
wishlist: dict[str, set[int]] = {}


@app.post("/wishlist/add/{item_id}", status_code=201)
def add_to_wishlist(item_id: int, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    if user.email not in wishlist:
        wishlist[user.email] = set()
    wishlist[user.email].add(item_id)
    return {"item_id": item_id}


@app.get("/wishlist", response_model=list[ItemInDB])
def get_wishlist(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    user_wishlist = wishlist.get(user.email, set())
    return [db[item_id] for item_id in user_wishlist if item_id in db]


@app.delete("/wishlist/remove/{item_id}", status_code=204)
def remove_from_wishlist(item_id: int, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    user_wishlist = wishlist.get(user.email, set())
    if item_id not in user_wishlist:
        raise HTTPException(status_code=404, detail="Item not in wishlist")
    user_wishlist.discard(item_id)


# --- История поиска ---

# dict[str, list[str]] — email → список поисковых запросов
search_history: dict[str, list[str]] = {}


@app.get("/items/search/history", response_model=list[str])
def get_search_history(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    return search_history.get(user.email, [])


@app.get("/items/search/with-history", response_model=list[ItemInDB])
def search_items_with_history(name: str, authorization: Optional[str] = Header(None)):
    # Сохраняем запрос в историю если пользователь авторизован
    user = get_user_from_token(authorization)
    if user:
        if user.email not in search_history:
            search_history[user.email] = []
        search_history[user.email].append(name)
    # Ищем товары
    return [item for item in db.values() if name.lower() in item.name.lower()]
