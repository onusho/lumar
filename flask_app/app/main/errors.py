# /flask_app/app/main/errors.py
from flask import render_template, current_app

# These functions are registered to the app object in app/__init__.py
# So they don't need to use @bp.app_errorhandler here.

def forbidden_error(error):
    current_app.logger.warning(f"Forbidden (403) error: {error}")
    return render_template('errors/403.html'), 403

def page_not_found(error):
    current_app.logger.info(f"Page not found (404) error: {error}")
    return render_template('errors/404.html'), 404

def internal_error(error):
    # Log the actual exception for server-side debugging
    current_app.logger.error(f"Internal server (500) error: {error}", exc_info=True)
    return render_template('errors/500.html'), 500