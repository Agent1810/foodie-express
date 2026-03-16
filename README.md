# 🍔 FoodieExpress – Full Web App

A Swiggy/Zomato-style food delivery web app built with Flask + CSV storage.

---

## 📁 Project Structure

```
zomato_app/
├── app.py                  ← Flask backend (all routes)
├── requirements.txt        ← Dependencies
├── Procfile                ← For deployment
├── data/
│   ├── users.csv
│   ├── restaurants.csv
│   ├── menu.csv
│   ├── orders.csv
│   ├── ratings.csv
│   └── coupons.csv
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── restaurants.html
    ├── menu.html
    ├── cart.html
    ├── order_success.html
    ├── track_order.html
    ├── my_orders.html
    └── admin.html
```

---

## 🚀 STEP-BY-STEP: Run Locally

### Step 1 — Make sure Python is installed
Open your terminal (Command Prompt on Windows, Terminal on Mac/Linux) and type:
```
python --version
```
You need Python 3.10 or higher. Download from https://python.org if needed.

### Step 2 — Install dependencies
Navigate to the project folder and run:
```
cd zomato_app
pip install flask reportlab
```

### Step 3 — Run the app
```
python app.py
```
You'll see:
```
 * Running on http://127.0.0.1:5000
```

### Step 4 — Open in browser
Go to: **http://localhost:5000**

### Step 5 — Login with demo accounts
| Role     | Email                  | Password   |
|----------|------------------------|------------|
| Customer | alice@email.com        | alice123   |
| Admin    | admin@foodie.com       | admin123   |

---

## 🌐 DEPLOY TO RENDER (Free Hosting)

### Step 1 — Push to GitHub
1. Create a free account at https://github.com
2. Create a new repository (e.g. `foodie-express`)
3. Upload all your project files to it

   Easiest way — install Git, then in your project folder:
   ```
   git init
   git add .
   git commit -m "first commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/foodie-express.git
   git push -u origin main
   ```

### Step 2 — Deploy on Render
1. Go to https://render.com and create a free account
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select your repo
4. Fill in these settings:
   - **Name**: foodie-express
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
5. Click **"Create Web Service"**
6. Wait ~2 minutes → your app is live at a public URL! 🎉

### Important: Production mode
Before deploying, change the last line in `app.py`:
```python
# Change this:
app.run(debug=True, port=5000)

# To this:
import os
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
```

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Login / Register | Customer + Admin roles |
| 🍽️ Browse Restaurants | Search, filter by cuisine |
| 📜 Menu | Browse by category, add to cart |
| 🛒 Cart | Add/remove items, session-based |
| 🏷️ Coupons | WELCOME20, SAVE10, FEAST30, FLAT50 |
| 📦 Place Order | With delivery agent assignment |
| 📍 Track Order | Live status timeline |
| 🧾 PDF Invoice | Download per order |
| ⭐ Ratings | Food + delivery ratings + review |
| ⚡ Admin Panel | Orders, restaurants, customers |

---

## 🏷️ Available Coupons

| Code      | Discount        | Min Order |
|-----------|-----------------|-----------|
| WELCOME20 | 20% off         | Rs.100    |
| SAVE10    | 10% off         | Rs.200    |
| FLAT50    | Rs.50 flat      | Rs.300    |
| FEAST30   | 30% off         | Rs.500    |
