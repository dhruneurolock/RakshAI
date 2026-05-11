# 🚀 How To Run This Project

---

## Prerequisites

```bash
# Check installed versions
python --version        # Python 3.10+
node --version          # Node.js 18+
npm --version           # npm 9+
git --version           # Git
```

---

## 1️⃣ Clone the Repository

```bash
git clone <your-repo-url>
cd NeuroPentWeb
```

---

## 2️⃣ Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate virtual environment (Windows CMD)
.\.venv\Scripts\activate.bat

# Activate virtual environment (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Run database migrations
python -m alembic upgrade head

# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> Backend runs at: **http://localhost:8000**  
> API Docs at: **http://localhost:8000/api/v1/docs**

---

## 3️⃣ Frontend Setup

```bash
# Open a new terminal and navigate to frontend
cd frontend

# Copy environment file
copy .env.local.example .env.local

# Install dependencies
npm install

# Start the development server
npm run dev
```

> Frontend runs at: **http://localhost:5173**

---

## 4️⃣ Quick Start (PowerShell – One Command)

```powershell
# From the project root directory
.\start-local-dev.ps1
```

---

## 5️⃣ Docker Setup (Optional)

```bash
# From the project root directory
docker-compose up --build
```

---

## 🔗 Access URLs

| Service     | URL                                  |
|-------------|--------------------------------------|
| Frontend    | http://localhost:5173                 |
| Backend API | http://localhost:8000                 |
| API Docs    | http://localhost:8000/api/v1/docs     |

---

## 🛑 Stop the Servers

```bash
# Press Ctrl + C in each terminal to stop the running servers
```

---
