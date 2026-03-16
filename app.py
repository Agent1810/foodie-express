from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import csv, os, random, string, io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

app = Flask(__name__)
app.secret_key = "foodie_secret_2024"

BASE  = os.path.dirname(os.path.abspath(__file__))
DATA  = os.path.join(BASE, "data")

USERS       = os.path.join(DATA, "users.csv")
RESTAURANTS = os.path.join(DATA, "restaurants.csv")
MENU        = os.path.join(DATA, "menu.csv")
ORDERS      = os.path.join(DATA, "orders.csv")
RATINGS     = os.path.join(DATA, "ratings.csv")
COUPONS     = os.path.join(DATA, "coupons.csv")

AGENTS = ["Ravi Kumar","Priya Singh","Arjun Das","Meena Rao","Suresh Nair"]

# ── CSV helpers ──────────────────────────────
def read_csv(path):
    if not os.path.exists(path): return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def append_csv(path, row, fields):
    empty = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if empty: w.writeheader()
        w.writerow(row)

def gen_id(prefix, n=6):
    return prefix + "".join(random.choices(string.digits, k=n))

# ── Auth helpers ─────────────────────────────
def logged_in():  return "user_id" in session
def is_admin():   return session.get("role") == "admin"
def current_user():
    if not logged_in(): return None
    return next((u for u in read_csv(USERS) if u["user_id"]==session["user_id"]), None)

# ════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════
@app.route("/")
def home():
    return redirect(url_for("restaurants_page"))

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"].strip()
        pwd   = request.form["password"].strip()
        user  = next((u for u in read_csv(USERS)
                      if u["email"]==email and u["password"]==pwd), None)
        if user:
            session["user_id"] = user["user_id"]
            session["name"]    = user["name"]
            session["role"]    = user["role"]
            return redirect(url_for("admin_dashboard") if user["role"]=="admin"
                            else url_for("restaurants_page"))
        error = "Invalid email or password."
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == "POST":
        name    = request.form["name"].strip()
        email   = request.form["email"].strip()
        pwd     = request.form["password"].strip()
        phone   = request.form["phone"].strip()
        address = request.form["address"].strip()
        if any(u["email"]==email for u in read_csv(USERS)):
            error = "Email already registered."
        else:
            uid = gen_id("U")
            append_csv(USERS, {"user_id":uid,"name":name,"email":email,
                "password":pwd,"role":"customer","phone":phone,
                "address":address,"created_at":datetime.now().strftime("%Y-%m-%d")},
                ["user_id","name","email","password","role","phone","address","created_at"])
            session["user_id"]=uid; session["name"]=name; session["role"]="customer"
            return redirect(url_for("restaurants_page"))
    return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

# ════════════════════════════════════════════
#  RESTAURANTS
# ════════════════════════════════════════════
@app.route("/restaurants")
def restaurants_page():
    if not logged_in(): return redirect(url_for("login"))
    rests   = read_csv(RESTAURANTS)
    ratings = read_csv(RATINGS)
    query   = request.args.get("q","").lower()
    cuisine = request.args.get("cuisine","")
    if query:
        rests = [r for r in rests if query in r["name"].lower()
                 or query in r["cuisine"].lower() or query in r["location"].lower()]
    if cuisine:
        rests = [r for r in rests if r["cuisine"]==cuisine]
    all_cuisines = sorted(set(r["cuisine"] for r in read_csv(RESTAURANTS)))
    return render_template("restaurants.html", restaurants=rests,
                           cuisines=all_cuisines, query=query, sel_cuisine=cuisine)

@app.route("/restaurant/<rid>")
def menu_page(rid):
    if not logged_in(): return redirect(url_for("login"))
    rest  = next((r for r in read_csv(RESTAURANTS) if r["restaurant_id"]==rid), None)
    if not rest: return redirect(url_for("restaurants_page"))
    items = [m for m in read_csv(MENU) if m["restaurant_id"]==rid and m["is_available"]=="True"]
    cats  = sorted(set(m["category"] for m in items))
    cart  = session.get("cart", {})
    return render_template("menu.html", restaurant=rest, items=items,
                           categories=cats, cart=cart)

