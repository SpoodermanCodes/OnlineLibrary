# Step-by-Step Guide: Online Library & Book Rental System (DevOps Project)

This replicates everything in the sample report (Digital Canteen) for your project.

**Pipeline:** `GitHub → Jenkins → Docker Build → Pytest → Ansible → Docker Container → Flask → SQLite (Docker Volume)`

| Sample report (Digital Canteen) | Your project (Online Library) |
|---|---|
| Image `digital-canteen-ci` | Image `online-library-ci` |
| Container `digital-canteen-ansible` | Container `online-library-ansible` |
| Volume `canteen_data` → `/app/data` | Volume `library_data` → `/app/data` |
| DB `data/canteen.db`, table `orders` | DB `data/library.db`, tables `books`, `rentals`, `rental_items` |
| Port `5001 → 5000` | Port `5001 → 5000` |
| Jenkins on `localhost:9091` | Jenkins on `localhost:9091` |
| Ansible container `ansible-docker-lab` | Ansible container `ansible-docker-lab` |

Marks scheme in your evaluation sheet → where it is covered here: Planning (Step 1) · Git (Steps 3-4) · Branching/merging (Step 4) · App build (Step 2) · Jenkins (Step 8) · Docker (Step 6) · Ansible (Step 7) · Testing (Step 5) · Documentation (Step 10) · Demo/viva (Step 11).

---

## Step 0 – Prerequisites (install once)
- Git, Python 3.11+, Docker Desktop (or Docker Engine), a GitHub account, VS Code.
- Verify: `git --version`, `python --version`, `docker --version`, `docker ps`.

