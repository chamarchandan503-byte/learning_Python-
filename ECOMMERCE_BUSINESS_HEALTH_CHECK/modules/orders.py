"""
Order Management Blueprint.
Handles multi-item order creation, atomic stock deduction,
fulfillment lifecycle, tax calculation, and invoicing.
"""

import random
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from dashbase.models import db, Order, OrderItem, Customer, Product, Payment, InventoryAuditLog

logger = logging.getLogger(__name__)

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/')
@login_required
def list_orders():
    """List orders with server-side pagination, status filters, and search."""
    status_filter = request.args.get('status', '').strip()
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Order.query.join(Customer)

    if status_filter:
        query = query.filter(Order.status == status_filter)

    if search_query:
        query = query.filter(
            (Order.order_number.ilike(f"%{search_query}%")) |
            (Customer.name.ilike(f"%{search_query}%")) |
            (Customer.email.ilike(f"%{search_query}%"))
        )

    pagination = query.order_by(Order.order_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    total_orders = Order.query.count()
    pending_count = Order.query.filter_by(status='Pending').count()
    completed_count = Order.query.filter_by(status='Completed').count()
    total_sales = sum(o.total_amount for o in Order.query.filter(Order.status != 'Cancelled').all())

    all_customers = Customer.query.order_by(Customer.name.asc()).all()
    all_products = Product.query.filter(Product.stock > 0).order_by(Product.name.asc()).all()

    return render_template(
        'orders.html',
        orders=orders,
        pagination=pagination,
        customers=all_customers,
        products=all_products,
        total_orders=total_orders,
        pending_count=pending_count,
        completed_count=completed_count,
        total_sales=total_sales,
        selected_status=status_filter,
        search_query=search_query
    )

@orders_bp.route('/create', methods=['POST'])
@login_required
def create_order():
    """Create a new order with atomic stock deduction and audit logging."""
    customer_id = request.form.get('customer_id')
    shipping_address = request.form.get('shipping_address', '').strip()
    payment_method = request.form.get('payment_method', 'Cash')
    mark_paid = request.form.get('mark_paid') == 'on'

    product_ids = request.form.getlist('product_id[]')
    quantities = request.form.getlist('quantity[]')

    if not customer_id:
        flash('Please select a customer for the order.', 'danger')
        return redirect(url_for('orders.list_orders'))

    customer = Customer.query.get(customer_id)
    if not customer:
        flash('Selected customer does not exist.', 'danger')
        return redirect(url_for('orders.list_orders'))

    if not product_ids or not quantities:
        flash('Please add at least one product item to the order.', 'danger')
        return redirect(url_for('orders.list_orders'))

    # Validate stock availability for ALL selected items first
    items_to_process = []
    for p_id_str, qty_str in zip(product_ids, quantities):
        try:
            p_id = int(p_id_str)
            qty = int(qty_str)
        except (ValueError, TypeError):
            continue

        if qty <= 0:
            continue

        prod = Product.query.get(p_id)
        if not prod:
            continue

        if prod.stock < qty:
            flash(f'Insufficient stock for "{prod.name}". Available: {prod.stock}, Requested: {qty}', 'danger')
            return redirect(url_for('orders.list_orders'))

        items_to_process.append((prod, qty))

    if not items_to_process:
        flash('No valid items were selected.', 'danger')
        return redirect(url_for('orders.list_orders'))

    now = datetime.utcnow()
    order_number = f"ORD-{now.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

    new_order = Order(
        order_number=order_number,
        customer_id=customer.id,
        order_date=now,
        status='Completed' if mark_paid else 'Pending',
        shipping_address=shipping_address or customer.address or customer.city
    )

    try:
        db.session.add(new_order)
        db.session.flush()

        subtotal = 0.0
        for prod, qty in items_to_process:
            # Atomic stock deduction
            prev_stock = prod.stock
            prod.stock -= qty
            line_total = round(prod.price * qty, 2)
            subtotal += line_total

            # Add OrderItem
            db.session.add(OrderItem(
                order_id=new_order.id,
                product_id=prod.id,
                quantity=qty,
                unit_price=prod.price,
                total_price=line_total
            ))

            # Audit Log for stock deduction
            db.session.add(InventoryAuditLog(
                product_id=prod.id,
                change_qty=-qty,
                previous_stock=prev_stock,
                new_stock=prod.stock,
                action_type='ORDER_DEDUCT',
                reason=f'Sold via Order #{order_number}'
            ))

        tax_amount = round(subtotal * 0.18, 2)
        total_amount = round(subtotal + tax_amount, 2)

        new_order.subtotal = subtotal
        new_order.tax_amount = tax_amount
        new_order.total_amount = total_amount

        # Record immediate payment if requested
        if mark_paid and total_amount > 0:
            txn_id = f"TXN-{random.randint(10000000, 99999999)}"
            db.session.add(Payment(
                order_id=new_order.id,
                payment_method=payment_method,
                amount=total_amount,
                payment_status='Completed',
                transaction_id=txn_id,
                payment_date=now
            ))

        db.session.commit()
        flash(f'Order {order_number} created successfully! Total: ₹{total_amount:,.2f}', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating order: {str(e)}")
        flash('An internal error occurred while creating the order.', 'danger')

    return redirect(url_for('orders.list_orders'))

@orders_bp.route('/update-status/<int:order_id>', methods=['POST'])
@login_required
def update_status(order_id):
    """Update order fulfillment status with automatic stock return upon cancellation."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    valid_statuses = ['Pending', 'Processing', 'Completed', 'Cancelled']
    if new_status not in valid_statuses:
        flash('Invalid status chosen.', 'danger')
        return redirect(url_for('orders.list_orders'))

    try:
        # If transitioning to Cancelled, return stock
        if new_status == 'Cancelled' and order.status != 'Cancelled':
            for item in order.items:
                prod = item.product
                if prod:
                    prev_stock = prod.stock
                    prod.stock += item.quantity
                    db.session.add(InventoryAuditLog(
                        product_id=prod.id,
                        change_qty=item.quantity,
                        previous_stock=prev_stock,
                        new_stock=prod.stock,
                        action_type='ORDER_CANCEL_RESTORE',
                        reason=f'Order #{order.order_number} cancelled by admin'
                    ))
            flash(f'Order {order.order_number} cancelled and items returned to stock.', 'warning')
        elif order.status == 'Cancelled' and new_status != 'Cancelled':
            # Re-deduct stock
            for item in order.items:
                prod = item.product
                if prod and prod.stock >= item.quantity:
                    prev_stock = prod.stock
                    prod.stock -= item.quantity
                    db.session.add(InventoryAuditLog(
                        product_id=prod.id,
                        change_qty=-item.quantity,
                        previous_stock=prev_stock,
                        new_stock=prod.stock,
                        action_type='ORDER_DEDUCT',
                        reason=f'Order #{order.order_number} reactivated'
                    ))
                else:
                    flash(f'Cannot reactivate order: insufficient stock for {prod.name}.', 'danger')
                    return redirect(url_for('orders.list_orders'))

        order.status = new_status
        db.session.commit()
        flash(f'Order {order.order_number} status updated to {new_status}.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating order status: {str(e)}")
        flash('Failed to update order status.', 'danger')

    return redirect(url_for('orders.list_orders'))

@orders_bp.route('/delete/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    """Delete an order."""
    order = Order.query.get_or_404(order_id)
    order_num = order.order_number
    try:
        db.session.delete(order)
        db.session.commit()
        flash(f'Order {order_num} has been deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting order: {str(e)}")
        flash('Could not delete order.', 'danger')

    return redirect(url_for('orders.list_orders'))
