# /flask_app/app/auth/__init__.py
from flask import Blueprint

bp = Blueprint('auth', __name__)

from . import routes # Import routes AFTER bp is defined