## Step 1 – Planning (10 marks)
Write these in your report's Introduction/Objectives/Abstract:
- **Problem:** manual library registers → slow lookups, lost records, hard to track due dates/fines.
- **Solution:** web app to browse/search/rent books + admin dashboard + DevOps automation.
- **Modules** (use these as your report's Module 1-12):
  1. User Interface & Book Browsing (HTML/CSS/JS)
  2. Flask Backend & Rental Management
  3. SQLite Database Management
  4. Git & GitHub Source Control
  5. Docker Containerization
  6. Jenkins CI/CD Pipeline
  7. Automated Testing (Pytest)
  8. Ansible Deployment
  9. Persistent Storage (Docker Volume)
  10. Admin & Rental Management (returns, fines, inventory)
  11. CI/CD Integration
  12. Application & Deployment Verification
- **Tech stack table:** HTML5, CSS3, JavaScript ES6, Python 3.11, Flask 3.0.0, SQLite 3, Git, GitHub, Jenkins, Docker, Pytest 8.3.5, Ansible, community.docker. (Put real versions from `docker --version`, Jenkins "About", `docker exec ansible-docker-lab ansible --version`.)
- **Architecture diagram:** draw boxes in the order of the pipeline above (draw.io / PowerPoint).

## Step 2 – Create the application (15 marks)
```bash
mkdir OnlineLibrary && cd OnlineLibrary
```
Copy in the project files provided (`app.py`, `templates/`, `static/`, `requirements.txt`, `test_app.py`, `Dockerfile`, `Jenkinsfile`, `ansible/`, `jenkins/`, `docker-compose.lab.yml`, `.gitignore`, `.dockerignore`, `README.md`).

Run it locally first:
```bash
python -m venv venv
venv\Scripts\activate            # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000 → browse, search, add to cart, rent. Open http://localhost:5000/admin → see the rental, mark returned.
**Screenshots:** home page (Fig 7.1), cart + rental confirmation (Fig 7.2), Flask code in VS Code (Fig 7.3), the DB opened in "DB Browser for SQLite" (Fig 7.4), admin dashboard (Fig 7.13).

## Step 3 – Git & GitHub (15 marks)
1. On github.com create a repo named `OnlineLibrary` (public, no README).
2. Locally:
```bash
git init
git status
git add .
git commit -m "Initial commit: Flask library app with rental cart and admin dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/OnlineLibrary.git
git push -u origin main
```
(Use a Personal Access Token as the password: GitHub → Settings → Developer settings → Tokens.)
3. Later practise `git pull origin main`, `git fetch`, `git log --oneline --graph`.
**Screenshot:** the GitHub repository page (Fig 7.5).

## Step 4 – Branching, merging, conflict (10 marks)
Do real, meaningful work on branches (examiners look at the history).
```bash
# Feature 1: late-fine display
git checkout -b feature/fine-calculation
# edit app.py (e.g. change FINE_PER_DAY) ...
git add . && git commit -m "feat: add late-return fine calculation"
git push -u origin feature/fine-calculation

# Feature 2: UI tweak (parallel branch from main)
git checkout main
git checkout -b feature/ui-improvements
# edit static/style.css ...
git add . && git commit -m "style: improve book card layout"

# Merge both
git checkout main
git merge feature/fine-calculation
git merge feature/ui-improvements
git push origin main
```
**Create a conflict on purpose** (to demonstrate handling): change the same line (e.g. `MAX_RENT_DAYS`) in `app.py` on two branches with different values, merge both, then:
```bash
git status                # shows "both modified"
# open app.py, keep the correct value, delete the <<<<<<< ======= >>>>>>> markers
git add app.py
git commit -m "fix: resolve merge conflict in MAX_RENT_DAYS"
git log --oneline --graph --all
```
**Screenshot:** `git log --oneline --graph --all` and GitHub's branches page.

## Step 5 – Automated testing (5 marks)
```bash
python -m pytest test_app.py -v
```
Expected: `12 passed`. (The project includes 12 tests: home page, health, seed data, search, category filter, rent, validation, out-of-stock, return, fine, admin/stats.)
**Screenshot:** the green pytest output (Fig 7.10). For "error identification and corrective action", deliberately break a test once (e.g. change an expected value), show the red failure, fix it, show green – write that in your Troubleshooting section.

## Step 6 – Docker (10 marks)
```bash
docker build -t online-library-ci .
docker images
docker run --rm online-library-ci python -m pytest test_app.py       # tests inside the image
docker run -d -p 5001:5000 -v library_data:/app/data --name online-library online-library-ci
docker ps
docker logs online-library
```
Open http://localhost:5001. Rent a book, then prove persistence:
```bash
docker rm -f online-library
docker run -d -p 5001:5000 -v library_data:/app/data --name online-library online-library-ci
# the rental you made is still in /admin
docker volume ls
docker volume inspect library_data
```
Then remove this manual container (Ansible will manage it from now on): `docker rm -f online-library`.
**Screenshots:** `docker images` (Fig 7.6), `docker ps` (7.7), volume list/inspect (7.12).

## Step 7 – Lab containers: Ansible + Jenkins
The provided `docker-compose.lab.yml` creates both containers (the sample report used `ansible-docker-lab` and `jenkins`).
```bash
docker compose -f docker-compose.lab.yml up -d --build
docker ps                               # jenkins + ansible-docker-lab running
docker exec ansible-docker-lab ansible --version
docker exec ansible-docker-lab ansible-galaxy collection list | findstr docker   # Linux: grep docker
```
Run the playbook by hand first (needs the image from Step 6 to exist):
```bash
docker exec ansible-docker-lab cat /docker-deploy.yml
docker exec ansible-docker-lab ansible-playbook -i /inventory.ini /docker-deploy.yml
docker ps                               # online-library-ansible on 5001->5000
```
Expected recap: `ok=… changed=… failed=0`.
**Screenshot:** the playbook (Fig 7.11) and the `failed=0` result.

What the playbook does (explain in viva): creates volume `library_data`, then starts container `online-library-ansible` from image `online-library-ci` with port `5001:5000`, volume `library_data:/app/data`, `restart_policy: always`, `recreate: yes` (so each pipeline run replaces the container with the new image, while data survives in the volume).

## Step 8 – Jenkins CI/CD (15 marks)
1. Open http://localhost:9091. Get the unlock password: `docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`
2. Install suggested plugins, create the admin user.
3. Verify Docker access from Jenkins:
```bash
docker exec jenkins docker info
```
(If "permission denied": `docker exec -u root jenkins chmod 666 /var/run/docker.sock` – same fix as in the sample report.)
4. **New Item → Pipeline** → name `OnlineLibrary-Pipeline`.
5. Pipeline section → Definition: **Pipeline script from SCM** → SCM: **Git** → Repository URL `https://github.com/<you>/OnlineLibrary.git` → Branch `*/main` → Script Path `Jenkinsfile` → Save.
6. **Build Now.** Open the build → **Console Output**.

Stages in the provided `Jenkinsfile`: Checkout → Docker Build → Pytest → Ansible Deploy → Verify.
Expected end of console: `Pipeline SUCCESS - Online Library deployed on http://localhost:5001`.
**Screenshots:** the stage view (Fig 7.8, 7.9, 7.14), console output, Jenkins pipeline config.
**Show failure-gating:** break a test, push, run build → Pytest stage goes red and Ansible stage is skipped. Fix, push, run again → green.

> Note: Jenkins pulls from GitHub, so the repo must be public (or add credentials in Jenkins). Optional extra: Poll SCM `H/2 * * * *` under "Build Triggers" for automatic builds.

## Step 9 – Verify everything (Module 12)
```bash
docker ps
docker volume ls
docker volume inspect library_data
docker exec online-library-ansible python -c "import sqlite3; c=sqlite3.connect('data/library.db'); print(c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()); c.close()"
docker exec online-library-ansible python -c "import sqlite3; c=sqlite3.connect('data/library.db'); [print(r) for r in c.execute('SELECT * FROM rentals')]; c.close()"
docker logs online-library-ansible
```
Then in the browser: rent a book at http://localhost:5001 → check it in `/admin` → run the Jenkins pipeline again (container is recreated) → refresh `/admin`: the rental is still there. That proves Docker Volume persistence.
Important outputs to quote: `Docker Build → SUCCESS`, `Pytest → 12 PASSED`, `Ansible → failed=0`, `Pipeline → SUCCESS`.

## Step 10 – Write the report (5 marks)
Use the same order as the sample's table of contents:
1 Introduction · 2 Objectives · 3 Abstract · 4 Technology Stack · 5 System Architecture (diagram + 11 numbered flow points) · Modules 1-12 (each: description, "Main Functions" bullets, technology, screenshot) · Results and Output · Commands Used · Advantages · Limitations · Future Enhancements · Conclusion.
Also include the front matter: cover page, bonafide certificate, evaluation scheme, and the repository URL.

Content you can reuse:
- **Advantages:** reduces manual register work; fast search; automatic stock/due-date/fine tracking; automated testing and deployment; consistent Docker environment; persistent data.
- **Limitations:** SQLite only; no login/authentication (admin page is open); no online payment; no email reminders; local Docker deployment; no monitoring/logging.
- **Future enhancements:** member login with roles, online payments, email/SMS due reminders, book reservations/waitlist, PostgreSQL/MySQL, GitHub webhook triggers, cloud deployment, monitoring.

## Step 11 – Viva preparation
Be able to explain, in your own words:
- Why SQLite + a volume? (DB file would be lost when the container is removed.)
- What does each Jenkinsfile stage do, and why does the build stop if tests fail?
- Why does Ansible use `recreate: yes`?
- How does the app prevent renting an out-of-stock book? (`available_copies` check in `/api/rent`, returns 409.)
- How is the fine computed? (`late_days × ₹2 × number of books`.)
- What is the difference between an image and a container; what does `-p 5001:5000` mean?
- How did you resolve the merge conflict?
Practise a live demo: edit text → commit → push → Build Now → see change at :5001.

## Troubleshooting (put real ones you hit into the report)
| Problem | Fix |
|---|---|
| Jenkins: `permission denied ... docker.sock` | `docker exec -u root jenkins chmod 666 /var/run/docker.sock` |
| Jenkins: `docker: not found` | Use the provided `jenkins/Dockerfile` (installs Docker CLI) and rebuild the lab |
| Ansible: `docker_container` module not found | `docker exec ansible-docker-lab ansible-galaxy collection install community.docker` |
| Ansible: no image `online-library-ci` | Run the Docker Build stage / `docker build -t online-library-ci .` first |
| Port 5001 already in use | `docker rm -f online-library` (remove the manual test container) |
| Git push rejected | `git pull origin main --rebase`, then push |
| Windows: `findstr` vs `grep` | Use `findstr` in cmd/PowerShell, `grep` on Linux/Mac |
