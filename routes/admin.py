from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from models.db import get_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('q', '').strip()

    conn = get_connection(current_app.config['DATABASE'])
    cursor = conn.cursor()

    query = """
        SELECT c.*, u.name AS user_name, u.mobile AS user_mobile
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE 1=1
    """
    params = []

    if status_filter:
        query += ' AND c.status = ?'
        params.append(status_filter)

    if category_filter:
        query += ' AND c.category = ?'
        params.append(category_filter)

    if search_query:
        query += ' AND (c.title LIKE ? OR c.description LIKE ? OR u.name LIKE ? OR u.mobile LIKE ?)'
        like = f'%{search_query}%'
        params.extend([like, like, like, like])

    query += ' ORDER BY c.created_at DESC'

    cursor.execute(query, tuple(params))
    complaints = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) AS total FROM complaints')
    total = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM complaints WHERE status = 'Pending'")
    pending = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) AS total FROM complaints WHERE status = 'Resolved'")
    resolved = cursor.fetchone()['total']

    conn.close()

    return render_template(
        'admin_dashboard.html',
        complaints=complaints,
        total=total,
        pending=pending,
        resolved=resolved,
        status_filter=status_filter,
        category_filter=category_filter,
        search_query=search_query,
    )


@admin_bp.route('/complaint/<int:complaint_id>/update', methods=['POST'])
def update_complaint(complaint_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))

    status = request.form.get('status', 'Pending')
    assigned_to = request.form.get('assigned_to', '').strip()

    now = datetime.utcnow().isoformat()

    conn = get_connection(current_app.config['DATABASE'])
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,))
    complaint = cursor.fetchone()
    if complaint is None:
        conn.close()
        flash('Complaint not found.', 'error')
        return redirect(url_for('admin.dashboard'))

    cursor.execute(
        'UPDATE complaints SET status = ?, assigned_to = ?, updated_at = ? WHERE id = ?',
        (status, assigned_to, now, complaint_id),
    )

    update_note = f'Status updated to {status}'
    if assigned_to:
        update_note += f' and assigned to {assigned_to}'

    cursor.execute(
        'INSERT INTO complaint_updates (complaint_id, note, created_at) VALUES (?, ?, ?)',
        (complaint_id, update_note, now),
    )

    cursor.execute(
        'INSERT INTO notifications (user_id, complaint_id, message, is_read, created_at) VALUES (?, ?, ?, 0, ?)',
        (complaint['user_id'], complaint_id, update_note, now),
    )

    conn.commit()
    conn.close()

    flash('Complaint updated successfully.', 'success')
    return redirect(url_for('admin.dashboard'))
