from fastapi.testclient import TestClient
from main import app, db, ItemInDB, users_db, carts, wishlist, ratings, view_counts, search_history, users_by_email, CATEGORIES

client = TestClient(app)


def setup_function():
    db.clear()
    db[1] = ItemInDB(id=1, name="Макбук", price=189900, category="Ноутбуки")
    db[2] = ItemInDB(id=2, name="Айфон", price=99900, category="Телефоны")
    db[3] = ItemInDB(id=3, name="Айпад", price=69900, category="Планшеты")
    db[4] = ItemInDB(id=4, name="Эйрподс", price=19900, category="Аксессуары")

    from main import UserInDB
    users_db.clear()
    users_by_email.clear()
    users_db[1] = UserInDB(id=1, name="Админ", email="admin@shop.com", password="admin123", roles={"admin"})
    users_db[2] = UserInDB(id=2, name="Клиент", email="customer@shop.com", password="user123", roles={"customer"})
    users_by_email["admin@shop.com"] = users_db[1]
    users_by_email["customer@shop.com"] = users_db[2]

    carts.clear()
    wishlist.clear()
    ratings.clear()
    view_counts.clear()
    search_history.clear()


# --- healthcheck ---

def test_healthcheck():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- list_items ---

def test_list_items_returns_all():
    response = client.get("/items")
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_list_items_structure():
    response = client.get("/items")
    item = response.json()[0]
    assert "id" in item
    assert "name" in item
    assert "price" in item
    assert "category" in item


def test_list_items_filter_by_category():
    response = client.get("/items?category=Ноутбуки")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Макбук"


def test_list_items_filter_by_category_no_results():
    response = client.get("/items?category=Несуществующая")
    assert response.status_code == 200
    assert len(response.json()) == 0


# --- get_item ---

def test_get_item_exists():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Макбук"


def test_get_item_not_found():
    response = client.get("/items/999")
    assert response.status_code == 404


def test_get_item_increments_views():
    client.get("/items/1")
    client.get("/items/1")
    from main import view_counts
    assert view_counts[1] == 2


# --- create_item ---

def test_create_item_status_code():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Клавиатура", "price": 3500, "category": "Аксессуары"}, headers=headers)
    assert response.status_code == 201


def test_create_item_returns_created_object():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Клавиатура", "price": 3500, "category": "Аксессуары"}, headers=headers)
    data = response.json()
    assert data["name"] == "Клавиатура"
    assert data["price"] == 3500
    assert data["category"] == "Аксессуары"
    assert "id" in data


def test_create_item_appears_in_list():
    headers = {"Authorization": "Bearer admin@shop.com"}
    client.post("/items", json={"name": "Клавиатура", "price": 3500, "category": "Аксессуары"}, headers=headers)
    response = client.get("/items")
    names = [i["name"] for i in response.json()]
    assert "Клавиатура" in names


def test_create_item_id_is_unique():
    headers = {"Authorization": "Bearer admin@shop.com"}
    r1 = client.post("/items", json={"name": "Товар 1", "price": 100, "category": "Аксессуары"}, headers=headers)
    r2 = client.post("/items", json={"name": "Товар 2", "price": 200, "category": "Аксессуары"}, headers=headers)
    assert r1.json()["id"] != r2.json()["id"]


def test_create_item_missing_field():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Без цены"}, headers=headers)
    assert response.status_code == 422


def test_create_item_invalid_category():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Товар", "price": 100, "category": "Несуществующая"}, headers=headers)
    assert response.status_code == 400


# --- delete_item ---

def test_delete_item_status_code():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.delete("/items/1", headers=headers)
    assert response.status_code == 204


def test_delete_item_removed_from_list():
    headers = {"Authorization": "Bearer admin@shop.com"}
    client.delete("/items/1", headers=headers)
    response = client.get("/items/1")
    assert response.status_code == 404


def test_delete_item_not_found():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.delete("/items/999", headers=headers)
    assert response.status_code == 404


def test_delete_item_others_remain():
    headers = {"Authorization": "Bearer admin@shop.com"}
    client.delete("/items/1", headers=headers)
    response = client.get("/items/2")
    assert response.status_code == 200


