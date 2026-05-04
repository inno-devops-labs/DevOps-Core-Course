#!/usr/bin/env python3
from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "hostname": socket.gethostname()})

@app.route('/')
def root():
    return jsonify({
        "app": "DevOps Info Service",
        "built_with": "Nix",
        "reproducible": True,
        "version": "1.0.0"
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
