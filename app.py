import os, json, random, string, io
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room
from models import db, User, Restaurant, MenuItem, Order, Rating, Coupon
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

app = Flask(__name__)
app.secret_key = "foodie_v2_secret_2024"

# ── Database config ──────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///foodie.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.template_filter("fromjson")
def fromjson(s): return json.loads(s) if s else {}

@app.template_filter("enumerate")
def do_enumerate(it, start=0): return enumerate(it, start)

AGENTS = ["Ravi Kumar","Priya Singh","Arjun Das","Meena Rao","Suresh Nair"]

# ── Seed data ────────────────────────────────
def seed_db():
    if User.query.first(): return
    # Users
    admin   = User(name="Admin",email="admin@foodie.com",password="admin123",role="admin",phone="9000000000",address="HQ Mumbai")
    alice   = User(name="Alice Johnson",email="alice@email.com",password="alice123",role="customer",phone="9876543210",address="12 MG Road Bangalore")
    owner1  = User(name="Raj Sharma",email="raj@spice.com",password="raj123",role="owner",phone="9111122223",address="Bangalore")
    owner2  = User(name="Marco Polo",email="marco@pizza.com",password="marco123",role="owner",phone="9222233334",address="Kolkata")
    owner3  = User(name="Chen Wei",email="chen@dragon.com",password="chen123",role="owner",phone="9333344445",address="Chennai")
    db.session.add_all([admin, alice, owner1, owner2, owner3])
    db.session.flush()

    # Restaurants
    r1 = Restaurant(owner_id=owner1.id,name="Spice Garden",cuisine="Indian",description="Authentic North Indian flavors",address="12 Brigade Road",city="Bangalore",image_emoji="🍛",rating=4.5,delivery_time="30-40 min",min_order=150,lat=12.9716,lng=77.5946)
    r2 = Restaurant(owner_id=owner2.id,name="Pizza Palace",cuisine="Italian",description="Wood-fired pizzas since 1995",address="45 Park Street",city="Kolkata",image_emoji="🍕",rating=4.2,delivery_time="25-35 min",min_order=200,lat=22.5726,lng=88.3639)
    r3 = Restaurant(owner_id=owner3.id,name="Dragon Wok",cuisine="Chinese",description="Wok-tossed perfection",address="78 Anna Salai",city="Chennai",image_emoji="🥢",rating=4.7,delivery_time="20-30 min",min_order=120,lat=13.0827,lng=80.2707)
    r4 = Restaurant(owner_id=owner1.id,name="Burger Barn",cuisine="American",description="Juicy burgers, crispy fries",address="34 Indiranagar",city="Bangalore",image_emoji="🍔",rating=4.0,delivery_time="15-25 min",min_order=100,lat=12.9784,lng=77.6408)
    db.session.add_all([r1,r2,r3,r4])
    db.session.flush()

    # Menu
    menus = [
        MenuItem(restaurant_id=r1.id,name="Butter Chicken",description="Creamy tomato curry",category="Main Course",price=280,emoji="🍗"),
        MenuItem(restaurant_id=r1.id,name="Paneer Tikka",description="Grilled cottage cheese",category="Starter",price=220,emoji="🧀"),
        MenuItem(restaurant_id=r1.id,name="Garlic Naan",description="Soft bread with garlic butter",category="Bread",price=60,emoji="🫓"),
        MenuItem(restaurant_id=r1.id,name="Mango Lassi",description="Chilled mango yogurt",category="Beverage",price=80,emoji="🥭"),
        MenuItem(restaurant_id=r1.id,name="Dal Makhani",description="Slow cooked black lentils",category="Main Course",price=200,emoji="🫘"),
        MenuItem(restaurant_id=r2.id,name="Margherita Pizza",description="Classic tomato mozzarella",category="Pizza",price=350,emoji="🍕"),
        MenuItem(restaurant_id=r2.id,name="Pepperoni Pizza",description="Loaded with pepperoni",category="Pizza",price=420,emoji="🍕"),
        MenuItem(restaurant_id=r2.id,name="Garlic Bread",description="Crispy herb butter bread",category="Starter",price=150,emoji="🥖"),
        MenuItem(restaurant_id=r2.id,name="Tiramisu",description="Classic Italian dessert",category="Dessert",price=180,emoji="☕"),
        MenuItem(restaurant_id=r3.id,name="Kung Pao Chicken",description="Spicy stir-fried chicken",category="Main Course",price=300,emoji="🥜"),
        MenuItem(restaurant_id=r3.id,name="Spring Rolls",description="Crispy vegetable rolls",category="Starter",price=160,emoji="🥟"),
        MenuItem(restaurant_id=r3.id,name="Fried Rice",description="Wok-tossed rice",category="Main Course",price=200,emoji="🍚"),
        MenuItem(restaurant_id=r4.id,name="Classic Burger",description="Juicy beef patty",category="Burger",price=250,emoji="🍔"),
        MenuItem(restaurant_id=r4.id,name="Cheese Fries",description="Crispy fries with cheese",category="Sides",price=120,emoji="🧀"),
        MenuItem(restaurant_id=r4.id,name="Chicken Wings",description="Crispy with dipping sauce",category="Starter",price=280,emoji="🍗"),
    ]
    db.session.add_all(menus)

    # Coupons
    coupons = [
        Coupon(code="WELCOME20",discount_percent=20,min_order=100,description="20% off your first order"),
        Coupon(code="SAVE10",discount_percent=10,min_order=200,description="10% off above Rs.200"),
        Coupon(code="FLAT50",flat_discount=50,min_order=300,description="Rs.50 flat off above Rs.300"),
        Coupon(code="FEAST30",discount_percent=30,min_order=500,description="30% off above Rs.500"),
    ]
    db.session.add_all(coupons)
    db.session.commit()
    print("✅ Database seeded!")

