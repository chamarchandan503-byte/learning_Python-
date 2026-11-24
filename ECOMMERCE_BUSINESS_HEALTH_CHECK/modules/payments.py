"""
Payment Management Blueprint.
Handles payment transactions, reconciliations, payment method statistics,
and customer invoice receipts.
"""

import random
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from dashbase.models import db, Payment, Order

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/')
@login_required
def list_payments():
    """List payment records with search, filters, and server-side pagination."""
    method_filter = request.args.get('method', '').strip()
    status_filter = request.args.get('status', '').strip()
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Payment.query.join(Order)

    if method_filter:
        query = query.filter(Payment.payment_method == method_filter)

    if status_filter:
        query = query.filter(Payment.payment_status == status_filter)

    if search_query:
        query = query.filter(
            (Payment.transaction_id.ilike(f"%{search_query}%")) |
            (Order.order_number.ilike(f"%{search_query}%"))
        )

    pagination = query.order_by(Payment.payment_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    payments = pagination.items

    total_received = sum(p.amount for p in Payment.query.filter_by(payment_status='Completed').all())
    pending_amount = sum(p.amount for p in Payment.query.filter_by(payment_status='Pending').all())
    total_transactions = Payment.query.count()

    unpaid_orders = Order.query.filter(Order.status != 'Cancelled').order_by(Order.order_date.desc()).all()

    return render_template(
        'payments.html',
        payments=payments,
        pagination=pagination,
        unpaid_orders=unpaid_orders,
        total_received=total_received,
        pending_amount=pending_amount,
        total_transactions=total_transactions,
        selected_method=method_filter,
        selected_status=status_filter,
        search_query=search_query
    )

@payments_bp.route('/record', methods=['POST'])
@login_required
def record_payment():
    """Record payment for an order and auto-update order status upon full settlement."""
    order_id = request.form.get('order_id')
    payment_method = request.form.get('payment_method', 'UPI')
    amount_raw = request.form.get('amount', '0')
    payment_status = request.form.get('payment_status', 'Completed')

    if not order_id:
        flash('Please select an order to apply the payment.', 'danger')
        return redirect(url_for('payments.list_payments'))

    order = Order.query.get(order_id)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('payments.list_payments'))

    try:
        amount = max(0.01, float(amount_raw))
    except ValueError:
        flash('Invalid numeric amount.', 'danger')
        return redirect(url_for('payments.list_payments'))

    txn_id = f"TXN-{random.randint(10000000, 99999999)}"

    new_payment = Payment(
        order_id=order.id,
        payment_method=payment_method,
        amount=amount,
        payment_status=payment_status,
        transaction_id=txn_id,
        payment_date=datetime.utcnow()
    )

    try:
        db.session.add(new_payment)

        # Update order status if paid
        if payment_status == 'Completed':
            existing_paid = order.amount_paid
            if (existing_paid + amount) >= order.total_amount and order.status == 'Pending':
                order.status = 'Processing'

        db.session.commit()
        flash(f'Payment of ₹{amount:,.2f} recorded successfully (Txn ID: {txn_id}).', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving payment: {str(e)}")
        flash('Failed to record payment.', 'danger')

    return redirect(url_for('payments.list_payments'))

@payments_bp.route('/update-status/<int:payment_id>', methods=['POST'])
@login_required
def update_status(payment_id):
    """Update transaction settlement status."""
    payment = Payment.query.get_or_404(payment_id)
    new_status = request.form.get('status')

    valid_statuses = ['Completed', 'Pending', 'Failed', 'Refunded']
    if new_status in valid_statuses:
        payment.payment_status = new_status
        try:
            db.session.commit()
            flash(f'Transaction {payment.transaction_id} marked as {new_status}.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating payment: {str(e)}")
            flash('Error updating transaction.', 'danger')
    else:
        flash('Invalid transaction status.', 'danger')

    return redirect(url_for('payments.list_payments'))
