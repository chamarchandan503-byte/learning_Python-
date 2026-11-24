"""
Main Application Entry Point.
Initializes Flask app instance, extensions, database schemas,
security sessions, blueprints, and global context variables.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import Config
from dashbase.models import db, User, Customer, Product, Order, Payment
from dashbase.db_init import init_database

# Blueprints
from modules.customers import customers_bp
from modules.products import products_bp
from modules.orders import orders_bp
from modules.payments import payments_bp
from modules.inventory import inventory_bp
from reports.sales_report import reports_bp

# Configure standard application logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('ecommerce_app')


def create_app():
    """Application factory for the E-Commerce Management System."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please sign in to access the system.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(customers_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)

    # Auto-initialize database tables and demo seed data on startup
    with app.app_context():
        init_database(app)

    # ------------------- Core App Routes -------------------

    @app.route('/')
    def index():
        """Root redirect to dashboard or login."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User authentication portal."""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember = True if request.form.get('remember') else False

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                user.last_login = datetime.utcnow()
                db.session.commit()
                login_user(user, remember=remember)
                flash(f'Welcome back, {user.username}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')

        return render_template('index.html')

    @app.route('/logout')
    @login_required
    def logout():
        """Terminate user session."""
        logout_user()
        flash('You have been logged out securely.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Executive Business Health Check Dashboard."""
        # Financial & Sales Metrics
        completed_orders = Order.query.filter(Order.status != 'Cancelled').all()
        total_revenue = round(sum(o.total_amount for o in completed_orders), 2)
        total_orders_count = Order.query.count()
        total_customers_count = Customer.query.count()
        total_products_count = Product.query.count()

        # Inventory Health Metrics
        low_stock_products = Product.query.filter(Product.stock <= Product.min_stock_level, Product.stock > 0).all()
        out_of_stock_products = Product.query.filter(Product.stock <= 0).all()
        healthy_products = Product.query.filter(Product.stock > Product.min_stock_level).all()

        # Business Health Score calculation (0 - 100)
        inv_score = 100
        if total_products_count > 0:
            stock_defect_rate = (len(out_of_stock_products) * 2 + len(low_stock_products)) / total_products_count
            inv_score = max(20, round(100 - (stock_defect_rate * 50)))

        fulfillment_score = 95
        cancelled_count = Order.query.filter_by(status='Cancelled').count()
        if total_orders_count > 0:
            fulfillment_score = round(((total_orders_count - cancelled_count) / total_orders_count) * 100)

        health_score = round((inv_score * 0.6) + (fulfillment_score * 0.4))

        # Recent activities
        recent_orders = Order.query.order_by(Order.order_date.desc()).limit(6).all()
        recent_payments = Payment.query.order_by(Payment.payment_date.desc()).limit(5).all()

        return render_template(
            'dashbosrd.html',
            total_revenue=total_revenue,
            total_orders=total_orders_count,
            total_customers=total_customers_count,
            total_products=total_products_count,
            low_stock_count=len(low_stock_products),
            out_of_stock_count=len(out_of_stock_products),
            healthy_count=len(healthy_products),
            health_score=health_score,
            low_stock_list=low_stock_products[:5],
            recent_orders=recent_orders,
            recent_payments=recent_payments
        )

    # Global context processor
    @app.context_processor
    def inject_global_data():
        if current_user.is_authenticated:
            low_stock_alerts = Product.query.filter(Product.stock <= Product.min_stock_level).count()
            pending_orders = Order.query.filter_by(status='Pending').count()
            return dict(
                global_low_stock_count=low_stock_alerts,
                global_pending_orders_count=pending_orders,
                now_year=datetime.utcnow().year
            )
        return dict(
            global_low_stock_count=0,
            global_pending_orders_count=0,
            now_year=datetime.utcnow().year
        )

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('dashbosrd.html', error_code=404, error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('dashbosrd.html', error_code=500, error_message="Internal Server Error"), 500

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