# ── Helpers ──────────────────────────────────
def logged_in():  return "user_id" in session
def is_admin():   return session.get("role") == "admin"
def is_owner():   return session.get("role") in ("owner","admin")
def current_user(): return User.query.get(session["user_id"]) if logged_in() else None
def gen_code():   return "ORD" + "".join(random.choices(string.digits, k=6))

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
        user = User.query.filter_by(email=request.form["email"], password=request.form["password"]).first()
        if user:
            session["user_id"] = user.id
            session["name"]    = user.name
            session["role"]    = user.role
            if user.role == "admin":   return redirect(url_for("admin_dashboard"))
            if user.role == "owner":   return redirect(url_for("owner_dashboard"))
            return redirect(url_for("restaurants_page"))
        error = "Invalid email or password."
    return render_template("login.html", error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == "POST":
        if User.query.filter_by(email=request.form["email"]).first():
            error = "Email already registered."
        else:
            role = request.form.get("role","customer")
            u = User(name=request.form["name"], email=request.form["email"],
                     password=request.form["password"], role=role,
                     phone=request.form["phone"], address=request.form["address"])
            db.session.add(u); db.session.commit()
            session["user_id"]=u.id; session["name"]=u.name; session["role"]=u.role
            if role=="owner": return redirect(url_for("owner_dashboard"))
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
    q       = request.args.get("q","").lower()
    cuisine = request.args.get("cuisine","")
    rests   = Restaurant.query.filter_by(is_open=True).all()
    if q:       rests = [r for r in rests if q in r.name.lower() or q in r.cuisine.lower()]
    if cuisine: rests = [r for r in rests if r.cuisine == cuisine]
    all_cuisines = sorted(set(r.cuisine for r in Restaurant.query.all()))
    return render_template("restaurants.html", restaurants=rests,
                           cuisines=all_cuisines, query=q, sel_cuisine=cuisine)

@app.route("/restaurant/<int:rid>")
def menu_page(rid):
    if not logged_in(): return redirect(url_for("login"))
    rest  = Restaurant.query.get_or_404(rid)
    items = MenuItem.query.filter_by(restaurant_id=rid, is_available=True).all()
    cats  = sorted(set(i.category for i in items))
    return render_template("menu.html", restaurant=rest, items=items, categories=cats)

# ════════════════════════════════════════════
#  CART
# ════════════════════════════════════════════
@app.route("/cart/add", methods=["POST"])
def cart_add():
    if not logged_in(): return jsonify({"error":"login"}), 401
    d    = request.json
    cart = session.get("cart", {})
    iid  = str(d["item_id"])
    if iid in cart: cart[iid]["qty"] += 1
    else: cart[iid] = {"name":d["name"],"price":float(d["price"]),"qty":1,"restaurant_id":d["restaurant_id"]}
    session["cart"] = cart
    return jsonify({"success":True,"cart_count":sum(v["qty"] for v in cart.values())})

@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    d    = request.json
    cart = session.get("cart",{})
    iid  = str(d["item_id"])
    if iid in cart:
        cart[iid]["qty"] -= 1
        if cart[iid]["qty"] <= 0: del cart[iid]
    session["cart"] = cart
    return jsonify({"success":True,"cart_count":sum(v["qty"] for v in cart.values())})

@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    session["cart"] = {}
    return jsonify({"success":True})

@app.route("/cart")
def cart_page():
    if not logged_in(): return redirect(url_for("login"))
    cart     = session.get("cart",{})
    coupons  = Coupon.query.filter_by(is_active=True).all()
    user     = current_user()
    subtotal = sum(v["price"]*v["qty"] for v in cart.values())
    return render_template("cart.html", cart=cart, subtotal=subtotal, coupons=coupons, user=user)

@app.route("/apply_coupon", methods=["POST"])
def apply_coupon():
    code     = request.json.get("code","").upper()
    subtotal = float(request.json.get("subtotal",0))
    coupon   = Coupon.query.filter_by(code=code, is_active=True).first()
    if not coupon: return jsonify({"success":False,"message":"Invalid or expired coupon"})
    if subtotal < coupon.min_order:
        return jsonify({"success":False,"message":f"Minimum order Rs.{int(coupon.min_order)} required"})
    discount = round(subtotal * coupon.discount_percent / 100 if coupon.discount_percent else coupon.flat_discount, 2)
    final    = max(0, subtotal - discount)
    session["applied_coupon"] = {"code":code,"discount":discount}
    return jsonify({"success":True,"discount":discount,"final":final,"message":coupon.description})

# ════════════════════════════════════════════
#  CHECKOUT
# ════════════════════════════════════════════
@app.route("/checkout", methods=["POST"])
def checkout():
    if not logged_in(): return redirect(url_for("login"))
    cart = session.get("cart",{})
    if not cart: return redirect(url_for("cart_page"))
    user    = current_user()
    address = request.form.get("address", user.address)
    coupon_info = session.get("applied_coupon",{})
    subtotal = sum(v["price"]*v["qty"] for v in cart.values())
    discount = coupon_info.get("discount",0)
    total    = round(max(0, subtotal-discount),2)
    rid      = list(cart.values())[0]["restaurant_id"]
    agent    = random.choice(AGENTS)
    rest     = Restaurant.query.get(rid)

    # Agent starts near restaurant
    agent_lat = (rest.lat or 12.9716) + random.uniform(-0.01, 0.01)
    agent_lng = (rest.lng or 77.5946) + random.uniform(-0.01, 0.01)

    order = Order(
        order_code=gen_code(), user_id=user.id, restaurant_id=rid,
        items_json=json.dumps(cart), subtotal=subtotal, discount=discount,
        total=total, status="Confirmed", delivery_agent=agent,
        address=address, coupon_used=coupon_info.get("code",""),
        agent_lat=agent_lat, agent_lng=agent_lng
    )
    db.session.add(order)
    if coupon_info.get("code"):
        c = Coupon.query.filter_by(code=coupon_info["code"]).first()
        if c: c.used_count += 1
    db.session.commit()
    session["cart"] = {}
    session.pop("applied_coupon",None)
    return redirect(url_for("order_success", oid=order.id))

@app.route("/order/success/<int:oid>")
def order_success(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = Order.query.get_or_404(oid)
    return render_template("order_success.html", order=order, restaurant=order.restaurant)

# ════════════════════════════════════════════
#  ORDER TRACKING
# ════════════════════════════════════════════
@app.route("/orders")
def my_orders():
    if not logged_in(): return redirect(url_for("login"))
    orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.placed_at.desc()).all()
    return render_template("my_orders.html", orders=orders)

@app.route("/order/<int:oid>")
def track_order(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = Order.query.get_or_404(oid)
    rated = Rating.query.filter_by(order_id=oid).first()
    steps = ["Confirmed","Preparing","Out for Delivery","Delivered"]
    try: step_idx = steps.index(order.status)
    except: step_idx = 0
    return render_template("track_order.html", order=order,
                           restaurant=order.restaurant, steps=steps,
                           step_idx=step_idx, rated=rated)

@app.route("/order/<int:oid>/rate", methods=["POST"])
def rate_order(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = Order.query.get_or_404(oid)
    if order.status != "Delivered": return redirect(url_for("track_order", oid=oid))
    r = Rating(order_id=oid, user_id=session["user_id"],
               restaurant_id=order.restaurant_id,
               food_rating=request.form["food_rating"],
               delivery_rating=request.form["delivery_rating"],
               review=request.form.get("review",""))
    db.session.add(r); db.session.commit()
    return redirect(url_for("track_order", oid=oid))

# ════════════════════════════════════════════
#  PDF INVOICE
# ════════════════════════════════════════════
@app.route("/invoice/<int:oid>")
def download_invoice(oid):
    if not logged_in(): return redirect(url_for("login"))
    order = Order.query.get_or_404(oid)
    user  = order.customer
    rest  = order.restaurant
    cart  = json.loads(order.items_json)

    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4,
           leftMargin=0.6*inch, rightMargin=0.6*inch,
           topMargin=0.6*inch, bottomMargin=0.6*inch)
    orange = colors.HexColor("#FF6B35")
    dark   = colors.HexColor("#1a1a2e")
    gray   = colors.HexColor("#666666")
    light  = colors.HexColor("#fff3ee")
    styles = getSampleStyleSheet()

    h1  = ParagraphStyle("h1",fontSize=26,textColor=orange,fontName="Helvetica-Bold",alignment=TA_CENTER,spaceAfter=2)
    h2  = ParagraphStyle("h2",fontSize=11,textColor=gray,fontName="Helvetica",alignment=TA_CENTER,spaceAfter=4)
    sm  = ParagraphStyle("sm",fontSize=9,textColor=gray,fontName="Helvetica")
    val = ParagraphStyle("val",fontSize=10,textColor=dark,fontName="Helvetica-Bold")

    story = []
    story.append(Paragraph("FoodieExpress", h1))
    story.append(Paragraph("Your favourite food, delivered fast", h2))
    story.append(HRFlowable(width="100%",thickness=2,color=orange,spaceAfter=12))

    meta = [[Paragraph("INVOICE",ParagraphStyle("i",fontSize=16,fontName="Helvetica-Bold",textColor=dark)),
             Paragraph(f"Order: <b>{order.order_code}</b>",ParagraphStyle("oc",fontSize=10,fontName="Helvetica",textColor=dark,alignment=TA_RIGHT))],
            [Paragraph(f"Date: {order.placed_at.strftime('%d %b %Y %H:%M')}",sm),
             Paragraph(f"Status: <b>{order.status}</b>",ParagraphStyle("st",fontSize=10,fontName="Helvetica-Bold",textColor=orange,alignment=TA_RIGHT))]]
    t = Table(meta,colWidths=[3.5*inch,3.5*inch])
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t); story.append(Spacer(1,12))

    info = [[Paragraph("Bill To",ParagraphStyle("bt",fontSize=10,fontName="Helvetica-Bold",textColor=orange)),
             Paragraph("Restaurant",ParagraphStyle("rt",fontSize=10,fontName="Helvetica-Bold",textColor=orange))],
            [Paragraph(f"<b>{user.name}</b>",val),Paragraph(f"<b>{rest.name}</b>",val)],
            [Paragraph(user.phone or "",sm),Paragraph(rest.cuisine,sm)],
            [Paragraph(order.address or "",sm),Paragraph(f"Agent: {order.delivery_agent}",sm)]]
    ti = Table(info,colWidths=[3.5*inch,3.5*inch])
    ti.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(1,0),light),("BACKGROUND",(0,1),(1,-1),colors.white),
        ("BOX",(0,0),(1,-1),0.5,colors.HexColor("#ddd")),
        ("INNERGRID",(0,0),(1,-1),0.25,colors.HexColor("#eee")),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(ti); story.append(Spacer(1,16))

    story.append(Paragraph("Order Items",ParagraphStyle("oit",fontSize=12,fontName="Helvetica-Bold",textColor=dark,spaceAfter=6)))
    header = [Paragraph(h,ParagraphStyle("th",fontSize=10,fontName="Helvetica-Bold",textColor=colors.white))
              for h in ["Item","Qty","Unit Price","Amount"]]
    rows = [header]
    for iid, item in cart.items():
        amt = item["price"]*item["qty"]
        rows.append([Paragraph(item["name"],sm),
                     Paragraph(str(item["qty"]),ParagraphStyle("c",fontSize=9,fontName="Helvetica",alignment=TA_CENTER)),
                     Paragraph(f"Rs.{item['price']:.0f}",ParagraphStyle("r",fontSize=9,fontName="Helvetica",alignment=TA_RIGHT)),
                     Paragraph(f"Rs.{amt:.0f}",ParagraphStyle("rb",fontSize=9,fontName="Helvetica-Bold",alignment=TA_RIGHT))])
    tbl = Table(rows,colWidths=[3.2*inch,0.7*inch,1.3*inch,1.5*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(3,0),orange),("BACKGROUND",(0,1),(3,-1),colors.white),
        ("BOX",(0,0),(3,-1),0.5,colors.HexColor("#ddd")),
        ("INNERGRID",(0,0),(3,-1),0.25,colors.HexColor("#eee")),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(tbl); story.append(Spacer(1,10))

    tot_data = [("Subtotal", f"Rs.{order.subtotal:.0f}")]
    if order.discount and order.discount > 0:
        tot_data.append((f"Discount ({order.coupon_used})", f"- Rs.{order.discount:.0f}"))
    tot_data.append(("Delivery", "FREE"))
    tot_data.append(("TOTAL", f"Rs.{order.total:.0f}"))
    tot_rows = []
    for k,v in tot_data:
        is_last = k == "TOTAL"
        tot_rows.append([
            Paragraph(k,ParagraphStyle("tk",fontSize=11 if is_last else 9,fontName="Helvetica-Bold" if is_last else "Helvetica",textColor=orange if is_last else dark,alignment=TA_LEFT)),
            Paragraph(v,ParagraphStyle("tv",fontSize=11 if is_last else 9,fontName="Helvetica-Bold" if is_last else "Helvetica",textColor=orange if is_last else dark,alignment=TA_RIGHT))
        ])
    tt = Table(tot_rows,colWidths=[5.5*inch,1.5*inch])
    tt.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LINEABOVE",(0,-1),(1,-1),1.5,orange)]))
    story.append(tt)
    story.append(Spacer(1,20))
    story.append(HRFlowable(width="100%",thickness=1,color=colors.HexColor("#eee"),spaceAfter=8))
    story.append(Paragraph("Thank you for ordering with FoodieExpress!",ParagraphStyle("ty",fontSize=11,fontName="Helvetica",textColor=gray,alignment=TA_CENTER)))

    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f"invoice_{order.order_code}.pdf", mimetype="application/pdf")

