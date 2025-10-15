from flask import Flask

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    
    app.config.from_pyfile('../config.py')

    with app.app_context():
        # Import and register the routes
        from . import routes

    return app