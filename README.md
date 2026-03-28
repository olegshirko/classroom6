# Практическая работа: REST API + Docker

Пишем простой REST API на FastAPI и запускаем его в Docker-контейнере.

---

## Структура проекта

```
classroom6/
├── main.py          # API - здесь весь твой код
├── Dockerfile       # описание образа
├── requirements.txt # зависимости Python
├── tests/           # тесты
│   └── test_main.py
└── hints/           # шпаргалки
    └── dict.md      # справочник по словарям
```

---

## REST API

### Задача

Реализовать REST API для магазина Apple-техники. В файле `main.py` уже есть:
- модели данных (`Item`, `ItemInDB`)
- словарь `db` с четырьмя товарами (Макбук, Айфон, Айпад, Эйрподс)

Тебе нужно:
1. Изучить шпаргалку `hints/dict.md` по работе со словарями в Python
2. Реализовать все 18 эндпоинтов вместо `pass`

### Что нужно реализовать

#### Товары

| Метод | URL | Что делает | Код ответа | Права |
|-------|-----|------------|------------|-------|
| GET | `/` | Проверка работоспособности | 200 | Все |
| GET | `/items` | Список всех товаров | 200 | Все |
| GET | `/items/{id}` | Один товар по id | 200 / 404 | Все |
| GET | `/items/search?name=...` | Поиск по названию | 200 | Все |
| GET | `/items/expensive?min_price=...` | Товары дороже цены | 200 | Все |
| POST | `/items` | Создать товар | 201 | Только админ |
| PUT | `/items/{id}` | Обновить товар | 200 / 404 | Только админ |
| DELETE | `/items/{id}` | Удалить товар | 204 / 404 | Только админ |
| GET | `/stats` | Статистика по товарам | 200 | Только админ |

#### Пользователи и аутентификация

| Метод | URL | Что делает | Код ответа | Права |
|-------|-----|------------|------------|-------|
| GET | `/users` | Список пользователей | 200 | Все |
| POST | `/users` | Создать пользователя | 201 | Все |
| POST | `/login` | Вход (получить токен) | 200 / 401 | Все |
| GET | `/me?email=...` | Текущий пользователь | 200 / 404 | Все |
| GET | `/users/{id}` | Один пользователь по id | 200 / 404 | Только админ |

#### Корзина

| Метод | URL | Что делает | Код ответа | Права |
|-------|-----|------------|------------|-------|
| GET | `/cart` | Содержимое корзины | 200 | Только авторизованный |
| POST | `/cart/items` | Добавить товар в корзину | 201 | Только авторизованный |
| DELETE | `/cart/items/{id}` | Удалить из корзины | 204 / 404 | Только авторизованный |
| GET | `/cart/total` | Общая стоимость корзины | 200 | Только авторизованный |

### Запуск

```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить
uvicorn main:app -reload
```

После запуска открой в браузере:
- `http://localhost:8000/items` - список товаров

### Проверка через curl

```bash
# === Авторизация ===

# Получить токен админа
curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@shop.com", "password": "admin123"}'
# Ответ: {"access_token": "admin@shop.com", "token_type": "bearer"}

# Получить токен клиента
curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/json" \
     -d '{"email": "customer@shop.com", "password": "user123"}'


# === Товары ===

# Получить все товары (открыто)
curl http://localhost:8000/items

# Получить один товар (открыто)
curl http://localhost:8000/items/1

# Создать товар (только админ)
curl -X POST http://localhost:8000/items \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer admin@shop.com" \
     -d '{"name": "Клавиатура", "price": 3500}'

# Обновить товар (только админ)
curl -X PUT http://localhost:8000/items/1 \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer admin@shop.com" \
     -d '{"name": "Макбук Про", "price": 199900}'

# Удалить товар (только админ)
curl -X DELETE http://localhost:8000/items/1 \
     -H "Authorization: Bearer admin@shop.com"

# Поиск товаров (открыто)
curl "http://localhost:8000/items/search?name=ай"

# Товары дороже 50000 (открыто)
curl "http://localhost:8000/items/expensive?min_price=50000"

# Статистика (только админ)
curl -H "Authorization: Bearer admin@shop.com" http://localhost:8000/stats


# === Пользователи ===

# Список пользователей (открыто)
curl http://localhost:8000/users

# Создать пользователя (открыто)
curl -X POST http://localhost:8000/users \
     -H "Content-Type: application/json" \
     -d '{"name": "Пётр", "email": "petr@example.com", "password": "pass123"}'

# Войти (получить токен)
curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@shop.com", "password": "admin123"}'

# Получить текущего пользователя
curl "http://localhost:8000/me?email=admin@shop.com"

# Получить пользователя по id (только админ)
curl -H "Authorization: Bearer admin@shop.com" http://localhost:8000/users/1


# === Корзина (только авторизованный) ===

# Получить содержимое корзины
curl -H "Authorization: Bearer customer@shop.com" http://localhost:8000/cart

# Добавить товар в корзину
curl -X POST http://localhost:8000/cart/items \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer customer@shop.com" \
     -d '{"item_id": 1, "quantity": 2}'

# Общая стоимость корзины
curl -H "Authorization: Bearer customer@shop.com" http://localhost:8000/cart/total

# Удалить товар из корзины
curl -X DELETE http://localhost:8000/cart/items/1 \
     -H "Authorization: Bearer customer@shop.com"


# === Ошибки ===

# Несуществующий товар - 404
curl http://localhost:8000/items/999

# Создание без авторизации - 401
curl -X POST http://localhost:8000/items \
     -H "Content-Type: application/json" \
     -d '{"name": "Товар", "price": 100}'

# Создание с токеном клиента - 403
curl -X POST http://localhost:8000/items \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer customer@shop.com" \
     -d '{"name": "Товар", "price": 100}'
```

### Запуск тестов

```bash
# Запустить все тесты
pytest tests/test_main.py -v

# Запустить один тест
pytest tests/test_main.py::test_healthcheck -v
```

---

## Docker

### Задача

Упаковать готовый API в Docker-образ и запустить его в контейнере.

### Шаг 1 - собери образ

```bash
docker build -t shop-api .
```

### Шаг 2 - запусти контейнер

```bash
docker run -d -p 8000:8000 shop-api
```

Проверь, что API работает: `http://localhost:8000/items`

### Шаг 3 - изучи базовые команды Docker

```bash
# Посмотреть запущенные контейнеры
docker ps

# Логи контейнера
docker logs <container_id>

# Зайти внутрь контейнера
docker exec -it <container_id> sh

# Найди, где лежит main.py
```

```bash
docker images
```

---

## Критерии приёма работы

**Задание 1 (REST API):**
- [ ] Все 18 эндпоинтов реализованы
- [ ] GET `/items/999` возвращает 404, а не 500
- [ ] POST `/items` без авторизации возвращает 401
- [ ] POST `/items` с токеном клиента возвращает 403
- [ ] POST `/items` с токеном админа возвращает 201
- [ ] DELETE `/items/{id}` с токеном админа возвращает 204
- [ ] PUT `/items/{id}` обновляет существующий товар
- [ ] Поиск `/items/search?name=...` работает без учёта регистра
- [ ] `/stats` возвращает правильную сумму всех товаров
- [ ] POST `/users` создаёт пользователя
- [ ] POST `/login` возвращает токен при верных данных
- [ ] POST `/login` возвращает 401 при неверных данных
- [ ] GET `/me?email=...` возвращает текущего пользователя
- [ ] GET `/cart` без авторизации возвращает 401
- [ ] Корзина: добавление, удаление, подсчёт суммы работают
- [ ] Все 60 тестов проходят
---
