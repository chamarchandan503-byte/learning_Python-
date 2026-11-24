"""
Inventory & Stock Management Blueprint.
Core module for Business Health Checks, inventory valuation,
low-stock risk assessment, and stock audit logging.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from dashbase.models import db, Product, InventoryAuditLog

logger = logging.getLogger(__name__)

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
def inventory_dashboard():
    """Stock Management & Business Inventory Health Check overview."""
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Product.query

    if search_query:
        query = query.filter(
            (Product.name.ilike(f"%{search_query}%")) |
            (Product.sku.ilike(f"%{search_query}%"))
        )

    if category_filter:
        query = query.filter(Product.category == category_filter)

    if status_filter == 'out':
        query = query.filter(Product.stock <= 0)
    elif status_filter == 'low':
        query = query.filter(Product.stock <= Product.min_stock_level, Product.stock > 0)
    elif status_filter == 'healthy':
        query = query.filter(Product.stock > Product.min_stock_level)

    pagination = query.order_by(Product.stock.asc()).paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    # Business Health Computations
    all_products = Product.query.all()
    total_items = len(all_products)
    out_of_stock_items = [p for p in all_products if p.is_out_of_stock]
    low_stock_items = [p for p in all_products if p.is_low_stock]
    healthy_items = [p for p in all_products if not p.is_low_stock and not p.is_out_of_stock]

    total_stock_units = sum(p.stock for p in all_products)
    total_inventory_value = sum(p.stock * p.price for p in all_products)
    total_cost_value = sum(p.stock * p.cost_price for p in all_products)

    # Health Index Calculation
    health_score = 100
    if total_items > 0:
        penalty = (len(out_of_stock_items) / total_items * 60) + (len(low_stock_items) / total_items * 30)
        health_score = max(0, min(100, round(100 - penalty)))

    categories = sorted(list(set(p.category for p in all_products if p.category)))
    recent_audits = InventoryAuditLog.query.order_by(InventoryAuditLog.timestamp.desc()).limit(10).all()

    return render_template(
        'inventory.html',
        products=products,
        pagination=pagination,
        categories=categories,
        total_items=total_items,
        out_of_stock_count=len(out_of_stock_items),
        low_stock_count=len(low_stock_items),
        healthy_count=len(healthy_items),
        total_stock_units=total_stock_units,
        total_inventory_value=total_inventory_value,
        total_cost_value=total_cost_value,
        health_score=health_score,
        recent_audits=recent_audits,
        selected_status=status_filter,
        selected_category=category_filter,
        search_query=search_query
    )

@inventory_bp.route('/adjust-stock', methods=['POST'])
@login_required
def adjust_stock():
    """Perform stock adjustments with automatic immutable audit logging."""
    product_id = request.form.get('product_id')
    adjustment_type = request.form.get('adjustment_type', 'add')
    quantity_raw = request.form.get('quantity', '0')
    reason = request.form.get('reason', 'Routine Restock').strip()

    product = Product.query.get_or_404(product_id)

    try:
        qty = int(quantity_raw)
        if qty < 0:
            flash('Quantity must be positive.', 'danger')
            return redirect(url_for('inventory.inventory_dashboard'))
    except ValueError:
        flash('Invalid quantity.', 'danger')
        return redirect(url_for('inventory.inventory_dashboard'))

    old_stock = product.stock

    if adjustment_type == 'add':
        product.stock += qty
        diff = qty
        action = 'RESTOCK'
    elif adjustment_type == 'subtract':
        if product.stock < qty:
            flash(f'Cannot deduct {qty} units. Current stock is only {product.stock}.', 'danger')
            return redirect(url_for('inventory.inventory_dashboard'))
        product.stock -= qty
        diff = -qty
        action = 'DAMAGE_WRITE_OFF'
    elif adjustment_type == 'set':
        diff = qty - product.stock
        product.stock = qty
        action = 'AUDIT_CORRECTION'
    else:
        diff = 0
        action = 'AUDIT'

    # Record Audit Log
    db.session.add(InventoryAuditLog(
        product_id=product.id,
        change_qty=diff,
        previous_stock=old_stock,
        new_stock=product.stock,
        action_type=action,
        reason=reason
    ))

    try:
        db.session.commit()
        flash(f'Stock updated for "{product.name}": {old_stock} → {product.stock} units ({reason}).', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adjusting stock: {str(e)}")
        flash('Failed to adjust stock.', 'danger')

    return redirect(url_for('inventory.inventory_dashboard'))

@inventory_bp.route('/update-threshold', methods=['POST'])
@login_required
def update_threshold():
    """Update low-stock alert threshold for a product."""
    product_id = request.form.get('product_id')
    new_threshold_raw = request.form.get('min_stock_level', '5')

    product = Product.query.get_or_404(product_id)

    try:
        product.min_stock_level = max(0, int(new_threshold_raw))
        db.session.commit()
        flash(f'Low stock alert threshold for "{product.name}" updated to {product.min_stock_level}.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating threshold: {str(e)}")
        flash('Failed to update threshold.', 'danger')

    return redirect(url_for('inventory.inventory_dashboard'))
