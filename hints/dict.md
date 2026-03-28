# Шпаргалка: dict в Python

Краткий справочник по словарям.

---

## Создание

```python
db: dict[int, ItemInDB] = {}          # пустой словарь
db: dict[int, ItemInDB] = {1: item1}  # словарь с одним элементом

db = {}           # без аннотации - работает так же, но IDE не подсказывает
db = {1: item1}   # без аннотации - работает так же, но IDE не подсказывает
```

---

## Добавить элемент

```python
db[1] = ItemInDB(id=1, name="Мышь", price=1200)
```

---

## Обновить элемент

```python
if item_id in db:
    db[item_id].name = "Новое название"
    db[item_id].price = 9999
```

---

## Перебрать все элементы

```python
for item in db.values():
    print(item.id, item.name)
```

---

## Перебрать ключи и значения

```python
for key, value in db.items():
    print(key, value.id, value.name)
```

---

## Найти элемент по ключу (id)

```python
if item_id in db:
    return db[item_id]
```

---

## Удалить элемент по ключу

```python
if item_id in db:
    del db[item_id]
    return
```

---

## Узнать максимальный ключ (id)

```python
max(db.keys(), default=0)
# default=0 - если db пустой, вернёт 0, а не ошибку
```

---

## Количество элементов

```python
len(db)  # количество пар ключ-значение
```

---

## Получить элемент по ключу

```python
db[1]      # элемент с ключом 1
db.get(1)  # то же самое, но вернёт None если ключа нет
```

---

## Проверить наличие ключа

```python
if 1 in db:
    print("Ключ существует")
```

---

## Фильтрация элементов

```python
# Все товары дороже 50000
expensive = [item for item in db.values() if item.price >= 50000]

# Поиск по подстроке в названии (без учёта регистра)
found = [item for item in db.values() if "айфон" in item.name.lower()]
```

---

## Сумма значений

```python
# Общая стоимость всех товаров
total_value = sum(item.price for item in db.values())
```

---

## Ключ vs значение - важно

В этой задаче ключ словаря - это `id` товара:

```python
db = {
    1: ItemInDB(id=1, name="Ноутбук", price=89900),
    2: ItemInDB(id=2, name="Мышь",    price=1200),
}

db[1]      # доступ по ключу (id)
db[1].id   # → 1
db[1].name # → "Ноутбук"

# После удаления:
del db[1]
db[1]  # KeyError - ключ больше не существует
```

Ключ словаря обеспечивает быстрый доступ к элементу без перебора всех элементов.

---

## Несколько словарей в проекте

В реальном проекте могут быть разные словари для разных сущностей:

```python
# Товары
items_db: dict[int, ItemInDB] = {...}

# Пользователи
users_db: dict[int, UserInDB] = {...}

# Корзина
cart_db: dict[int, CartItemInDB] = {...}
```

Работа с ними одинаковая - используй те же операции dict.

---

## Флаг is_admin для разделения прав

```python
class User(BaseModel):
    name: str
    email: str
    password: str
    is_admin: bool = False  # False - обычный пользователь, True - админ

# Пример данных
users_db = {
    1: UserInDB(id=1, name="Админ", email="admin@shop.com", password="admin123", is_admin=True),
    2: UserInDB(id=2, name="Клиент", email="customer@shop.com", password="user123", is_admin=False),
}

# Проверка прав
def require_admin(user):
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
```

---

## Авторизация через заголовок

```python
from fastapi import Header

@app.post("/items")
def create_item(item: Item, authorization: Optional[str] = Header(None)):
    # Извлечь токен из заголовка "Bearer <email>"
    # Проверить пользователя и права
    pass
```

---

## Извлечение email из заголовка авторизации

Заголовок приходит в формате `"Bearer admin@shop.com"`:

```python
authorization = "Bearer admin@shop.com"

# Убрать префикс "Bearer " (7 символов)
email = authorization[7:]  # "admin@shop.com"

# Или через split
email = authorization.split(" ")[1]  # "admin@shop.com"
```

---

## Поиск пользователя по email (не по id)

В `users_db` ключ - это `id`, но нам нужно найти по `email`:

```python
def find_user_by_email(email: str):
    for user in users_db.values():  # перебираем все значения
        if user.email == email:
            return user  # нашли пользователя
    return None  # не нашли
```

Или через генератор:

```python
user = next((u for u in users_db.values() if u.email == email), None)
```

---

## Возврат токена из /login

Успешный ответ должен содержать токен:

```python
@app.post("/login")
def login(login_req: LoginRequest):
    # Нашли пользователя с таким email и паролем
    return {
        "access_token": user.email,
        "token_type": "bearer"
    }

# Пример ответа:
# {"access_token": "admin@shop.com", "token_type": "bearer"}
```

---

## Полный пример проверки авторизации

```python
@app.post("/items")
def create_item(item: Item, authorization: Optional[str] = Header(None)):
    # 1. Извлечь email из заголовка
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")
    
    email = authorization[7:]
    
    # 2. Найти пользователя по email
    user = None
    for u in users_db.values():
        if u.email == email:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # 3. Проверить, что пользователь - админ
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # 4. Создать товар (основная логика)
    new_id = max(db.keys(), default=0) + 1
    ...
```
