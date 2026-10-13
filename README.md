# Online Library & Book Rental System

A web-based library where members browse/search books, add them to a rental cart and rent them for a chosen
period; admins track rentals, process returns (with late fines) and manage inventory.
Built with **Flask + SQLite** and delivered through a **DevOps pipeline**:

`GitHub → Jenkins → Docker Build → Pytest → Ansible → Docker Container → Flask → SQLite (Docker Volume)`

## Features
- Browse, search (title/author) and filter by category
- Rental cart, rental period (1-30 days), automatic rent calculation, rental ID (`RNT-XXXXXXXX`)
- Stock tracking (copies reduce on rent, restore on return)
- Admin dashboard: stats, rental records, mark returned (fine = Rs.2/day/book overdue), add/delete books

## Run locally
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                                        # http://localhost:5000
python -m pytest test_app.py -v                      # run tests
```

## Run with Docker
```bash
docker build -t online-library-ci .
docker run -d -p 5001:5000 -v library_data:/app/data --name online-library online-library-ci
```
Open http://localhost:5001 (admin: http://localhost:5001/admin).

## CI/CD
See `Jenkinsfile`, `ansible/docker-deploy.yml` and `docker-compose.lab.yml`.

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/books?search=&category=` | list/search books |
| POST | `/api/books` | add book |
| DELETE | `/api/books/<id>` | delete book |
| POST | `/api/rent` | create rental |
| GET | `/api/rentals` | all rentals |
| POST | `/api/rentals/<rental_id>/return` | return books |
| GET | `/api/stats` | dashboard numbers |
| GET | `/health` | health check |
