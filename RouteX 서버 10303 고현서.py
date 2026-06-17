from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# 🔥 ODSay ON/OFF 스위치
# =========================
USE_ODSAY = True   # True = ODSay 사용 / False = 자체 알고리즘

# =========================
# 🔥 더미 함수 (나중에 여기만 교체하면 됨)
# =========================
import requests

ODSAY_KEY = "xkOfzY5Wfc0DJqF4KQc023zQxBwBQAkXpRmx3A/xzWY"

def use_odsay(start, end):

    url = "https://api.odsay.com/v1/api/searchPubTransPathT"

    params = {
        "apiKey": ODSAY_KEY,
        "SX": start_x,
        "SY": start_y,
        "EX": end_x,
        "EY": end_y,
        "SearchPathType": 0
    }

    response = requests.get(url, params=params)

    data = response.json()

    return {
        "mode": "ODsay",
        "result": data
    }

def use_local_model(start, end):

    distance = get_distance(start, end)

    # 0.5km 미만도 처리 (예외)
    if distance < 0.5:
        avg_speed = 45
        time = (distance / avg_speed) * 60
    else:
        time = estimate_time(distance)

    return {
        "mode": "LOCAL",
        "distance_km": round(distance, 2),
        "total_time_min": round(time, 1)
    }
# =========================
# 🚀 메인 API
# =========================
@app.route("/route", methods=["POST"])
def route():

    data = request.json

    start = data.get("start")
    end = data.get("end")

    if not start or not end:
        return jsonify({
            "error": "start / end 필요"
        }), 400

    # =========================
    # 🔥 핵심 스위치
    # =========================
    if USE_ODSAY:
        result = use_odsay(start, end)
    else:
        result = use_local_model(start, end)

    return jsonify(result)


# =========================
# 🚀 서버 실행
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # 외부 접속 가능
        port=5000,
        debug=True
    )
