"""
Минимальный тестовый сервер
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "OK"

@app.route('/test')
def test():
    return {"status": "working"}

if __name__ == '__main__':
    print("Starting test server on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=False)
