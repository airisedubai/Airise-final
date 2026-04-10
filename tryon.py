import os
import time
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)

@app.route("/")
def home():
    """Serve the main HTML page"""
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route("/tryon", methods=["POST"])
def tryon():
    """AI Virtual Try-On endpoint"""
    token = os.environ.get("REPLICATE_TOKEN", "")
    if not token:
        return jsonify({"error": "Token missing"}), 500
    
    body = request.get_json()
    if not body:
        return jsonify({"error": "No data"}), 400
    
    h = {"Authorization": "Token " + token, "Content-Type": "application/json"}
    inp = {
        "version": "906425dbca90663ff5427624839572cc56ea7d380343d13e2a4c4b09d3f0c30f",
        "input": {
            "human_img": body.get("person"),
            "garm_img": body.get("garment"),
            "garment_des": body.get("desc", "clothing"),
            "is_checked": True,
            "is_checked_crop": False,
            "denoise_steps": 30,
            "seed": 42
        }
    }
    
    r = requests.post("https://api.replicate.com/v1/predictions", headers=h, json=inp, timeout=30)
    if not r.ok:
        return jsonify({"error": r.text}), 500
    
    pid = r.json().get("id")
    if not pid:
        return jsonify({"error": "No prediction ID"}), 500
    
    for _ in range(100):
        time.sleep(3)
        p = requests.get("https://api.replicate.com/v1/predictions/" + pid, headers=h, timeout=10).json()
        s = p.get("status")
        if s == "succeeded":
            out = p.get("output")
            return jsonify({"result": out[0] if isinstance(out, list) else out})
        if s in ["failed", "canceled"]:
            return jsonify({"error": p.get("error", "Failed")}), 500
    
    return jsonify({"error": "Timeout"}), 504

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)