"""Entrée Windows / Linux / hébergement : python server.py."""
import os
from flask import Flask, jsonify, send_from_directory
from waitress import serve
from services import ROOT, CONFIG, weather, transport

app = Flask(__name__, static_folder=None)

@app.get('/')
def index():
    return send_from_directory(ROOT / 'static', 'index.html')

@app.get('/app.js')
def javascript():
    return send_from_directory(ROOT / 'static', 'app.js')

@app.get('/style.css')
def stylesheet():
    return send_from_directory(ROOT / 'static', 'style.css')

@app.get('/api/weather')
def weather_api():
    return jsonify(city=CONFIG['weather']['city'], **weather())

@app.get('/api/transport')
def transport_api():
    return jsonify(transport())

@app.get('/healthz')
def health():
    return jsonify(status='ok')

@app.after_request
def headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'self'"
    return response

if __name__ == '__main__':
    # Un seul processus, plusieurs threads : cache commun à tous les visiteurs.
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    print(f'Tableau du salon prêt sur le port {port}', flush=True)
    serve(app, host=host, port=port, threads=8)