# ════════════════════════════════════════════
#  WEBSOCKET — Real-time tracking
# ════════════════════════════════════════════
@socketio.on("join_order")
def on_join(data):
    join_room(f"order_{data['order_id']}")

@socketio.on("update_status")
def on_update_status(data):
    order = Order.query.get(data["order_id"])
    if not order: return
    order.status = data["status"]
    db.session.commit()
    socketio.emit("status_changed", {
        "order_id": order.id,
        "status": order.status,
        "agent_lat": order.agent_lat,
        "agent_lng": order.agent_lng,
    }, room=f"order_{order.id}")

@socketio.on("update_location")
def on_location(data):
    order = Order.query.get(data["order_id"])
    if not order: return
    order.agent_lat = data["lat"]
    order.agent_lng = data["lng"]
    db.session.commit()
    socketio.emit("location_update", {
        "lat": data["lat"], "lng": data["lng"]
    }, room=f"order_{order.id}")

# ════════════════════════════════════════════
#  RESTAURANT OWNER DASHBOARD
# ════════════════════════════════════════════
@app.route("/owner")
def owner_dashboard():
    if not logged_in() or not is_owner(): return redirect(url_for("login"))
    user  = current_user()
    rests = Restaurant.query.filter_by(owner_id=user.id).all() if user.role=="owner" else Restaurant.query.all()
    rest_ids = [r.id for r in rests]
    orders   = Order.query.filter(Order.restaurant_id.in_(rest_ids)).order_by(Order.placed_at.desc()).all() if rest_ids else []
    revenue  = sum(o.total for o in orders if o.status=="Delivered")
    return render_template("owner_dashboard.html", restaurants=rests,
                           orders=orders, revenue=round(revenue,2), user=user)

