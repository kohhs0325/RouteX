from flask import Flask, request, jsonify
import requests
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)

# =========================
# 🔑 API KEY
# =========================
KAKAO_KEY = "6e365680936819c2e656e6cebede3ce8"
ODSAY_KEY = "xkOfzY5Wfc0DJqF4KQc023zQxBwBQAkXpRmx3A/xzWY"

# =========================
# 🔥 카카오 장소 → 좌표
# =========================
def search_place(place_name):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    headers = {
        "Authorization": f"KakaoAK {KAKAO_KEY}"
    }

    params = {"query": place_name}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=3)
        data = res.json()

        if not data.get("documents"):
            return None

        place = data["documents"][0]

        return {
            "name": place["place_name"],
            "x": float(place["x"]),
            "y": float(place["y"])
        }

    except:
        return None


# =========================
# 🔥 거리 계산 (km)
# =========================
def get_distance(loc1, loc2):
    R = 6371

    lat1 = radians(loc1["y"])
    lon1 = radians(loc1["x"])
    lat2 = radians(loc2["y"])
    lon2 = radians(loc2["x"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


# =========================
# 🔥 시간 추정 모델
# =========================
def estimate_time(distance):

    if distance < 0.5:
        speed = 45
    elif distance < 1.0:
        speed = 42
    elif distance < 1.5:
        speed = 38
    else:
        speed = 33

    return (distance / speed) * 60




# =========================
# 🔥 ODSay 모델
# =========================
def use_odsay(start, end, waypoints):

    print("===== ODsay 함수 진입 =====")
    print("start =", start)
    print("end =", end)
    
    start_loc = search_place(start)
    end_loc = search_place(end)

    print("start_loc =", start_loc)
    print("end_loc =", end_loc)

    if not start_loc or not end_loc:
        return None

    url = "https://api.odsay.com/v1/api/searchPubTransPathT"

    params = {
        "apiKey": ODSAY_KEY,
        "SX": start_loc["x"],
        "SY": start_loc["y"],
        "EX": end_loc["x"],
        "EY": end_loc["y"],
        "SearchPathType": 0
    }

    try:
        res = requests.get(url, params=params, timeout=3)
        
        print("ODsay 상태:", res.status_code)
        print("ODsay 응답:", res.text)

        data = res.json()

        if "error" in data or "result" not in data:
            return None

        path = data["result"]["path"][0]["subPath"]

        route = []

        for p in path:

            if p["trafficType"] == 1:

                start_station = p.get("startName", "")
                lane = p.get("lane", [])

                line_name = ""

                if lane:
                    line_name = lane[0].get("name", "")

                route.append(f"{start_station} ({line_name})")

        if path:
            route.append(path[-1].get("endName", "도착"))

        return {
            "mode": "ODsay",
            "route": route,
            "raw": data
        }

    except Exception as e:
        print("ODsay 오류:", e)
        return None

        
# =========================
# 🔥 LOCAL fallback 모델
# =========================
def use_local_model(start, end, waypoints):

    start_loc = search_place(start)
    end_loc = search_place(end)

    if not start_loc or not end_loc:
        return {
            "mode": "LOCAL",
            "error": "카카오 좌표 변환 실패"
        }

    distance = get_distance(start_loc, end_loc)
    time = estimate_time(distance)

    route = [
        f"{start_loc['name']} (출발)"
    ]

    for wp in waypoints:
        route.append(wp)

    route.append(
        f"{end_loc['name']} (도착)"
    )

    return {
        "mode": "LOCAL",
        "route": route,
        "distance_km": round(distance, 2),
        "total_time_min": round(time, 1)
    }

# =========================
# 🚀 메인 API (핵심)
# =========================
@app.route("/route", methods=["POST"])
def route():

    data = request.json
    
    start = data.get("start")
    end = data.get("end")
    waypoints = data.get("waypoints", [])

    print("출발:", start)
    print("방문지:", waypoints)
    print("도착:", end)

    if not start or not end:
        return jsonify({"error": "start / end 필요"}), 400


    # =========================
    # 1️⃣ ODSay 먼저 시도
    # =========================
    result = use_odsay(start, end, waypoints)

    if result:
        return jsonify(result)


    # =========================
    # 2️⃣ fallback (카카오 + LOCAL)
    # =========================
    result = use_local_model(start, end, waypoints)
    result["mode"] = "FALLBACK"

    return jsonify(result)


# =========================
# 🚀 실행
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
