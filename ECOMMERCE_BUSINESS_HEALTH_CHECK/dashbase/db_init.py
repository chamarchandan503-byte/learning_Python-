"""
Database Initialization & Seeding Module.
Populates standard admin accounts, catalog products with diverse inventory health statuses,
sample verified customers, realistic orders, and inventory audit trails.
"""

import random
from datetime import datetime, timedelta
from dashbase.models import db, User, Customer, Product, Order, OrderItem, Payment, InventoryAuditLog

def init_database(app):
    """
    Initialize database schema and seed realistic operational data.
    Ensures safe, idempotent execution on application startup.
    """
    with app.app_context():
        # Create all tables matching models schema
        db.create_all()

        # 1. Seed Administrator and Manager Users
        if not User.query.first():
            print("[INFO] Creating default administrative credentials...")
            admin_user = User(
                username='admin',
                email='admin@ecommerce.com',
                role='Admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)

            manager_user = User(
                username='manager',
                email='manager@ecommerce.com',
                role='Manager'
            )
            manager_user.set_password('manager123')
            db.session.add(manager_user)
            db.session.commit()

        # 2. Seed Sample Customers
        if not Customer.query.first():
            print("[INFO] Populating verified customer profiles...")
            sample_customers = [
                Customer(name='Aarav Sharma', email='aarav.sharma@example.com', phone='+91 9876543210', address='402, Lotus Towers, Andheri West', city='Mumbai'),
                Customer(name='Priya Patel', email='priya.patel@example.com', phone='+91 9823456789', address='15, Green Park Society, Satellite', city='Ahmedabad'),
                Customer(name='Rohan Verma', email='rohan.verma@example.com', phone='+91 9712345678', address='88, Brigade Road, Ashok Nagar', city='Bengaluru'),
                Customer(name='Sneha Kulkarni', email='sneha.k@example.com', phone='+91 9934567890', address='22, FC Road, Shivajinagar', city='Pune'),
                Customer(name='Vikram Malhotra', email='vikram.m@example.com', phone='+91 9845678901', address='104, Connaught Place', city='New Delhi'),
                Customer(name='Ananya Iyer', email='ananya.iyer@example.com', phone='+91 9756789012', address='12, Anna Salai, T. Nagar', city='Chennai'),
            ]
            db.session.add_all(sample_customers)
            db.session.commit()

        # 3. Seed Products with Various Inventory Health States
        if not Product.query.first():
            print("[INFO] Seeding catalog products and stock levels...")
            sample_products = [
                Product(name='Wireless Noise-Canceling Headphones', sku='ELEC-WNH-001', category='Electronics', price=4999.00, cost_price=3100.00, stock=28, min_stock_level=8, description='Premium active noise cancelling over-ear wireless headphones.'),
                Product(name='Smart Fitness Watch Pro', sku='ELEC-SFW-002', category='Electronics', price=2999.00, cost_price=1750.00, stock=4, min_stock_level=10, description='AMOLED waterproof smartwatch with comprehensive health sensors.'),  # Low stock
                Product(name='Ergonomic Mesh Office Chair', sku='FURN-EOC-003', category='Furniture', price=7499.00, cost_price=4400.00, stock=15, min_stock_level=5, description='High-back breathable mesh ergonomic chair with lumbar adjustment.'),
                Product(name='Mechanical RGB Gaming Keyboard', sku='ELEC-MGK-004', category='Electronics', price=3499.00, cost_price=2050.00, stock=20, min_stock_level=6, description='Custom tactile mechanical gaming keyboard with programmable backlight.'),
                Product(name='Stainless Steel Vacuum Flask (1L)', sku='HOME-SSF-005', category='Home & Kitchen', price=899.00, cost_price=420.00, stock=45, min_stock_level=12, description='Double-walled insulated flask keeping temperatures for 24 hours.'),
                Product(name='Organic Arabica Coffee Beans (500g)', sku='GROC-OAC-006', category='Grocery', price=599.00, cost_price=300.00, stock=3, min_stock_level=10, description='Freshly roasted single-origin medium roast whole beans.'),  # Low stock
                Product(name='Fast 65W GaN Charger Adapter', sku='ELEC-FGC-007', category='Electronics', price=1499.00, cost_price=780.00, stock=0, min_stock_level=8, description='Ultra-compact gallium nitride laptop & phone fast charger.'),  # Out of stock
                Product(name='Premium Cotton Polo T-Shirt', sku='APPA-PCT-008', category='Apparel', price=999.00, cost_price=450.00, stock=60, min_stock_level=15, description='100% combed cotton classic comfort regular fit polo.'),
                Product(name='Ceramic Nonstick Frying Pan 28cm', sku='HOME-CNP-009', category='Home & Kitchen', price=1799.00, cost_price=950.00, stock=11, min_stock_level=5, description='Toxin-free durable ceramic coating compatible with induction.'),
                Product(name='Wireless Vertical Ergonomic Mouse', sku='ELEC-WVM-010', category='Electronics', price=1299.00, cost_price=680.00, stock=2, min_stock_level=6, description='Ergonomically contoured vertical mouse preventing wrist strain.'),  # Low stock
            ]
            db.session.add_all(sample_products)
            db.session.commit()

            # Create initial audit log for baseline inventory
            for p in sample_products:
                db.session.add(InventoryAuditLog(
                    product_id=p.id,
                    change_qty=p.stock,
                    previous_stock=0,
                    new_stock=p.stock,
                    action_type='RESTOCK',
                    reason='Initial system catalog setup baseline stock'
                ))
            db.session.commit()

        # 4. Seed Initial Orders and Financial Transactions
        if not Order.query.first():
            print("[INFO] Generating baseline orders and financial reconciliations...")
            customers = Customer.query.all()
            products = Product.query.all()
            now = datetime.utcnow()
            payment_methods = ['UPI', 'Credit Card', 'Net Banking', 'Cash']

            for i in range(1, 11):
                order_date = now - timedelta(days=random.randint(0, 22), hours=random.randint(1, 16))
                cust = random.choice(customers)
                order_num = f"ORD-{now.year}{i:04d}"
                status = 'Completed' if i <= 7 else ('Processing' if i <= 9 else 'Pending')

                selected_prods = random.sample(products, random.randint(1, 3))
                subtotal = 0.0

                order = Order(
                    order_number=order_num,
                    customer_id=cust.id,
                    order_date=order_date,
                    status=status,
                    shipping_address=f"{cust.address}, {cust.city}"
                )
                db.session.add(order)
                db.session.flush()

                for prod in selected_prods:
                    qty = random.randint(1, 2)
                    line_total = prod.price * qty
                    subtotal += line_total

                    db.session.add(OrderItem(
                        order_id=order.id,
                        product_id=prod.id,
                        quantity=qty,
                        unit_price=prod.price,
                        total_price=line_total
                    ))

                tax_amount = round(subtotal * 0.18, 2)
                order.subtotal = round(subtotal, 2)
                order.tax_amount = tax_amount
                order.total_amount = round(subtotal + tax_amount, 2)

                # Record payment for settled or processing orders
                if status in ['Completed', 'Processing']:
                    pay_method = random.choice(payment_methods)
                    db.session.add(Payment(
                        order_id=order.id,
                        payment_method=pay_method,
                        amount=order.total_amount,
                        payment_status='Completed',
                        transaction_id=f"TXN-{random.randint(10000000, 99999999)}",
                        payment_date=order_date + timedelta(minutes=random.randint(5, 30))
                    ))

            db.session.commit()
            print("[SUCCESS] Database initialization completed with zero schema errors.")


if __name__ == '__main__':
    from flask import Flask
    from config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    init_database(app)
    print("Database ready.")