@app.route("/owner/update_status", methods=["POST"])
def owner_update_status():
    if not is_owner(): return jsonify({"error":"Unauthorized"}),403
    data  = request.json
    order = Order.query.get(data["order_id"])
    if not order: return jsonify({"error":"Not found"}),404
    order.status = data["status"]
    db.session.commit()
    socketio.emit("status_changed",{
        "order_id":order.id,"status":order.status,
        "agent_lat":order.agent_lat,"agent_lng":order.agent_lng,
    }, room=f"order_{order.id}")
    return jsonify({"success":True})

@app.route("/owner/toggle_restaurant", methods=["POST"])
def toggle_restaurant():
    if not is_owner(): return jsonify({"error":"Unauthorized"}),403
    r = Restaurant.query.get(request.json["restaurant_id"])
    if not r: return jsonify({"error":"Not found"}),404
    r.is_open = not r.is_open
    db.session.commit()
    return jsonify({"success":True,"is_open":r.is_open})

@app.route("/owner/add_menu_item", methods=["POST"])
def add_menu_item():
    if not is_owner(): return jsonify({"error":"Unauthorized"}),403
    d = request.json
    item = MenuItem(restaurant_id=d["restaurant_id"],name=d["name"],
                    description=d.get("description",""),category=d.get("category","Main Course"),
                    price=float(d["price"]),emoji=d.get("emoji","🍽️"))
    db.session.add(item); db.session.commit()
    return jsonify({"success":True,"item_id":item.id})

