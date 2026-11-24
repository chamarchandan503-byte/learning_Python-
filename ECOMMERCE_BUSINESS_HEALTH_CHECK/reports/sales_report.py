"""
Sales Reports and Business Analytics Blueprint.
Generates financial KPI summaries, CSV transaction exports,
and JSON data for dynamic Chart.js dashboards.
"""

import io
import csv
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, Response, jsonify
from flask_login import login_required
from sqlalchemy import func
from dashbase.models import db, Order, OrderItem, Product, Customer, Payment

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/sales')
@login_required
def sales_report():
    """Executive Sales Report with custom timeframe metrics."""
    period = request.args.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    start_date = datetime.utcnow() - timedelta(days=days)
    orders = Order.query.filter(Order.order_date >= start_date, Order.status != 'Cancelled').all()

    total_revenue = round(sum(o.total_amount for o in orders), 2)
    total_orders = len(orders)
    avg_order_value = round((total_revenue / total_orders) if total_orders > 0 else 0.0, 2)

    # Top Selling Products in timeframe
    top_items = (
        db.session.query(
            Product.name,
            Product.sku,
            Product.category,
            func.sum(OrderItem.quantity).label('total_qty'),
            func.sum(OrderItem.total_price).label('total_revenue')
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.order_date >= start_date, Order.status != 'Cancelled')
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    return render_template(
        'dashbosrd.html',
        is_report_view=True,
        selected_period=days,
        total_revenue=total_revenue,
        total_orders=total_orders,
        avg_order_value=avg_order_value,
        top_items=top_items
    )

@reports_bp.route('/export/csv')
@login_required
def export_csv():
    """Export complete order history into a downloadable CSV file."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Order Number',
        'Customer Name',
        'Customer Email',
        'Order Date',
        'Status',
        'Items Count',
        'Subtotal (INR)',
        'Tax Amount (INR)',
        'Total Amount (INR)',
        'Payment Status'
    ])

    orders = Order.query.order_by(Order.order_date.desc()).all()
    for o in orders:
        writer.writerow([
            o.order_number,
            o.customer.name if o.customer else 'N/A',
            o.customer.email if o.customer else 'N/A',
            o.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            o.status,
            o.total_items,
            f"{o.subtotal:.2f}",
            f"{o.tax_amount:.2f}",
            f"{o.total_amount:.2f}",
            o.payment_status
        ])

    output.seek(0)
    filename = f"sales_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@reports_bp.route('/api/analytics')
@login_required
def api_analytics():
    """JSON API providing structured metrics for Chart.js charts."""
    # 1. Monthly revenue over past 6 months
    monthly_data = {}
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month_label = (now - timedelta(days=i * 30)).strftime('%b %Y')
        monthly_data[month_label] = 0.0

    completed_orders = Order.query.filter(Order.status != 'Cancelled').all()
    for o in completed_orders:
        label = o.order_date.strftime('%b %Y')
        if label in monthly_data:
            monthly_data[label] = round(monthly_data[label] + o.total_amount, 2)

    # 2. Sales by Category
    category_sales = {}
    for item in OrderItem.query.all():
        if item.order and item.order.status != 'Cancelled' and item.product:
            cat = item.product.category or 'General'
            category_sales[cat] = round(category_sales.get(cat, 0.0) + item.total_price, 2)

    # 3. Order Status Breakdown
    status_counts = {
        'Completed': Order.query.filter_by(status='Completed').count(),
        'Processing': Order.query.filter_by(status='Processing').count(),
        'Pending': Order.query.filter_by(status='Pending').count(),
        'Cancelled': Order.query.filter_by(status='Cancelled').count()
    }

    # 4. Inventory Health status breakdown
    inventory_health = {
        'In Stock': Product.query.filter(Product.stock > Product.min_stock_level).count(),
        'Low Stock': Product.query.filter(Product.stock <= Product.min_stock_level, Product.stock > 0).count(),
        'Out of Stock': Product.query.filter(Product.stock <= 0).count()
    }

    return jsonify({
        'monthly_labels': list(monthly_data.keys()),
        'monthly_revenue': list(monthly_data.values()),
        'category_labels': list(category_sales.keys()),
        'category_values': list(category_sales.values()),
        'order_statuses': status_counts,
        'inventory_health': inventory_health
    })
