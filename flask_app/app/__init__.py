# /flask_app/app/__init__.py
from flask import Flask, current_app, url_for
from flask_session import Session # Import Flask-Session
from config import Config
import os
import datetime
import base64 as b64_std
import markdown
from jinja2 import pass_eval_context
from markupsafe import Markup

# Initialize Flask-Session extension object (but don't associate with app yet)
sess = Session()

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configurations: first from config_class, then update/override from instance if exists
    app.config.from_object(config_class)
    # Example for instance config (optional, if you have an instance/config.py)
    # app.config.from_pyfile('config.py', silent=True) 

    # Ensure instance folder exists (config.py also does this, but belt-and-suspenders)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    

    # Ensure SESSION_FILE_DIR exists if using filesystem (config.py handles this too)
    if app.config.get("SESSION_TYPE") == "filesystem":
        session_file_dir = app.config.get("SESSION_FILE_DIR", os.path.join(app.instance_path, 'flask_session'))
        os.makedirs(session_file_dir, exist_ok=True)
        app.config["SESSION_FILE_DIR"] = session_file_dir # Ensure it's set on app.config

    # Initialize Flask-Session with the app
    sess.init_app(app)

    # === Markdown Filter Definition and Registration ===
    @pass_eval_context
    def markdown_filter(eval_ctx, value):
        if not value:
            return ""
        html_content = markdown.markdown(str(value) if value is not None else "", extensions=['fenced_code', 'tables'])
        if eval_ctx.autoescape:
            return Markup(html_content)
        return html_content
    app.jinja_env.filters['markdown'] = markdown_filter

    # === URL-safe Base64 Encode Filter ===
    def urlsafe_b64encode_filter(s):
        if s is None: return ''
        if isinstance(s, str): s_bytes = s.encode('utf-8')
        elif isinstance(s, bytes): s_bytes = s
        else: s_bytes = str(s).encode('utf-8')
        return b64_std.urlsafe_b64encode(s_bytes).decode('utf-8')
    app.jinja_env.filters['urlsafe_b64encode'] = urlsafe_b64encode_filter

    # Register Blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_global_vars():
        video_filename_config = current_app.config.get("WELCOME_VIDEO_FILENAME", "")
        welcome_video_static_path = f'videos/{video_filename_config}' if video_filename_config else None
        video_full_path_on_server = ""
        if welcome_video_static_path and current_app.static_folder and video_filename_config:
            video_full_path_on_server = os.path.join(current_app.static_folder, 'videos', video_filename_config)
        return {
            'now': datetime.datetime.now(datetime.timezone.utc),
            'welcome_video_path': url_for('static', filename=welcome_video_static_path) if welcome_video_static_path else None,
            'video_exists': os.path.exists(video_full_path_on_server) if video_full_path_on_server else False
        }

    # Error Handlers
    from .main.errors import forbidden_error, page_not_found, internal_error 
    app.register_error_handler(403, forbidden_error)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_error)

    # Optional: Logging setup
    if not app.debug and not app.testing:
        # Add logging handlers (e.g., to a file)
        import logging
        from logging.handlers import RotatingFileHandler
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/lumar.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Lumar startup')
    elif app.debug: # Add this block for debug mode too
        app.logger.setLevel(logging.DEBUG)

    return app