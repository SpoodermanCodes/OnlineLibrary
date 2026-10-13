"""Automated tests (Pytest). Run: python -m pytest test_app.py -v"""
import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "test.db")})
    return app.test_client()


def test_home_page_loads(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Online Library" in res.data


def test_health_endpoint(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_books_are_seeded(client):
    books = client.get("/api/books").get_json()
    assert len(books) >= 10


def test_search_by_title_and_author(client):
    assert any("Clean Code" == b["title"] for b in client.get("/api/books?search=clean").get_json())
    assert all("gene kim" in b["author"].lower() for b in client.get("/api/books?search=gene%20kim").get_json())


def test_filter_by_category(client):
    books = client.get("/api/books?category=DevOps").get_json()
    assert books and all(b["category"] == "DevOps" for b in books)


def test_rent_book_reduces_stock_and_creates_rental(client):
    book = client.get("/api/books?search=clean").get_json()[0]
    res = client.post("/api/rent", json={"member_name": "Asha", "member_id": "L1",
                                         "days": 5, "book_ids": [book["id"]]})
    assert res.status_code == 201
    data = res.get_json()
    assert data["rental_id"].startswith("RNT-")
    assert data["total_amount"] == book["price_per_day"] * 5
    after = client.get("/api/books?search=clean").get_json()[0]
    assert after["available_copies"] == book["available_copies"] - 1


def test_rent_requires_member_details(client):
    res = client.post("/api/rent", json={"member_name": "", "member_id": "", "days": 3, "book_ids": [1]})
    assert res.status_code == 400


def test_rent_rejects_invalid_days(client):
    res = client.post("/api/rent", json={"member_name": "A", "member_id": "1", "days": 99, "book_ids": [1]})
    assert res.status_code == 400


def test_cannot_rent_out_of_stock_book(client):
    client.post("/api/books", json={"title": "Rare", "author": "X", "category": "Misc",
                                    "copies": 1, "price_per_day": 5})
    rare = client.get("/api/books?search=rare").get_json()[0]
    ok = client.post("/api/rent", json={"member_name": "A", "member_id": "1", "days": 2, "book_ids": [rare["id"]]})
    assert ok.status_code == 201
    again = client.post("/api/rent", json={"member_name": "B", "member_id": "2", "days": 2, "book_ids": [rare["id"]]})
    assert again.status_code == 409


def test_return_restores_stock_and_marks_returned(client):
    book = client.get("/api/books?search=alchemist").get_json()[0]
    rid = client.post("/api/rent", json={"member_name": "A", "member_id": "1", "days": 3,
                                         "book_ids": [book["id"]]}).get_json()["rental_id"]
    res = client.post(f"/api/rentals/{rid}/return")
    assert res.status_code == 200 and res.get_json()["fine"] == 0
    assert client.get("/api/books?search=alchemist").get_json()[0]["available_copies"] == book["available_copies"]
    assert client.post(f"/api/rentals/{rid}/return").status_code == 409   # already returned


def test_overdue_return_charges_fine(client, tmp_path):
    import sqlite3
    book = client.get("/api/books?search=alchemist").get_json()[0]
    rid = client.post("/api/rent", json={"member_name": "A", "member_id": "1", "days": 3,
                                         "book_ids": [book["id"]]}).get_json()["rental_id"]
    db = sqlite3.connect(str(tmp_path / "test.db"))
    db.execute("UPDATE rentals SET due_on = date('now','-4 day') WHERE rental_id = ?", (rid,))
    db.commit(); db.close()
    data = client.post(f"/api/rentals/{rid}/return").get_json()
    assert data["late_days"] == 4 and data["fine"] == 8.0   # 4 days x Rs.2 x 1 book


def test_admin_dashboard_and_stats(client):
    assert client.get("/admin").status_code == 200
    stats = client.get("/api/stats").get_json()
    assert {"titles", "available", "active_rentals", "revenue"} <= set(stats)
