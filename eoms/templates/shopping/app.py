from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecret"

# Database config (change user/pass/db as needed)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/agrihire'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---- Models ----
class CartItem(db.Model):
    __tablename__ = "cart_items"
    cart_item_id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50))
    name = db.Column(db.String(200))
    image = db.Column(db.String(200))
    qty = db.Column(db.Integer)
    hire_rate = db.Column(db.Float)
    discount = db.Column(db.Float, default=0)
    subtotal = db.Column(db.Float)
    hire_from = db.Column(db.DateTime)
    hire_to = db.Column(db.DateTime)

# ---- Helpers ----
def serialize_cart(item):
    return {
        "cart_item_id": item.cart_item_id,
        "product_code": item.product_code,
        "name": item.name,
        "image": item.image,
        "qty": item.qty,
        "hire_rate": item.hire_rate,
        "discount": item.discount,
        "subtotal": item.subtotal,
        "hire_from": item.hire_from.strftime("%Y-%m-%d %H:%M:%S"),
        "hire_to": item.hire_to.strftime("%Y-%m-%d %H:%M:%S"),
    }

def recalc_totals():
    items = CartItem.query.all()
    original_total = sum(i.qty * i.hire_rate for i in items)
    total_discount = sum(i.discount for i in items)
    cart_total = sum(i.subtotal for i in items)
    total_gst = round(cart_total * 0.15, 2)  # 15% GST
    return items, original_total, total_discount, total_gst, cart_total

# ---- Routes ----
@app.route("/")
def view_cart():
    items, original_total, total_discount, total_gst, cart_total = recalc_totals()
    return render_template("shopping_cart.html",
                           cart_items=items,
                           original_total=original_total,
                           total_discount=total_discount,
                           total_gst=total_gst,
                           cart_total=cart_total,
                           store_list=[],
                           promo_code=None)

@app.route("/update_cart", methods=["POST"])
def update_cart():
    data = request.get_json()
    item = CartItem.query.get(data["cart_item_id"])
    if not item:
        return jsonify({"success": False, "message": "Item not found"})
    item.qty = data["qty"]
    item.subtotal = item.qty * item.hire_rate - item.discount
    db.session.commit()
    items, original_total, total_discount, total_gst, cart_total = recalc_totals()
    return jsonify({
        "success": True,
        "cart_items": [serialize_cart(i) for i in items],
        "original_total": original_total,
        "total_discount": total_discount,
        "total_gst": total_gst,
        "cart_total": cart_total
    })

@app.route("/apply_promo", methods=["POST"])
def apply_promo():
    data = request.get_json()
    code = data.get("promo_code", "")
    items = CartItem.query.all()
    if code == "SAVE10":
        for i in items:
            i.discount = 10
            i.subtotal = i.qty * i.hire_rate - i.discount
        db.session.commit()
        msg = "Promo applied successfully!"
        success = True
    else:
        msg = "Invalid promo code"
        success = False
    items, original_total, total_discount, total_gst, cart_total = recalc_totals()
    return jsonify({
        "success": success,
        "message": msg,
        "cart_items": [serialize_cart(i) for i in items],
        "original_total": original_total,
        "total_discount": total_discount,
        "total_gst": total_gst,
        "cart_total": cart_total
    })

@app.route("/remove_promo", methods=["POST"])
def remove_promo():
    items = CartItem.query.all()
    for i in items:
        i.discount = 0
        i.subtotal = i.qty * i.hire_rate
    db.session.commit()
    items, original_total, total_discount, total_gst, cart_total = recalc_totals()
    return jsonify({
        "success": True,
        "cart_items": [serialize_cart(i) for i in items],
        "original_total": original_total,
        "total_discount": total_discount,
        "total_gst": total_gst,
        "cart_total": cart_total
    })

# ---- Run ----
if __name__ == "__main__":
    # db.create_all()  # run once to create tables
    app.run(debug=True)