# --- update_item ---

def test_update_item_status_code():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.put("/items/1", json={"name": "Макбук Про", "price": 199900, "category": "Ноутбуки"}, headers=headers)
    assert response.status_code == 200


def test_update_item_returns_updated():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.put("/items/1", json={"name": "Макбук Про", "price": 199900, "category": "Ноутбуки"}, headers=headers)
    data = response.json()
    assert data["name"] == "Макбук Про"
    assert data["price"] == 199900
    assert data["id"] == 1


def test_update_item_not_found():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.put("/items/999", json={"name": "Тест", "price": 100, "category": "Аксессуары"}, headers=headers)
    assert response.status_code == 404


def test_update_item_persists():
    headers = {"Authorization": "Bearer admin@shop.com"}
    client.put("/items/1", json={"name": "Макбук Про", "price": 199900, "category": "Ноутбуки"}, headers=headers)
    response = client.get("/items/1")
    assert response.json()["name"] == "Макбук Про"


def test_update_item_invalid_category():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.put("/items/1", json={"name": "Тест", "price": 100, "category": "Несуществующая"}, headers=headers)
    assert response.status_code == 400


# --- search_items ---

def test_search_items_found():
    response = client.get("/items/search?name=мак")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Макбук"


def test_search_items_not_found():
    response = client.get("/items/search?name=несуществующий")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_search_items_case_insensitive():
    response = client.get("/items/search?name=АЙФОН")
    assert len(response.json()) == 1


def test_search_items_multiple():
    response = client.get("/items/search?name=ай")
    assert len(response.json()) == 2  # Айфон, Айпад


# --- get_expensive_items ---

def test_expensive_items_some_found():
    response = client.get("/items/expensive?min_price=50000")
    assert response.status_code == 200
    assert len(response.json()) == 3  # Макбук, Айфон, Айпад


def test_expensive_items_all_found():
    response = client.get("/items/expensive?min_price=10000")
    assert len(response.json()) == 4


def test_expensive_items_none_found():
    response = client.get("/items/expensive?min_price=500000")
    assert len(response.json()) == 0


# --- get_stats ---

def test_stats_total_items():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.get("/stats", headers=headers)
    assert response.status_code == 200
    assert response.json()["total_items"] == 4


def test_stats_total_value():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.get("/stats", headers=headers)
    data = response.json()
    # 189900 + 99900 + 69900 + 19900 = 379600
    assert data["total_value"] == 379600


def test_stats_structure():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.get("/stats", headers=headers)
    data = response.json()
    assert "total_items" in data
    assert "total_value" in data


# --- Категории ---

def test_get_categories():
    response = client.get("/categories")
    assert response.status_code == 200
    data = response.json()
    assert "Ноутбуки" in data
    assert "Телефоны" in data
    assert "Планшеты" in data
    assert "Аксессуары" in data
    assert len(data) == 4


# --- Популярные товары ---

def test_popular_items_empty_initially():
    response = client.get("/items/popular")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_popular_items_with_views():
    # Просматриваем товары
    client.get("/items/1")
    client.get("/items/1")
    client.get("/items/2")
    response = client.get("/items/popular")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Макбук"  # больше просмотров


# --- Рейтинг ---

def test_rate_item():
    response = client.post("/items/1/rate", json={"score": 5})
    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == 1
    assert data["score"] == 5
    assert data["average"] == 5.0


def test_rate_item_not_found():
    response = client.post("/items/999/rate", json={"score": 5})
    assert response.status_code == 404


def test_rate_item_invalid_score():
    response = client.post("/items/1/rate", json={"score": 6})
    assert response.status_code == 400


def test_get_item_rating_empty():
    response = client.get("/items/1/rating")
    assert response.status_code == 200
    assert response.json()["average"] == 0
    assert response.json()["count"] == 0


def test_get_item_rating_with_scores():
    client.post("/items/1/rate", json={"score": 5})
    client.post("/items/1/rate", json={"score": 3})
    response = client.get("/items/1/rating")
    assert response.status_code == 200
    assert response.json()["average"] == 4.0
    assert response.json()["count"] == 2


