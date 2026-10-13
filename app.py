"""Online Library & Book Rental System - Flask backend.

Frontend (HTML/CSS/JS) talks to this JSON API. Data lives in SQLite
(data/library.db), which is mounted from a Docker volume in deployment.
"""
import os
import sqlite3
import uuid
from datetime import date, timedelta

from flask import Flask, g, jsonify, render_template, request

FINE_PER_DAY = 2.5          # fine per overdue day per book (Rs.)
MAX_RENT_DAYS = 30

SEED_BOOKS = [
    ("Clean Code", "Robert C. Martin", "Programming", 4, 5.0),
    ("The Pragmatic Programmer", "Andrew Hunt", "Programming", 3, 5.0),
    ("Introduction to Algorithms", "Thomas H. Cormen", "Computer Science", 2, 6.0),
    ("Operating System Concepts", "Abraham Silberschatz", "Computer Science", 3, 5.0),
    ("The DevOps Handbook", "Gene Kim", "DevOps", 3, 6.0),
    ("The Phoenix Project", "Gene Kim", "DevOps", 2, 4.0),
    ("Wings of Fire", "A. P. J. Abdul Kalam", "Biography", 5, 3.0),
    ("The Story of My Experiments with Truth", "M. K. Gandhi", "Biography", 3, 3.0),
    ("Sapiens", "Yuval Noah Harari", "History", 4, 4.0),
    ("The Discovery of India", "Jawaharlal Nehru", "History", 2, 4.0),
    ("The Alchemist", "Paulo Coelho", "Fiction", 5, 3.0),
    ("To Kill a Mockingbird", "Harper Lee", "Fiction", 3, 3.0),
    ("Atomic Habits", "James Clear", "Self Help", 4, 4.0),
    ("Deep Work", "Cal Newport", "Self Help", 2, 4.0),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT NOT NULL,
    total_copies INTEGER NOT NULL,
    available_copies INTEGER NOT NULL,
    price_per_day REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS rentals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rental_id TEXT UNIQUE NOT NULL,
    member_name TEXT NOT NULL,
    member_id TEXT NOT NULL,
    rented_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT,
    days INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    fine REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS rental_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rental_id TEXT NOT NULL,
    book_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    price REAL NOT NULL
);
"""


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = os.environ.get(
        "LIBRARY_DB", os.path.join(os.path.dirname(__file__), "data", "library.db")
    )
    if test_config:
        app.config.update(test_config)

    # ---------- database helpers ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        os.makedirs(os.path.dirname(os.path.abspath(app.config["DB_PATH"])), exist_ok=True)
        db = sqlite3.connect(app.config["DB_PATH"])
        db.executescript(SCHEMA)
        if db.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO books (title, author, category, total_copies, "
                "available_copies, price_per_day) VALUES (?,?,?,?,?,?)",
                [(t, a, c, n, n, p) for t, a, c, n, p in SEED_BOOKS],
            )
        db.commit()
        db.close()

    init_db()

    # ---------- pages ----------
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/admin")
    def admin():
        return render_template("admin.html")

    @app.route("/health")
    def health():
        return jsonify(status="ok")

    # ---------- books ----------
    @app.route("/api/books")
    def list_books():
        search = request.args.get("search", "").strip().lower()
        category = request.args.get("category", "").strip()
        sql, params = "SELECT * FROM books WHERE 1=1", []
        if search:
            sql += " AND (LOWER(title) LIKE ? OR LOWER(author) LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if category and category != "All":
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY title"
        rows = get_db().execute(sql, params).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/categories")
    def categories():
        rows = get_db().execute("SELECT DISTINCT category FROM books ORDER BY category").fetchall()
        return jsonify(["All"] + [r["category"] for r in rows])

    @app.route("/api/books", methods=["POST"])
    def add_book():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        author = str(data.get("author", "")).strip()
        category = str(data.get("category", "")).strip()
        try:
            copies = int(data.get("copies", 0))
            price = float(data.get("price_per_day", 0))
        except (TypeError, ValueError):
            return jsonify(error="copies and price_per_day must be numbers"), 400
        if not (title and author and category) or copies < 1 or price <= 0:
            return jsonify(error="title, author, category, copies>=1 and price>0 are required"), 400
        db = get_db()
        cur = db.execute(
            "INSERT INTO books (title, author, category, total_copies, available_copies, "
            "price_per_day) VALUES (?,?,?,?,?,?)",
            (title, author, category, copies, copies, price),
        )
        db.commit()
        return jsonify(id=cur.lastrowid, message="Book added"), 201

    @app.route("/api/books/<int:book_id>", methods=["DELETE"])
    def delete_book(book_id):
        db = get_db()
        active = db.execute(
            "SELECT COUNT(*) FROM rental_items ri JOIN rentals r ON r.rental_id = ri.rental_id "
            "WHERE ri.book_id = ? AND r.status = 'ACTIVE'", (book_id,)).fetchone()[0]
        if active:
            return jsonify(error="Book is currently rented out"), 409
        db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        db.commit()
        return jsonify(message="Book deleted")

    # ---------- rentals ----------
    @app.route("/api/rent", methods=["POST"])
    def rent():
        data = request.get_json(silent=True) or {}
        member_name = str(data.get("member_name", "")).strip()
        member_id = str(data.get("member_id", "")).strip()
        book_ids = data.get("book_ids") or []
        try:
            days = int(data.get("days", 7))
        except (TypeError, ValueError):
            return jsonify(error="days must be a number"), 400

        if not member_name or not member_id:
            return jsonify(error="Member name and member ID are required"), 400
        if not isinstance(book_ids, list) or not book_ids:
            return jsonify(error="Select at least one book"), 400
        if not 1 <= days <= MAX_RENT_DAYS:
            return jsonify(error=f"Rental period must be 1-{MAX_RENT_DAYS} days"), 400

        db = get_db()
        books = []
        for bid in dict.fromkeys(book_ids):          # de-duplicate, keep order
            book = db.execute("SELECT * FROM books WHERE id = ?", (bid,)).fetchone()
            if book is None:
                return jsonify(error=f"Book {bid} not found"), 404
            if book["available_copies"] < 1:
                return jsonify(error=f"'{book['title']}' is not available"), 409
            books.append(book)

        today = date.today()
        due = today + timedelta(days=days)
        total = round(sum(b["price_per_day"] for b in books) * days, 2)
        rental_id = "RNT-" + uuid.uuid4().hex[:8].upper()

        db.execute(
            "INSERT INTO rentals (rental_id, member_name, member_id, rented_on, due_on, "
            "days, total_amount) VALUES (?,?,?,?,?,?,?)",
            (rental_id, member_name, member_id, today.isoformat(), due.isoformat(), days, total),
        )
        for b in books:
            db.execute(
                "INSERT INTO rental_items (rental_id, book_id, title, price) VALUES (?,?,?,?)",
                (rental_id, b["id"], b["title"], b["price_per_day"] * days),
            )
            db.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (b["id"],))
        db.commit()
        return jsonify(rental_id=rental_id, due_on=due.isoformat(), total_amount=total,
                       books=[b["title"] for b in books]), 201

    @app.route("/api/rentals")
    def list_rentals():
        db = get_db()
        rows = db.execute("SELECT * FROM rentals ORDER BY id DESC").fetchall()
        out = []
        for r in rows:
            item = dict(r)
            item["books"] = [i["title"] for i in db.execute(
                "SELECT title FROM rental_items WHERE rental_id = ?", (r["rental_id"],))]
            if r["status"] == "ACTIVE" and date.fromisoformat(r["due_on"]) < date.today():
                item["overdue"] = True
            out.append(item)
        return jsonify(out)

    @app.route("/api/rentals/<rental_id>/return", methods=["POST"])
    def return_rental(rental_id):
        db = get_db()
        rental = db.execute("SELECT * FROM rentals WHERE rental_id = ?", (rental_id,)).fetchone()
        if rental is None:
            return jsonify(error="Rental not found"), 404
        if rental["status"] != "ACTIVE":
            return jsonify(error="Rental already returned"), 409

        items = db.execute("SELECT book_id FROM rental_items WHERE rental_id = ?", (rental_id,)).fetchall()
        late_days = max(0, (date.today() - date.fromisoformat(rental["due_on"])).days)
        fine = round(late_days * FINE_PER_DAY * len(items), 2)
        for it in items:
            db.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = ?", (it["book_id"],))
        db.execute(
            "UPDATE rentals SET status='RETURNED', returned_on=?, fine=? WHERE rental_id=?",
            (date.today().isoformat(), fine, rental_id),
        )
        db.commit()
        return jsonify(message="Returned", late_days=late_days, fine=fine)

    @app.route("/api/stats")
    def stats():
        db = get_db()
        one = lambda q: db.execute(q).fetchone()[0]
        return jsonify(
            titles=one("SELECT COUNT(*) FROM books"),
            available=one("SELECT COALESCE(SUM(available_copies),0) FROM books"),
            active_rentals=one("SELECT COUNT(*) FROM rentals WHERE status='ACTIVE'"),
            revenue=round(one("SELECT COALESCE(SUM(total_amount + fine),0) FROM rentals"), 2),
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
