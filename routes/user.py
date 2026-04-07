import os
from datetime import datetime
from uuid import uuid4

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from models.db import detect_priority, get_connection, suggest_category

user_bp = Blueprint('user', __name__, url_prefix='/user')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def login_required():
    return session.get('user_id') and session.get('role') in {'user', 'admin'}


def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@user_bp.route('/dashboard')
def dashboard():
    if not login_required():
        return redirect(url_for('auth.login'))

    conn = get_connection(current_app.config['DATABASE'])
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM complaints WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],),
    )
    complaints = cursor.fetchall()

    cursor.execute(
        'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
        (session['user_id'],),
    )
    notifications = cursor.fetchall()

    conn.close()
    return render_template('user_dashboard.html', complaints=complaints, notifications=notifications)


@user_bp.route('/complaint/new', methods=['GET', 'POST'])
def new_complaint():
    if not login_required():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip() or 'Other'
        location_text = request.form.get('location_text', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()

        if not title or not description:
            flash('Title and description are required.', 'error')
            return render_template('new_complaint.html')

        ai_text = f'{title} {description}'
        suggested_category = suggest_category(ai_text)
        priority = detect_priority(ai_text)

        image = request.files.get('image')
        image_filename = None
        if image and image.filename:
            if not is_allowed_file(image.filename):
                flash('Invalid image file type.', 'error')
                return render_template('new_complaint.html')

            extension = image.filename.rsplit('.', 1)[1].lower()
            image_filename = secure_filename(f"{uuid4().hex}.{extension}")
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))

        now = datetime.utcnow().isoformat()
        conn = get_connection(current_app.config['DATABASE'])
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO complaints
            (user_id, title, description, category, suggested_category, priority, status,
             location_text, latitude, longitude, image_filename, assigned_to, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session['user_id'],
                title,
                description,
                category,
                suggested_category,
                priority,
                location_text,
                latitude,
                longitude,
                image_filename,
                None,
                now,
                now,
            ),
        )

        complaint_id = cursor.lastrowid
        cursor.execute(
            'INSERT INTO complaint_updates (complaint_id, note, created_at) VALUES (?, ?, ?)',
            (complaint_id, 'Complaint submitted successfully.', now),
        )

        conn.commit()
        conn.close()

        flash('Complaint submitted successfully.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('new_complaint.html')


@user_bp.route('/complaint/<int:complaint_id>')
def complaint_detail(complaint_id):
    if not login_required():
        return redirect(url_for('auth.login'))

    conn = get_connection(current_app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM complaints WHERE id = ? AND user_id = ?',
        (complaint_id, session['user_id']),
    )
    complaint = cursor.fetchone()

    if complaint is None:
        conn.close()
        flash('Complaint not found.', 'error')
        return redirect(url_for('user.dashboard'))

    cursor.execute(
        'SELECT * FROM complaint_updates WHERE complaint_id = ? ORDER BY created_at ASC',
        (complaint_id,),
    )
    updates = cursor.fetchall()
    conn.close()

    return render_template('complaint_detail.html', complaint=complaint, updates=updates)


@user_bp.route('/ai/suggest-category', methods=['POST'])
def ai_suggest_category():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    category = suggest_category(text)
    priority = detect_priority(text)
    return jsonify({'suggested_category': category, 'priority': priority})
