from app import create_app

# Create an instance of the Flask application using the factory function.
app = create_app()

if __name__ == '__main__':
    # This block runs only when you execute `python run.py` directly.
    # It starts the development web server.
    app.run(host='0.0.0.0', port=5001)