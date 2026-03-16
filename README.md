# 🍔 FoodieExpress v2 — Full Stack Web App

## Features
- 🔐 Login/Register (Customer, Restaurant Owner, Admin)
- 🍽️ Browse restaurants & menus
- 🛒 Cart with coupons
- 📦 Place orders
- 📍 **Live order tracking with OpenStreetMap**
- 🔄 **Real-time status updates via WebSockets**
- 🏪 **Restaurant owner dashboard** (manage menu, update orders)
- 🧾 PDF invoice download
- ⭐ Ratings & reviews
- 🐘 PostgreSQL / SQLite database

---

## Run Locally

```bash
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Customer | alice@email.com | alice123 |
| Owner | raj@spice.com | raj123 |
| Owner | marco@pizza.com | marco123 |
| Admin | admin@foodie.com | admin123 |

---

## Deploy on Render

1. Push to GitHub
2. Go to render.com → New Web Service
3. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
4. Add Environment Variable:
   - `DATABASE_URL` = your PostgreSQL URL from Supabase

---

## Connect PostgreSQL (Supabase)

1. Go to https://supabase.com → New Project
2. Settings → Database → Connection String → URI
3. Copy the URI
4. On Render → Environment → Add: `DATABASE_URL` = paste URI

Tables are created automatically on first run!
