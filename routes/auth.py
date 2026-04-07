import random
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from models.db import get_connection, is_allowed_ward

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form.get('mobile', '').strip()
        if len(mobile) != 10 or not mobile.isdigit():
            flash('Please enter a valid 10-digit mobile number.', 'error')
            return render_template('login.html')

        otp = str(random.randint(100000, 999999))
        session['pending_mobile'] = mobile
        session['otp'] = otp
        flash(f'OTP generated (demo): {otp}', 'info')
        return redirect(url_for('auth.verify_otp'))

    return render_template('login.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_mobile' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        name = request.form.get('name', '').strip() or 'Resident'
        ward = request.form.get('ward', '').strip()
        pincode = request.form.get('pincode', '').strip()

        if entered_otp != session.get('otp'):
            flash('Invalid OTP. Please try again.', 'error')
            return render_template('verify_otp.html')

        if not is_allowed_ward(ward, pincode):
            flash('Access denied. Only Khadia ward residents are allowed.', 'error')
            return render_template('verify_otp.html')

        conn = get_connection(current_app.config['DATABASE'])
        cursor = conn.cursor()

        mobile = session['pending_mobile']
        cursor.execute('SELECT * FROM users WHERE mobile = ?', (mobile,))
        user = cursor.fetchone()

        if user is None:
            cursor.execute(
                """
                INSERT INTO users (name, mobile, ward, pincode, role, created_at)
                VALUES (?, ?, ?, ?, 'user', ?)
                """,
                (name, mobile, ward or 'Khadia', pincode, datetime.utcnow().isoformat()),
            )
            conn.commit()
            cursor.execute('SELECT * FROM users WHERE mobile = ?', (mobile,))
            user = cursor.fetchone()

        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']

        session.pop('otp', None)
        session.pop('pending_mobile', None)

        conn.close()

        if user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('verify_otp.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
