# Import Flask class from the flask package
from flask import Flask

# Create an instance of the Flask app
app = Flask(__name__)

# Define the route for the root URL '/'
@app.route('/')
def home():
    # Return a simple HTML response
    return '<h1>Hello from Flask!</h1>'

# Only run the app if this file is executed directly (not imported)
if __name__ == '__main__':
    # Start the app, host 0.0.0.0 makes it accessible outside the container
    app.run(host='0.0.0.0', port=5000)