# --- Пользователи ---

def test_list_users():
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_user_exists():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.get("/users/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Админ"


def test_get_user_not_found():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.get("/users/999", headers=headers)
    assert response.status_code == 404


def test_create_user():
    response = client.post("/users", json={"name": "Пётр", "email": "petr@example.com", "password": "pass123"})
    assert response.status_code == 201
    assert response.json()["name"] == "Пётр"


def test_create_user_duplicate_email():
    client.post("/users", json={"name": "Пётр", "email": "petr@example.com", "password": "pass123"})
    response = client.post("/users", json={"name": "Пётр 2", "email": "petr@example.com", "password": "pass456"})
    assert response.status_code == 400


def test_create_user_with_roles():
    response = client.post("/users", json={"name": "Модератор", "email": "mod@shop.com", "password": "mod123", "roles": ["moderator", "customer"]})
    assert response.status_code == 201
    data = response.json()
    assert "moderator" in data["roles"]
    assert "customer" in data["roles"]


# --- Аутентификация ---

def test_login_admin():
    response = client.post("/login", json={"email": "admin@shop.com", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "admin@shop.com"
    assert data["token_type"] == "bearer"


def test_login_customer():
    response = client.post("/login", json={"email": "customer@shop.com", "password": "user123"})
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "customer@shop.com"


def test_login_wrong_email():
    response = client.post("/login", json={"email": "unknown@example.com", "password": "admin123"})
    assert response.status_code == 401


def test_login_wrong_password():
    response = client.post("/login", json={"email": "admin@shop.com", "password": "wrongpass"})
    assert response.status_code == 401


def test_get_current_user():
    response = client.get("/me?email=admin@shop.com")
    assert response.status_code == 200
    assert response.json()["name"] == "Админ"


def test_get_current_user_not_found():
    response = client.get("/me?email=unknown@example.com")
    assert response.status_code == 404


# --- Авторизация ---

def test_create_item_no_auth():
    response = client.post("/items", json={"name": "Товар", "price": 100, "category": "Аксессуары"})
    assert response.status_code == 401


def test_create_item_customer_forbidden():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.post("/items", json={"name": "Товар", "price": 100, "category": "Аксессуары"}, headers=headers)
    assert response.status_code == 403


def test_create_item_admin_success():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Товар", "price": 100, "category": "Аксессуары"}, headers=headers)
    assert response.status_code == 201


def test_delete_item_no_auth():
    response = client.delete("/items/1")
    assert response.status_code == 401


def test_delete_item_customer_forbidden():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.delete("/items/1", headers=headers)
    assert response.status_code == 403


def test_delete_item_admin_success():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.delete("/items/1", headers=headers)
    assert response.status_code == 204


def test_get_stats_no_auth():
    response = client.get("/stats")
    assert response.status_code == 401


def test_get_stats_admin_success():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.get("/stats", headers=headers)
    assert response.status_code == 200


# --- Корзина (привязана к email) ---

def test_get_cart_no_auth():
    response = client.get("/cart")
    assert response.status_code == 401


def test_get_cart_with_auth():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.get("/cart", headers=headers)
    assert response.status_code == 200


def test_add_to_cart_no_auth():
    response = client.post("/cart/items", json={"item_id": 1, "quantity": 1})
    assert response.status_code == 401


def test_add_to_cart_with_auth():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.post("/cart/items", json={"item_id": 1, "quantity": 1}, headers=headers)
    assert response.status_code == 201


def test_get_cart_total_no_auth():
    response = client.get("/cart/total")
    assert response.status_code == 401


def test_get_cart_total_with_auth():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.get("/cart/total", headers=headers)
    assert response.status_code == 200


def test_get_cart_empty():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.get("/cart", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_add_to_cart():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.post("/cart/items", json={"item_id": 1, "quantity": 2}, headers=headers)
    assert response.status_code == 201
    assert response.json()["item_id"] == 1
    assert response.json()["quantity"] == 2


def test_add_to_cart_appears_in_list():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/cart/items", json={"item_id": 1, "quantity": 1}, headers=headers)
    response = client.get("/cart", headers=headers)
    assert len(response.json()) == 1


def test_add_to_cart_same_item_twice():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/cart/items", json={"item_id": 1, "quantity": 2}, headers=headers)
    client.post("/cart/items", json={"item_id": 1, "quantity": 3}, headers=headers)
    response = client.get("/cart", headers=headers)
    assert len(response.json()) == 1
    assert response.json()[0]["quantity"] == 5


def test_remove_from_cart():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/cart/items", json={"item_id": 1, "quantity": 1}, headers=headers)
    response = client.get("/cart", headers=headers)
    # item_id в корзине совпадает с ID товара
    client.delete("/cart/items/1", headers=headers)
    response = client.get("/cart", headers=headers)
    assert len(response.json()) == 0


def test_remove_from_cart_not_found():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.delete("/cart/items/999", headers=headers)
    assert response.status_code == 404


def test_cart_total_empty():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.get("/cart/total", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_cart_total_with_items():
    # Добавляем 2 товара по цене 189900 (Макбук)
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/cart/items", json={"item_id": 1, "quantity": 2}, headers=headers)
    response = client.get("/cart/total", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 379800  # 189900 * 2


def test_cart_total_multiple_items():
    # Макбук (189900) * 1 + Айфон (99900) * 2 = 189900 + 199800 = 389700
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/cart/items", json={"item_id": 1, "quantity": 1}, headers=headers)
    client.post("/cart/items", json={"item_id": 2, "quantity": 2}, headers=headers)
    response = client.get("/cart/total", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 389700


def test_cart_separate_per_user():
    # Добавляем товар в корзину клиента
    customer_headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/cart/items", json={"item_id": 1, "quantity": 1}, headers=customer_headers)

    # Корзина админа пуста
    admin_headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.get("/cart", headers=admin_headers)
    assert len(response.json()) == 0


# --- Избранное ---

def test_add_to_wishlist():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.post("/wishlist/add/1", headers=headers)
    assert response.status_code == 201
    assert response.json()["item_id"] == 1


def test_add_to_wishlist_not_found():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.post("/wishlist/add/999", headers=headers)
    assert response.status_code == 404


def test_add_to_wishlist_no_auth():
    response = client.post("/wishlist/add/1")
    assert response.status_code == 401


def test_get_wishlist():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/wishlist/add/1", headers=headers)
    client.post("/wishlist/add/2", headers=headers)
    response = client.get("/wishlist", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_wishlist_empty():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.get("/wishlist", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_wishlist_no_auth():
    response = client.get("/wishlist")
    assert response.status_code == 401


def test_remove_from_wishlist():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/wishlist/add/1", headers=headers)
    client.delete("/wishlist/remove/1", headers=headers)
    response = client.get("/wishlist", headers=headers)
    assert len(response.json()) == 0


def test_remove_from_wishlist_not_found():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.delete("/wishlist/remove/1", headers=headers)
    assert response.status_code == 404


def test_wishlist_no_duplicates():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/wishlist/add/1", headers=headers)
    client.post("/wishlist/add/1", headers=headers)
    response = client.get("/wishlist", headers=headers)
    assert len(response.json()) == 1


# --- История поиска ---

def test_search_with_history():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.get("/items/search/with-history?name=мак", headers=headers)
    response = client.get("/items/search/history", headers=headers)
    assert response.status_code == 200
    assert "мак" in response.json()


def test_search_history_no_auth():
    response = client.get("/items/search/history")
    assert response.status_code == 401


def test_search_history_empty():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.get("/items/search/history", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_search_with_history_saves_multiple():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.get("/items/search/with-history?name=мак", headers=headers)
    client.get("/items/search/with-history?name=ай", headers=headers)
    response = client.get("/items/search/history", headers=headers)
    assert len(response.json()) == 2
    assert response.json()[0] == "мак"
    assert response.json()[1] == "ай"


def test_search_with_history_returns_results():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.get("/items/search/with-history?name=мак", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Макбук"
