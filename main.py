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
    # TODO: верни все значения из db как список
    pass


@app.get("/items/search", response_model=list[ItemInDB])
def search_items(name: str):
    # TODO: найди все товары, в названии которых есть подстрока name (без учёта регистра)
    # верни найденные товары как список
    pass


@app.get("/items/expensive", response_model=list[ItemInDB])
def get_expensive_items(min_price: float):
    # TODO: найди все товары с ценой >= min_price
    # верни их как список
    pass


@app.get("/items/{item_id}", response_model=ItemInDB)
def get_item(item_id: int):
    # TODO: проверь наличие ключа в db и верни значение
    # если ключа нет - raise HTTPException(status_code=404, detail="Item not found")
    pass


@app.post("/items", response_model=ItemInDB, status_code=201)
def create_item(item: Item, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # сгенерируй новый id (max ключ в db + 1)
    # создай ItemInDB и добавь в db по ключу
    # верни созданный объект
    pass


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # проверь наличие ключа и удали элемент из db
    # если ключа нет - raise HTTPException(status_code=404, detail="Item not found")
    pass


@app.put("/items/{item_id}", response_model=ItemInDB)
def update_item(item_id: int, item: Item, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # проверь наличие ключа в db
    # если нет - raise HTTPException(status_code=404, detail="Item not found")
    # обнови name и price у существующего элемента
    # верни обновлённый объект
    pass


@app.get("/stats")
def get_stats(authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # верни статистику: {"total_items": ..., "total_value": ...}
    # total_items — количество товаров в db
    # total_value — сумма цен всех товаров
    pass


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
    # TODO: верни все значения из users_db как список
    pass


@app.get("/users/{user_id}", response_model=UserInDB)
def get_user(user_id: int, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # проверь наличие ключа в users_db и верни значение
    # если ключа нет - raise HTTPException(status_code=404, detail="User not found")
    pass


@app.post("/users", response_model=UserInDB, status_code=201)
def create_user(user: User):
    # TODO: сгенерируй новый id (max ключ в users_db + 1)
    # создай UserInDB и добавь в users_db по ключу
    # верни созданный объект
    pass


@app.post("/login")
def login(login_req: LoginRequest):
    # TODO: найди пользователя по email в users_db
    # если не найден - raise HTTPException(status_code=401, detail="Invalid credentials")
    # проверь пароль (простое сравнение)
    # если неверный - raise HTTPException(status_code=401, detail="Invalid credentials")
    # верни {"access_token": email, "token_type": "bearer"}
    pass


@app.get("/me", response_model=UserInDB)
def get_current_user(email: str):
    # TODO: найди пользователя по email в query параметре
    # если не найден - raise HTTPException(status_code=404, detail="User not found")
    # верни найденного пользователя
    pass


# --- Корзина ---

class CartItem(BaseModel):
    item_id: int
    quantity: int


class CartItemInDB(CartItem):
    id: int


cart_db: dict[int, CartItemInDB] = {}


@app.get("/cart", response_model=list[CartItemInDB])
def get_cart(authorization: Optional[str] = Header(None)):
    # TODO: верни все значения из cart_db как список
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    pass


@app.post("/cart/items", response_model=CartItemInDB, status_code=201)
def add_to_cart(cart_item: CartItem, authorization: Optional[str] = Header(None)):
    # TODO: сгенерируй новый id (max ключ в cart_db + 1)
    # создай CartItemInDB и добавь в cart_db по ключу
    # верни созданный объект
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    pass


@app.delete("/cart/items/{cart_item_id}", status_code=204)
def remove_from_cart(cart_item_id: int, authorization: Optional[str] = Header(None)):
    # TODO: проверь наличие ключа в cart_db и удали элемент
    # если ключа нет - raise HTTPException(status_code=404, detail="Cart item not found")
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    pass


@app.get("/cart/total")
def get_cart_total(authorization: Optional[str] = Header(None)):
    # TODO: посчитай общую стоимость товаров в корзине
    # для каждого товара в cart_db найди цену в db
    # умножь на quantity и сложи всё вместе
    # верни {"total": ...}
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    pass