# ════════════════════════════════════════════
#  CART (session-based)
# ════════════════════════════════════════════
@app.route("/cart/add", methods=["POST"])
def cart_add():
    if not logged_in(): return jsonify({"error":"login"}), 401
    data = request.json
    cart = session.get("cart", {})
    iid  = data["item_id"]
    if iid in cart:
        cart[iid]["qty"] += 1
    else:
        cart[iid] = {"name":data["name"],"price":float(data["price"]),"qty":1,
                     "restaurant_id":data["restaurant_id"]}
    session["cart"] = cart
    total_items = sum(v["qty"] for v in cart.values())
    return jsonify({"success":True,"cart_count":total_items})

@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    data = request.json
    cart = session.get("cart", {})
    iid  = data["item_id"]
    if iid in cart:
        cart[iid]["qty"] -= 1
        if cart[iid]["qty"] <= 0: del cart[iid]
    session["cart"] = cart
    return jsonify({"success":True})

@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    session["cart"] = {}; return jsonify({"success":True})

@app.route("/cart")
def cart_page():
    if not logged_in(): return redirect(url_for("login"))
    cart    = session.get("cart", {})
    coupons = read_csv(COUPONS)
    user    = current_user()
    subtotal = sum(v["price"]*v["qty"] for v in cart.values())
    return render_template("cart.html", cart=cart, subtotal=subtotal,
                           coupons=coupons, user=user)

@app.route("/apply_coupon", methods=["POST"])
def apply_coupon():
    code     = request.json.get("code","").upper()
    subtotal = float(request.json.get("subtotal", 0))
    coupons  = read_csv(COUPONS)
    coupon   = next((c for c in coupons if c["code"]==code and c["is_active"]=="True"), None)
    if not coupon:
        return jsonify({"success":False,"message":"Invalid or expired coupon"})
    if subtotal < float(coupon["min_order"]):
        return jsonify({"success":False,
            "message":f"Minimum order Rs.{coupon['min_order']} required"})
    pct = float(coupon["discount_percent"])
    discount = round((subtotal * pct / 100) if pct > 0 else 50, 2)
    final    = max(0, subtotal - discount)
    session["applied_coupon"] = {"code":code,"discount":discount}
    return jsonify({"success":True,"discount":discount,"final":final,
                    "message":coupon["description"]})

# ════════════════════════════════════════════
#  CHECKOUT / PLACE ORDER
# ════════════════════════════════════════════
@app.route("/checkout", methods=["POST"])
def checkout():
    if not logged_in(): return redirect(url_for("login"))
    cart    = session.get("cart", {})
    if not cart: return redirect(url_for("cart_page"))
    user    = current_user()
    address = request.form.get("address", user["address"])
    coupon_info = session.get("applied_coupon", {})

    subtotal = sum(v["price"]*v["qty"] for v in cart.values())
    discount = coupon_info.get("discount", 0)
    final    = round(max(0, subtotal - discount), 2)

    items_str = "; ".join(f"{v['name']}x{v['qty']}" for v in cart.values())
    rid = list(cart.values())[0]["restaurant_id"]
    oid = gen_id("ORD")
    agent = random.choice(AGENTS)

    append_csv(ORDERS, {
        "order_id":oid, "user_id":session["user_id"],
        "restaurant_id":rid, "items":items_str,
        "total_amount":round(subtotal,2), "discount":discount,
        "final_amount":final, "status":"Confirmed",
        "order_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "delivery_agent":agent, "address":address,
        "coupon_used":coupon_info.get("code","")
    }, ["order_id","user_id","restaurant_id","items","total_amount","discount",
        "final_amount","status","order_time","delivery_agent","address","coupon_used"])

    # update coupon usage
    if coupon_info.get("code"):
        coupons = read_csv(COUPONS)
        for c in coupons:
            if c["code"] == coupon_info["code"]:
                c["used_count"] = str(int(c["used_count"]) + 1)
        write_csv(COUPONS, coupons,
            ["code","discount_percent","min_order","max_uses","used_count","is_active","description"])

    session["cart"] = {}
    session.pop("applied_coupon", None)
    return redirect(url_for("order_success", oid=oid))

