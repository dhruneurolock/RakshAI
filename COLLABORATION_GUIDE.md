# RakshAI Collaboration & Developer Setup Guide 🤝

This guide explains how two developers can work together on this project using separate laptops. Since the repository is already hosted on GitHub at `https://github.com/dhruneurolock/RakshAI.git`, you can follow these steps to keep your local environments, databases, and codebases in sync.

---

## 🛠️ Onboarding Developer B (Second Laptop Setup)

On the second laptop, perform the following setup steps:

### 1. Clone the Repository
Clone the repository into your preferred workspace directory:
```bash
git clone https://github.com/dhruneurolock/RakshAI.git
cd RakshAI
```

### 2. Configure Local Environment Variables
Create the local environment files from their template examples. 
> [!IMPORTANT]
> Do not commit `.env` or `.env.local` files to Git. They are ignored by `.gitignore` because they contain credentials and paths specific to your laptop.

```powershell
# In the project root directory:

# Create backend .env
copy backend\.env.local.example backend\.env

# Create frontend .env.local
copy frontend\.env.local.example frontend\.env.local
```

### 3. Create the Backend Python Virtual Environment
Set up an isolated Python environment and install the required dependencies:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

### 4. Install Frontend dependencies
Install the required npm packages for the React application:
```powershell
cd frontend
npm install
cd ..
```

### 5. Setup the Local SQLite Database
Run the initial database migrations to create tables in your local SQLite database:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
cd ..
```

### 6. Verify and Run
Run the verification script to confirm everything is set up correctly:
```powershell
python verify-setup.py
```
If verification passes, start the development servers:
```powershell
# On PowerShell:
powershell -ExecutionPolicy Bypass -File start-local-dev.ps1

# On CMD:
start-local-dev.bat
```
Open your browser to:
- **Frontend UI**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/api/v1/docs

---

## 🔄 Daily Collaboration Workflow

To ensure you don't overwrite each other's code or create messy conflicts, follow this daily routine:

### 🌅 Starting the Day (Syncing Up)
Before you write any new code:
1. Switch to your main branch:
   ```bash
   git checkout main
   ```
2. Pull the latest code from GitHub:
   ```bash
   git pull origin main
   ```
3. Update packages if `requirements.txt` or `package.json` changed:
   ```powershell
   # If backend requirements changed:
   cd backend
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

   # If frontend package.json changed:
   cd ../frontend
   npm install
   ```
4. Run any new database migrations:
   ```powershell
   cd ../backend
   .\.venv\Scripts\Activate.ps1
   alembic upgrade head
   ```

### 💻 Developing a Feature (Working Independently)
Always work in a separate branch rather than committing directly to `main`:
1. Create a descriptive feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Write code, test locally, and commit changes:
   ```bash
   git add .
   git commit -m "feat: added login validation error alerts"
   ```

### 🚀 Completing a Feature (Pushing & Merging)
1. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a **Pull Request (PR)** on GitHub.
3. Have the other developer review the code. Once approved, merge it into `main`.

---

## 🗄️ Database Schemas & Migrations (Alembic)

Since you are using SQLite, each developer has their own local database file (`neuropent_local.db`). Do not attempt to share or commit the database file itself. Instead, share the database structure using **Alembic**.

### When you create/modify a database model (e.g. in `backend/app/models/`):
1. Activate your virtual environment and run the migration generator:
   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   alembic revision --autogenerate -m "added_new_column_to_scan"
   ```
2. Check the newly generated migration file in `backend/alembic/versions/` to verify it looks correct.
3. Commit and push the new migration file to GitHub:
   ```bash
   git add backend/alembic/versions/
   git commit -m "migration: add new column to scan table"
   git push origin feature/your-feature-name
   ```
4. The other developer will pull the migration file and run:
   ```powershell
   alembic upgrade head
   ```
   This keeps both of your databases structured exactly the same way without affecting your local test data.

---

## ⚠️ Collaboration Best Practices

1. **Keep Pull Requests small**: Large PRs are harder to merge and more likely to cause conflicts.
2. **Never commit secret keys**: If you add new third-party services or tokens, add them to `backend/.env.local.example` with dummy/mock values, and configure the actual credentials locally in your private `.env` file.
3. **Run tests before pushing**:
   * **Backend**: `pytest`
   * **Frontend**: `npm run test` or `npm run build` (to ensure Vite compiles properly).
