# app.py
from flask import Flask, request, jsonify, redirect
import subprocess, pathlib, sys

app = Flask(__name__, static_folder='.')

@app.route('/')
def root():
    return app.send_static_file('login.html')

@app.route('/home')
def home():
    return app.send_static_file('home.html')

@app.route('/favorites')
def fav():
    return app.send_static_file('favorites.html')

@app.route('/catalog')
def catalog():
    return app.send_static_file('movie_catalog.html')

@app.route('/run-script', methods=['POST'])
def run_script():
    result = subprocess.run([sys.executable, 'old_script.py'],
                            capture_output=True, text=True)
    return jsonify(stdout=result.stdout,
                   stderr=result.stderr,
                   returncode=result.returncode)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