@app.route("/order/success/<oid>")
def order_success(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = next((o for o in read_csv(ORDERS) if o["order_id"]==oid), None)
    rest  = next((r for r in read_csv(RESTAURANTS)
                  if r["restaurant_id"]==order["restaurant_id"]), None) if order else None
    return render_template("order_success.html", order=order, restaurant=rest)

# ════════════════════════════════════════════
#  ORDER TRACKING & HISTORY
# ════════════════════════════════════════════
@app.route("/orders")
def my_orders():
    if not logged_in(): return redirect(url_for("login"))
    orders = [o for o in read_csv(ORDERS) if o["user_id"]==session["user_id"]]
    rests  = {r["restaurant_id"]:r for r in read_csv(RESTAURANTS)}
    return render_template("my_orders.html", orders=list(reversed(orders)), restaurants=rests)

@app.route("/order/<oid>")
def track_order(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = next((o for o in read_csv(ORDERS) if o["order_id"]==oid), None)
    if not order: return redirect(url_for("my_orders"))
    rest  = next((r for r in read_csv(RESTAURANTS)
                  if r["restaurant_id"]==order["restaurant_id"]), None)
    rated = any(r["order_id"]==oid for r in read_csv(RATINGS))
    steps = ["Confirmed","Preparing","Out for Delivery","Delivered"]
    try: step_idx = steps.index(order["status"])
    except: step_idx = 0
    return render_template("track_order.html", order=order, restaurant=rest,
                           steps=steps, step_idx=step_idx, rated=rated)

@app.route("/order/<oid>/rate", methods=["POST"])
def rate_order(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = next((o for o in read_csv(ORDERS) if o["order_id"]==oid), None)
    if not order or order["status"] != "Delivered":
        return redirect(url_for("track_order", oid=oid))
    append_csv(RATINGS, {
        "rating_id":gen_id("RAT"), "order_id":oid,
        "user_id":session["user_id"], "restaurant_id":order["restaurant_id"],
        "food_rating":request.form["food_rating"],
        "delivery_rating":request.form["delivery_rating"],
        "review":request.form.get("review",""),
        "rated_on":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }, ["rating_id","order_id","user_id","restaurant_id","food_rating",
        "delivery_rating","review","rated_on"])
    return redirect(url_for("track_order", oid=oid))

# ════════════════════════════════════════════
#  PDF INVOICE
# ════════════════════════════════════════════
@app.route("/invoice/<oid>")
def download_invoice(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = next((o for o in read_csv(ORDERS) if o["order_id"]==oid), None)
    if not order: return "Order not found", 404
    user  = next((u for u in read_csv(USERS) if u["user_id"]==order["user_id"]), {})
    rest  = next((r for r in read_csv(RESTAURANTS)
                  if r["restaurant_id"]==order["restaurant_id"]), {})

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=0.6*inch, rightMargin=0.6*inch,
          topMargin=0.6*inch, bottomMargin=0.6*inch)

    styles = getSampleStyleSheet()
    orange = colors.HexColor("#FF6B35")
    dark   = colors.HexColor("#1a1a2e")
    gray   = colors.HexColor("#666666")
    light  = colors.HexColor("#fff3ee")

    h1 = ParagraphStyle("h1", fontSize=26, textColor=orange,
                        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)
    h2 = ParagraphStyle("h2", fontSize=11, textColor=gray,
                        fontName="Helvetica", alignment=TA_CENTER, spaceAfter=4)
    lbl = ParagraphStyle("lbl", fontSize=9, textColor=gray, fontName="Helvetica")
    val = ParagraphStyle("val", fontSize=10, textColor=dark, fontName="Helvetica-Bold")
    sm  = ParagraphStyle("sm", fontSize=9, textColor=gray, fontName="Helvetica")

    story = []
    story.append(Paragraph("🍔 FoodieExpress", h1))
    story.append(Paragraph("Your favourite food, delivered fast", h2))
    story.append(HRFlowable(width="100%", thickness=2, color=orange, spaceAfter=12))

    # Invoice meta
    meta = [
        [Paragraph("INVOICE", ParagraphStyle("inv", fontSize=16, fontName="Helvetica-Bold",
                   textColor=dark)),
         Paragraph(f"Order ID: <b>{order['order_id']}</b>",
                   ParagraphStyle("oid", fontSize=10, fontName="Helvetica",
                                  textColor=dark, alignment=TA_RIGHT))],
        [Paragraph(f"Date: {order['order_time']}", sm),
         Paragraph(f"Status: <b>{order['status']}</b>",
                   ParagraphStyle("st", fontSize=10, fontName="Helvetica-Bold",
                                  textColor=orange, alignment=TA_RIGHT))]
    ]
    t = Table(meta, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t); story.append(Spacer(1,12))

    # Customer & Restaurant
    info = [
        [Paragraph("Bill To", ParagraphStyle("bt", fontSize=10, fontName="Helvetica-Bold",
                   textColor=orange)),
         Paragraph("Restaurant", ParagraphStyle("rt", fontSize=10, fontName="Helvetica-Bold",
                   textColor=orange))],
        [Paragraph(f"<b>{user.get('name','')}</b>", val),
         Paragraph(f"<b>{rest.get('name','')}</b>", val)],
        [Paragraph(user.get('phone',''), sm), Paragraph(rest.get('cuisine',''), sm)],
        [Paragraph(order.get('address',''), sm), Paragraph(f"Agent: {order.get('delivery_agent','')}", sm)],
    ]
    ti = Table(info, colWidths=[3.5*inch, 3.5*inch])
    ti.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(1,0), light),
        ("BACKGROUND",(0,1),(1,-1),colors.white),
        ("BOX",(0,0),(1,-1),0.5,colors.HexColor("#ddd")),
        ("INNERGRID",(0,0),(1,-1),0.25,colors.HexColor("#eee")),
        ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(ti); story.append(Spacer(1,16))

    # Items table
    story.append(Paragraph("Order Items", ParagraphStyle("oit", fontSize=12,
                 fontName="Helvetica-Bold", textColor=dark, spaceAfter=6)))
    header = [Paragraph(h, ParagraphStyle("th", fontSize=10, fontName="Helvetica-Bold",
                        textColor=colors.white))
              for h in ["Item", "Qty", "Unit Price", "Amount"]]
    rows   = [header]
    items_list = order["items"].split("; ")
    menu_map = {m["item_name"]: m for m in read_csv(MENU)}
    subtotal = float(order["total_amount"])

    for it in items_list:
        if "x" in it:
            parts = it.rsplit("x", 1)
            name  = parts[0].strip()
            qty   = int(parts[1]) if parts[1].isdigit() else 1
            mi    = menu_map.get(name, {})
            price = float(mi.get("price", 0)) if mi else 0
            amt   = price * qty
            rows.append([Paragraph(name, sm),
                         Paragraph(str(qty), ParagraphStyle("c", fontSize=9,
                                   fontName="Helvetica", alignment=TA_CENTER)),
                         Paragraph(f"Rs.{price:.2f}", ParagraphStyle("r", fontSize=9,
                                   fontName="Helvetica", alignment=TA_RIGHT)),
                         Paragraph(f"Rs.{amt:.2f}", ParagraphStyle("r", fontSize=9,
                                   fontName="Helvetica-Bold", alignment=TA_RIGHT))])

    tbl = Table(rows, colWidths=[3.2*inch,0.7*inch,1.3*inch,1.5*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(3,0), orange),
        ("BACKGROUND",(0,1),(3,-1),colors.white),
        ("BOX",(0,0),(3,-1),0.5,colors.HexColor("#ddd")),
        ("INNERGRID",(0,0),(3,-1),0.25,colors.HexColor("#eee")),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(tbl); story.append(Spacer(1,10))

    # Totals
    disc  = float(order.get("discount",0))
    final = float(order.get("final_amount", subtotal))
    tot_data = []
    tot_data.append(["Subtotal", f"Rs.{subtotal:.2f}"])
    if disc > 0:
        coupon = order.get("coupon_used","")
        tot_data.append([f"Discount ({coupon})", f"- Rs.{disc:.2f}"])
    tot_data.append(["Delivery Fee", "FREE"])
    tot_data.append(["TOTAL", f"Rs.{final:.2f}"])

    tot_rows = []
    for i,(k,v) in enumerate(tot_data):
        is_last = i == len(tot_data)-1
        ks = ParagraphStyle("tk", fontSize=11 if is_last else 9,
                            fontName="Helvetica-Bold" if is_last else "Helvetica",
                            textColor=orange if is_last else dark, alignment=TA_LEFT)
        vs = ParagraphStyle("tv", fontSize=11 if is_last else 9,
                            fontName="Helvetica-Bold" if is_last else "Helvetica",
                            textColor=orange if is_last else dark, alignment=TA_RIGHT)
        tot_rows.append([Paragraph(k,ks), Paragraph(v,vs)])

    tt = Table(tot_rows, colWidths=[5.5*inch,1.5*inch])
    tt.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LINEABOVE",(0,-1),(1,-1),1.5,orange),
    ]))
    story.append(tt)
    story.append(Spacer(1,20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#eee"), spaceAfter=8))
    story.append(Paragraph("Thank you for ordering with FoodieExpress! 🍕",
                 ParagraphStyle("ty", fontSize=11, fontName="Helvetica",
                                textColor=gray, alignment=TA_CENTER)))
    story.append(Paragraph("support@foodieexpress.com  |  www.foodieexpress.com",
                 ParagraphStyle("contact", fontSize=9, fontName="Helvetica",
                                textColor=gray, alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f"invoice_{oid}.pdf",
                     mimetype="application/pdf")

# ════════════════════════════════════════════
#  ADMIN DASHBOARD
# ════════════════════════════════════════════
@app.route("/admin")
def admin_dashboard():
    if not logged_in() or not is_admin(): return redirect(url_for("login"))
    orders    = read_csv(ORDERS)
    users     = read_csv(USERS)
    rests     = read_csv(RESTAURANTS)
    ratings   = read_csv(RATINGS)

    total_orders    = len(orders)
    total_revenue   = sum(float(o.get("final_amount",0)) for o in orders if o["status"]=="Delivered")
    total_customers = len([u for u in users if u["role"]=="customer"])
    avg_rating      = (sum(float(r["food_rating"]) for r in ratings)/len(ratings)
                       if ratings else 0)

    recent_orders = list(reversed(orders))[:10]
    rest_map = {r["restaurant_id"]:r["name"] for r in rests}
    user_map  = {u["user_id"]:u["name"] for u in users}

    status_counts = {}
    for o in orders:
        s = o["status"]
        status_counts[s] = status_counts.get(s,0)+1

    return render_template("admin.html",
        total_orders=total_orders, total_revenue=round(total_revenue,2),
        total_customers=total_customers, avg_rating=round(avg_rating,1),
        recent_orders=recent_orders, rest_map=rest_map, user_map=user_map,
        status_counts=status_counts, restaurants=rests, all_orders=orders,
        users=[u for u in users if u["role"]=="customer"])

@app.route("/admin/update_status", methods=["POST"])
def admin_update_status():
    if not is_admin(): return jsonify({"error":"Unauthorized"}), 403
    oid    = request.json["order_id"]
    status = request.json["status"]
    orders = read_csv(ORDERS)
    for o in orders:
        if o["order_id"] == oid:
            o["status"] = status
    write_csv(ORDERS, orders,
        ["order_id","user_id","restaurant_id","items","total_amount","discount",
         "final_amount","status","order_time","delivery_agent","address","coupon_used"])
    return jsonify({"success":True})

@app.route("/admin/toggle_restaurant", methods=["POST"])
def toggle_restaurant():
    if not is_admin(): return jsonify({"error":"Unauthorized"}), 403
    rid   = request.json["restaurant_id"]
    rests = read_csv(RESTAURANTS)
    for r in rests:
        if r["restaurant_id"] == rid:
            r["is_open"] = "False" if r["is_open"]=="True" else "True"
    write_csv(RESTAURANTS, rests,
        ["restaurant_id","name","cuisine","rating","location","is_open",
         "delivery_time","image_emoji","min_order"])
    return jsonify({"success":True})

@app.template_filter('enumerate')
def do_enumerate(iterable, start=0):
    return enumerate(iterable, start)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
