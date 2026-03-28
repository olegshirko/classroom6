from fastapi.testclient import TestClient
from main import app, db, ItemInDB, users_db, cart_db, UserInDB

client = TestClient(app)


def setup_function():
    db.clear()
    db[1] = ItemInDB(id=1, name="Макбук", price=189900)
    db[2] = ItemInDB(id=2, name="Айфон", price=99900)
    db[3] = ItemInDB(id=3, name="Айпад", price=69900)
    db[4] = ItemInDB(id=4, name="Эйрподс", price=19900)
    
    users_db.clear()
    users_db[1] = UserInDB(id=1, name="Админ", email="admin@shop.com", password="admin123", is_admin=True)
    users_db[2] = UserInDB(id=2, name="Клиент", email="customer@shop.com", password="user123", is_admin=False)
    
    cart_db.clear()


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


# --- get_item ---

def test_get_item_exists():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Макбук"


def test_get_item_not_found():
    response = client.get("/items/999")
    assert response.status_code == 404


# --- create_item ---

def test_create_item_status_code():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Клавиатура", "price": 3500}, headers=headers)
    assert response.status_code == 201


def test_create_item_returns_created_object():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Клавиатура", "price": 3500}, headers=headers)
    data = response.json()
    assert data["name"] == "Клавиатура"
    assert data["price"] == 3500
    assert "id" in data


def test_create_item_appears_in_list():
    headers = {"Authorization": "Bearer admin@shop.com"}
    client.post("/items", json={"name": "Клавиатура", "price": 3500}, headers=headers)
    response = client.get("/items")
    names = [i["name"] for i in response.json()]
    assert "Клавиатура" in names


def test_create_item_id_is_unique():
    headers = {"Authorization": "Bearer admin@shop.com"}
    r1 = client.post("/items", json={"name": "Товар 1", "price": 100}, headers=headers)
    r2 = client.post("/items", json={"name": "Товар 2", "price": 200}, headers=headers)
    assert r1.json()["id"] != r2.json()["id"]


def test_create_item_missing_field():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Без цены"}, headers=headers)
    assert response.status_code == 422


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
    response = client.put("/items/1", json={"name": "Макбук Про", "price": 199900}, headers=headers)
    assert response.status_code == 200


def test_update_item_returns_updated():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.put("/items/1", json={"name": "Макбук Про", "price": 199900}, headers=headers)
    data = response.json()
    assert data["name"] == "Макбук Про"
    assert data["price"] == 199900
    assert data["id"] == 1


def test_update_item_not_found():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.put("/items/999", json={"name": "Тест", "price": 100}, headers=headers)
    assert response.status_code == 404


def test_update_item_persists():
    headers = {"Authorization": "Bearer admin@shop.com"}
    client.put("/items/1", json={"name": "Макбук Про", "price": 199900}, headers=headers)
    response = client.get("/items/1")
    assert response.json()["name"] == "Макбук Про"


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
    response = client.post("/items", json={"name": "Товар", "price": 100})
    assert response.status_code == 401


def test_create_item_customer_forbidden():
    headers = {"Authorization": "Bearer customer@shop.com"}
    response = client.post("/items", json={"name": "Товар", "price": 100}, headers=headers)
    assert response.status_code == 403


def test_create_item_admin_success():
    headers = {"Authorization": "Bearer admin@shop.com"}
    response = client.post("/items", json={"name": "Товар", "price": 100}, headers=headers)
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


# --- Корзина ---

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


def test_remove_from_cart():
    headers = {"Authorization": "Bearer customer@shop.com"}
    client.post("/cart/items", json={"item_id": 1, "quantity": 1}, headers=headers)
    response = client.get("/cart", headers=headers)
    cart_item_id = response.json()[0]["id"]
    client.delete(f"/cart/items/{cart_item_id}", headers=headers)
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