from flask import Flask, send_from_directory
import os

from models.db import init_db
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    app.config['DATABASE'] = os.environ.get('DATABASE_PATH', 'khadia_seva.db')
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    init_db(app.config['DATABASE'])

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app