@app.route("/owner/toggle_item", methods=["POST"])
def toggle_item():
    if not is_owner(): return jsonify({"error":"Unauthorized"}),403
    item = MenuItem.query.get(request.json["item_id"])
    if not item: return jsonify({"error":"Not found"}),404
    item.is_available = not item.is_available
    db.session.commit()
    return jsonify({"success":True,"is_available":item.is_available})

@app.route("/owner/simulate_location/<int:oid>")
def simulate_location(oid):
    """Simulate delivery agent moving toward customer"""
    if not is_owner(): return jsonify({"error":"Unauthorized"}),403
    order = Order.query.get_or_404(oid)
    rest  = order.restaurant
    # Move agent slightly toward destination
    order.agent_lat = (order.agent_lat or rest.lat) + random.uniform(0.001, 0.003)
    order.agent_lng = (order.agent_lng or rest.lng) + random.uniform(0.001, 0.003)
    db.session.commit()
    socketio.emit("location_update",{
        "lat":order.agent_lat,"lng":order.agent_lng
    }, room=f"order_{oid}")
    return jsonify({"success":True,"lat":order.agent_lat,"lng":order.agent_lng})

# ════════════════════════════════════════════
#  ADMIN
# ════════════════════════════════════════════
@app.route("/admin")
def admin_dashboard():
    if not logged_in() or not is_admin(): return redirect(url_for("login"))
    orders    = Order.query.order_by(Order.placed_at.desc()).all()
    users     = User.query.filter_by(role="customer").all()
    rests     = Restaurant.query.all()
    ratings   = Rating.query.all()
    revenue   = sum(o.total for o in orders if o.status=="Delivered")
    avg_r     = sum(r.food_rating for r in ratings)/len(ratings) if ratings else 0
    status_counts = {}
    for o in orders: status_counts[o.status] = status_counts.get(o.status,0)+1
    return render_template("admin.html", orders=orders, users=users,
                           restaurants=rests, total_revenue=round(revenue,2),
                           avg_rating=round(avg_r,1), status_counts=status_counts)

@app.route("/admin/update_status", methods=["POST"])
def admin_update_status():
    if not is_admin(): return jsonify({"error":"Unauthorized"}),403
    order = Order.query.get(request.json["order_id"])
    if not order: return jsonify({"error":"Not found"}),404
    order.status = request.json["status"]
    db.session.commit()
    socketio.emit("status_changed",{
        "order_id":order.id,"status":order.status,
        "agent_lat":order.agent_lat,"agent_lng":order.agent_lng,
    }, room=f"order_{order.id}")
    return jsonify({"success":True})

# ════════════════════════════════════════════
#  API — Order status (for polling fallback)
# ════════════════════════════════════════════
@app.route("/api/order/<int:oid>")
def api_order(oid):
    if not logged_in(): return jsonify({"error":"Unauthorized"}),401
    order = Order.query.get_or_404(oid)
    return jsonify({"status":order.status,"agent_lat":order.agent_lat,"agent_lng":order.agent_lng})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_db()
    port = int(os.environ.get("PORT",5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
