"""
Enterprise Database Models for Smart E-Commerce Management System.
Implements normalized relational models with business properties,
audit trails, and comprehensive data integrity constraints.
"""

from datetime import datetime
from typing import Dict, Any
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize global SQLAlchemy database instance
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """System Administrator, Manager, and Staff user credentials."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='Admin', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password: str) -> None:
        """Hash and persist user password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify user credentials against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self) -> str:
        return f"<User {self.username} [{self.role}]>"


class Customer(db.Model):
    """Customer accounts, profiles, and purchasing analytics."""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(25), nullable=True, index=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(80), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    orders = db.relationship('Order', backref='customer', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def total_orders(self) -> int:
        return self.orders.count()

    @property
    def total_spent(self) -> float:
        completed = self.orders.filter_by(status='Completed').all()
        return round(sum(o.total_amount for o in completed), 2)

    @property
    def average_order_value(self) -> float:
        count = self.orders.filter(Order.status != 'Cancelled').count()
        if count == 0:
            return 0.0
        return round(self.total_spent / count, 2)

    @property
    def customer_tier(self) -> str:
        spent = self.total_spent
        if spent >= 25000:
            return 'Platinum VIP'
        elif spent >= 10000:
            return 'Gold'
        elif spent >= 3000:
            return 'Silver'
        return 'Standard'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone or '',
            'address': self.address or '',
            'city': self.city or '',
            'total_orders': self.total_orders,
            'total_spent': self.total_spent,
            'tier': self.customer_tier
        }

    def __repr__(self) -> str:
        return f"<Customer {self.name} ({self.email})>"


class Product(db.Model):
    """Inventory catalog items, pricing structures, and stock thresholds."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    sku = db.Column(db.String(60), unique=True, nullable=False, index=True)
    category = db.Column(db.String(80), default='General', nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    cost_price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, nullable=False, default=5)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    audit_logs = db.relationship('InventoryAuditLog', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_out_of_stock(self) -> bool:
        return self.stock <= 0

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock <= self.min_stock_level

    @property
    def stock_status(self) -> str:
        if self.stock <= 0:
            return 'Out of Stock'
        elif self.stock <= self.min_stock_level:
            return 'Low Stock'
        return 'In Stock'

    @property
    def profit_margin_percent(self) -> float:
        if self.price <= 0:
            return 0.0
        profit = self.price - self.cost_price
        return round((profit / self.price) * 100, 1)

    @property
    def inventory_asset_value(self) -> float:
        return round(self.stock * self.price, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'price': self.price,
            'cost_price': self.cost_price,
            'stock': self.stock,
            'min_stock_level': self.min_stock_level,
            'status': self.stock_status,
            'description': self.description or ''
        }

    def __repr__(self) -> str:
        return f"<Product {self.name} (SKU: {self.sku})>"


class Order(db.Model):
    """Customer sales orders, fulfillment tracking, and financial breakdown."""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), default='Pending', nullable=False, index=True)  # Pending, Processing, Completed, Cancelled
    shipping_address = db.Column(db.Text, nullable=True)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='select', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='order', lazy='select', cascade='all, delete-orphan')

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def amount_paid(self) -> float:
        completed_payments = [p.amount for p in self.payments if p.payment_status == 'Completed']
        return round(sum(completed_payments), 2)

    @property
    def balance_due(self) -> float:
        return max(0.0, round(self.total_amount - self.amount_paid, 2))

    @property
    def payment_status(self) -> str:
        paid = self.amount_paid
        if paid >= self.total_amount and self.total_amount > 0:
            return 'Paid'
        elif paid > 0:
            return 'Partially Paid'
        return 'Unpaid'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer.name if self.customer else 'N/A',
            'order_date': self.order_date.strftime('%Y-%m-%d %H:%M'),
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_status': self.payment_status,
            'items_count': self.total_items
        }

    def __repr__(self) -> str:
        return f"<Order {self.order_number} ({self.status})>"


class OrderItem(db.Model):
    """Line items inside customer purchase orders."""
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self) -> str:
        return f"<OrderItem #{self.id} Order:{self.order_id} Prod:{self.product_id} Qty:{self.quantity}>"


class Payment(db.Model):
    """Financial transactions and payment reconciliations."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    payment_method = db.Column(db.String(50), nullable=False, index=True)  # UPI, Credit Card, Net Banking, Cash
    amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(db.String(30), default='Completed', nullable=False, index=True)  # Completed, Pending, Failed, Refunded
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'order_number': self.order.order_number if self.order else 'N/A',
            'amount': self.amount,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self) -> str:
        return f"<Payment {self.transaction_id} (₹{self.amount})>"


class InventoryAuditLog(db.Model):
    """Immutable audit trail for all stock movements and adjustments."""
    __tablename__ = 'inventory_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    change_qty = db.Column(db.Integer, nullable=False)
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # RESTOCK, ORDER_DEDUCT, ORDER_CANCEL_RESTORE, AUDIT
    reason = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<InventoryAuditLog Prod:{self.product_id} Change:{self.change_qty:+d} ({self.action_type})>"
