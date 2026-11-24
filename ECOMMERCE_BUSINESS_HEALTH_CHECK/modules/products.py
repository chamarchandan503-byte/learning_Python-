"""
Product Management Blueprint.
Handles catalog items, SKU generation, pricing rules,
inventory alerts, and stock audit logging.
"""

import uuid
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from dashbase.models import db, Product, InventoryAuditLog

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/')
@login_required
def list_products():
    """List products with search, category filtering, stock health, and pagination."""
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    stock_filter = request.args.get('stock_status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Product.query

    if search_query:
        query = query.filter(
            (Product.name.ilike(f"%{search_query}%")) |
            (Product.sku.ilike(f"%{search_query}%")) |
            (Product.description.ilike(f"%{search_query}%"))
        )

    if category_filter:
        query = query.filter(Product.category == category_filter)

    if stock_filter == 'low':
        query = query.filter(Product.stock <= Product.min_stock_level, Product.stock > 0)
    elif stock_filter == 'out':
        query = query.filter(Product.stock <= 0)
    elif stock_filter == 'in':
        query = query.filter(Product.stock > Product.min_stock_level)

    pagination = query.order_by(Product.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    all_categories = sorted(list(set(p.category for p in Product.query.with_entities(Product.category).all() if p.category)))
    total_products = Product.query.count()
    low_stock_count = Product.query.filter(Product.stock <= Product.min_stock_level, Product.stock > 0).count()
    out_of_stock_count = Product.query.filter(Product.stock <= 0).count()

    return render_template(
        'products.html',
        products=products,
        pagination=pagination,
        categories=all_categories,
        search_query=search_query,
        selected_category=category_filter,
        selected_stock=stock_filter,
        total_products=total_products,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count
    )

@products_bp.route('/add', methods=['POST'])
@login_required
def add_product():
    """Register a new product in catalog with initial inventory audit log."""
    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip().upper()
    category = request.form.get('category', 'General').strip() or 'General'
    price_raw = request.form.get('price', '0')
    cost_price_raw = request.form.get('cost_price', '0')
    stock_raw = request.form.get('stock', '0')
    min_stock_raw = request.form.get('min_stock_level', '5')
    description = request.form.get('description', '').strip()

    if not name:
        flash('Product name is required.', 'danger')
        return redirect(url_for('products.list_products'))

    # Auto-generate unique SKU if blank
    if not sku:
        prefix = ''.join(c for c in category[:4] if c.isalnum()).upper() or 'PROD'
        sku = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"

    if Product.query.filter_by(sku=sku).first():
        flash(f'A product with SKU "{sku}" already exists.', 'warning')
        return redirect(url_for('products.list_products'))

    try:
        price = max(0.0, float(price_raw))
        cost_price = max(0.0, float(cost_price_raw)) if cost_price_raw else 0.0
        stock = max(0, int(stock_raw))
        min_stock = max(0, int(min_stock_raw)) if min_stock_raw else 5
    except ValueError:
        flash('Invalid numeric format for price, cost, or stock.', 'danger')
        return redirect(url_for('products.list_products'))

    new_prod = Product(
        name=name,
        sku=sku,
        category=category,
        price=price,
        cost_price=cost_price,
        stock=stock,
        min_stock_level=min_stock,
        description=description
    )

    try:
        db.session.add(new_prod)
        db.session.flush()

        # Log initial inventory baseline
        db.session.add(InventoryAuditLog(
            product_id=new_prod.id,
            change_qty=stock,
            previous_stock=0,
            new_stock=stock,
            action_type='RESTOCK',
            reason='Initial catalog item addition'
        ))

        db.session.commit()
        flash(f'Product "{name}" (SKU: {sku}) added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding product: {str(e)}")
        flash('An error occurred while saving the product.', 'danger')

    return redirect(url_for('products.list_products'))

@products_bp.route('/edit/<int:product_id>', methods=['POST'])
@login_required
def edit_product(product_id):
    """Update product details and log inventory adjustments."""
    product = Product.query.get_or_404(product_id)

    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip().upper()
    category = request.form.get('category', 'General').strip() or 'General'
    price_raw = request.form.get('price', '0')
    cost_price_raw = request.form.get('cost_price', '0')
    stock_raw = request.form.get('stock', '0')
    min_stock_raw = request.form.get('min_stock_level', '5')
    description = request.form.get('description', '').strip()

    if not name or not sku:
        flash('Product name and SKU cannot be empty.', 'danger')
        return redirect(url_for('products.list_products'))

    collision = Product.query.filter(Product.sku == sku, Product.id != product_id).first()
    if collision:
        flash(f'SKU "{sku}" is already assigned to another product.', 'warning')
        return redirect(url_for('products.list_products'))

    try:
        new_price = max(0.0, float(price_raw))
        new_cost = max(0.0, float(cost_price_raw)) if cost_price_raw else 0.0
        new_stock = max(0, int(stock_raw))
        new_min = max(0, int(min_stock_raw)) if min_stock_raw else 5

        # Check if stock changed
        if new_stock != product.stock:
            diff = new_stock - product.stock
            db.session.add(InventoryAuditLog(
                product_id=product.id,
                change_qty=diff,
                previous_stock=product.stock,
                new_stock=new_stock,
                action_type='AUDIT',
                reason='Manual inventory count adjustment in Product Editor'
            ))

        product.name = name
        product.sku = sku
        product.category = category
        product.price = new_price
        product.cost_price = new_cost
        product.stock = new_stock
        product.min_stock_level = new_min
        product.description = description

        db.session.commit()
        flash(f'Product "{name}" updated successfully.', 'success')
    except ValueError:
        flash('Invalid numeric inputs.', 'danger')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing product {product_id}: {str(e)}")
        flash('Failed to update product details.', 'danger')

    return redirect(url_for('products.list_products'))

@products_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """Soft delete or delete product safely."""
    product = Product.query.get_or_404(product_id)
    name = product.name
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{name}" removed from inventory.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        flash('Cannot delete product because it is referenced in past order records.', 'danger')

    return redirect(url_for('products.list_products'))

@products_bp.route('/api/list')
@login_required
def api_products_list():
    """JSON list of catalog products for autocomplete or dynamic order creation."""
    products = Product.query.order_by(Product.name.asc()).all()
    return jsonify([p.to_dict() for p in products])
