import os
import requests
import math
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Lấy Key từ Environment Variable của Render để bảo mật
GRAPHOPPER_KEY = os.environ.get("GRAPHOPPER_KEY", "c75fe5a2-2fd0-4732-ad83-d2d964782987")

# Các điểm nằm trên quốc lộ VN (Giữ nguyên danh sách của bạn)
HIGHWAY_POINTS = [
    (21.0278,105.8342), (20.8449,106.6881), (19.8067,105.7851),
    (18.6796,105.6813), (17.4833,106.6000), (16.0544,108.2022),
    (15.5736,108.4740), (13.7820,109.2190), (12.2388,109.1967),
    (11.5681,109.0227), (10.8231,106.6297), (10.0452,105.7469),
]

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def find_near_highway(start, end):
    best = None
    best_score = 999999
    for p in HIGHWAY_POINTS:
        score = dist(start, p) + dist(p, end)
        if score < best_score:
            best_score = score
            best = p
    return best

def get_route(points):
    url = "https://graphhopper.com/api/1/route"
    params = [("point", f"{p[0]},{p[1]}") for p in points]
    params += [
        ("profile", "car"),
        ("weighting", "fastest"),
        ("snap_preventions", "residential,service,track,path,footway,cycleway,living_street"),
        ("points_encoded", "false"),
        ("key", GRAPHOPPER_KEY)
    ]
    try:
        r = requests.get(url, params=params).json()
        if "paths" not in r:
            return None
        path = r["paths"][0]
        return {
            "distance": path["distance"] / 1000,
            "coords": [[c[1], c[0]] for c in path["points"]["coordinates"]]
        }
    except Exception:
        return None

@app.route("/")
def home():
    return render_template("map.html")

@app.route("/route", methods=["POST"])
def route():
    data = request.json
    start = data.get("start")
    end = data.get("end")

    if not start or not end:
        return jsonify({"status": "error", "message": "Missing coordinates"})

    normal = get_route([start, end])
    if not normal:
        return jsonify({"status": "error", "message": "Could not find normal route"})

    highway = find_near_highway(start, end)
    best = normal

    if highway:
        highway_route = get_route([start, highway, end])
        if highway_route:
            # Ưu tiên lộ trình quốc lộ nếu không dài hơn quá 20%
            if highway_route["distance"] <= normal["distance"] * 1.2:
                best = highway_route

    return jsonify({
        "status": "success",
        "distance": round(best["distance"], 2),
        "route": best["coords"]
    })

if __name__ == "__main__":
    # Render yêu cầu chạy trên host 0.0.0.0
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
