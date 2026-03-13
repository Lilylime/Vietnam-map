import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import openrouteservice

# Thiết lập đường dẫn hệ thống
raw_path = os.path.abspath(__file__)
BASE_DIR = os.path.dirname(raw_path)

# Cấu hình thư mục
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
JSON_PATH = os.path.join(BASE_DIR, 'gadm41_VNM_0.json') 

app = Flask(__name__, template_folder=TEMPLATE_DIR)
CORS(app) 

# API Key OpenRouteService (Thay bằng Key của bạn nếu Key này hết hạn)
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJlZTc0N2M0Yjk2MTQ3YmZiNWNhZDg1MDQ2NzU1YjRjIiwiaCI6Im11cm11cjY0In0="
client = openrouteservice.Client(key=API_KEY)

@app.route("/")
def index():
    """Trả về giao diện bản đồ chính"""
    return render_template("map.html")

@app.route("/vietnam_map")
def vietnam_map():
    """Gửi dữ liệu ranh giới hành chính Việt Nam lên bản đồ"""
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": f"Lỗi đọc file JSON: {str(e)}"}), 500
    return jsonify({"error": "Không tìm thấy file ranh giới VN"}), 404

@app.route("/route", methods=["POST"])
def get_route():
    """Xử lý tính toán đường đi giữa 2 điểm"""
    try:
        data = request.get_json()
        # Leaflet gửi [lat, lng], ORS nhận [lng, lat]
        start_coords = (data['start'][1], data['start'][0])
        end_coords = (data['end'][1], data['end'][0])

        # Gọi API lấy chỉ đường (Profile ô tô)
        # Chỉ tập trung trong vùng VN thông qua tọa độ gửi lên
        routes = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson',
            language='vi' # Chỉ dẫn bằng tiếng Việt
        )

        # Trích xuất dữ liệu hình học (đường vẽ)
        geometry = routes['features'][0]['geometry']['coordinates']
        # Đảo ngược lại thành [lat, lng] cho Leaflet
        leaflet_route = [[c[1], c[0]] for c in geometry]
        
        # Lấy thông tin tóm tắt
        summary = routes['features'][0]['properties']['summary']
        distance_km = round(summary['distance'] / 1000, 2)
        duration_min = round(summary['duration'] / 60)

        return jsonify({
            "status": "success",
            "route": leaflet_route,
            "distance": distance_km,
            "duration": duration_min
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "status": "error",
            "message": "Không thể tìm thấy đường đi trong lãnh thổ Việt Nam"
        }), 500

if __name__ == "__main__":
    # Chạy server tại cổng 5000
    app.run(debug=True, port=5000)