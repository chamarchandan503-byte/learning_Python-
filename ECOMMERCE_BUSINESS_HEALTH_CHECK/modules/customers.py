"""
Customer Management Blueprint.
Handles customer directory, profile updates, order analytics,
and customer relationship metrics.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from dashbase.models import db, Customer

logger = logging.getLogger(__name__)

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
@login_required
def list_customers():
    """List customer profiles with search and server-side pagination."""
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Customer.query

    if search_query:
        query = query.filter(
            (Customer.name.ilike(f"%{search_query}%")) |
            (Customer.email.ilike(f"%{search_query}%")) |
            (Customer.phone.ilike(f"%{search_query}%")) |
            (Customer.city.ilike(f"%{search_query}%"))
        )

    pagination = query.order_by(Customer.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items
    total_customers = Customer.query.count()

    return render_template(
        'customers.html',
        customers=customers,
        pagination=pagination,
        search_query=search_query,
        total_customers=total_customers
    )

@customers_bp.route('/add', methods=['POST'])
@login_required
def add_customer():
    """Create a new verified customer profile."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()

    if not name or not email:
        flash('Customer name and email are mandatory.', 'danger')
        return redirect(url_for('customers.list_customers'))

    if '@' not in email or '.' not in email:
        flash('Please enter a valid email address.', 'danger')
        return redirect(url_for('customers.list_customers'))

    # Check for duplicate email
    if Customer.query.filter_by(email=email).first():
        flash(f'A customer profile with email "{email}" already exists.', 'warning')
        return redirect(url_for('customers.list_customers'))

    new_cust = Customer(
        name=name,
        email=email,
        phone=phone,
        address=address,
        city=city
    )

    try:
        db.session.add(new_cust)
        db.session.commit()
        flash(f'Customer "{name}" registered successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering customer: {str(e)}")
        flash('An internal error occurred while registering the customer.', 'danger')

    return redirect(url_for('customers.list_customers'))

@customers_bp.route('/edit/<int:customer_id>', methods=['POST'])
@login_required
def edit_customer(customer_id):
    """Update existing customer profile details."""
    customer = Customer.query.get_or_404(customer_id)

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    city = request.form.get('city', '').strip()

    if not name or not email:
        flash('Customer name and email cannot be empty.', 'danger')
        return redirect(url_for('customers.list_customers'))

    # Check email collision with other customer records
    collision = Customer.query.filter(Customer.email == email, Customer.id != customer_id).first()
    if collision:
        flash(f'Email "{email}" is already used by another customer.', 'warning')
        return redirect(url_for('customers.list_customers'))

    customer.name = name
    customer.email = email
    customer.phone = phone
    customer.address = address
    customer.city = city

    try:
        db.session.commit()
        flash(f'Customer "{name}" updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        flash('Failed to update customer details.', 'danger')

    return redirect(url_for('customers.list_customers'))

@customers_bp.route('/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    """Delete a customer record."""
    customer = Customer.query.get_or_404(customer_id)
    cust_name = customer.name
    try:
        db.session.delete(customer)
        db.session.commit()
        flash(f'Customer "{cust_name}" deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting customer {customer_id}: {str(e)}")
        flash('Could not delete customer because they have related order records.', 'danger')

    return redirect(url_for('customers.list_customers'))

@customers_bp.route('/api/<int:customer_id>')
@login_required
def get_customer_api(customer_id):
    """Fetch customer profile data for AJAX modals."""
    customer = Customer.query.get_or_404(customer_id)
    return jsonify(customer.to_dict())
