#!/usr/bin/env python3
"""Simple Kindle Paperwhite dashboard: time, date (DD/MM) and weather for Northwich.

Writes a 1072x1448 8-bit grayscale PNG. Weather is from Open-Meteo (free, no key).
  python dashboard.py          # live weather
  python dashboard.py --demo   # fake weather, for testing the layout
"""
import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

W, H = 1072, 1448
TZ = ZoneInfo("Europe/London")
LAT, LON, PLACE = 53.2594, -2.5181, "Northwich"
OUT = os.environ.get("OUT_FILE", "dashboard.png")
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_DIR + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)
    except OSError:
        return ImageFont.load_default()


WMO = {0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
       51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain",
       65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain", 71: "Light snow", 73: "Snow",
       75: "Heavy snow", 77: "Snow grains", 80: "Showers", 81: "Showers", 82: "Heavy showers",
       85: "Snow showers", 86: "Snow showers", 95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"}


def get_weather(demo=False):
    if demo:
        return {"temp": 7, "feels": 4, "code": 61, "wind": 14, "hi": 9, "lo": 3, "pop": 70,
                "days": [("Sun", 8, 3, 61, 70), ("Mon", 10, 5, 3, 20), ("Tue", 9, 4, 2, 10)]}
    import requests
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": LAT, "longitude": LON, "timezone": "Europe/London", "wind_speed_unit": "mph",
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 4}, timeout=30)
    r.raise_for_status()
    j = r.json()
    c, d = j["current"], j["daily"]
    days = [(dt.date.fromisoformat(d["time"][i]).strftime("%a"), round(d["temperature_2m_max"][i]),
             round(d["temperature_2m_min"][i]), d["weather_code"][i],
             d["precipitation_probability_max"][i] or 0) for i in range(1, 4)]
    return {"temp": round(c["temperature_2m"]), "feels": round(c["apparent_temperature"]),
            "code": c["weather_code"], "wind": round(c["wind_speed_10m"]),
            "hi": round(d["temperature_2m_max"][0]), "lo": round(d["temperature_2m_min"][0]),
            "pop": d["precipitation_probability_max"][0] or 0, "days": days}


def render(now, w):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    pad = 60
    # time + date
    d.text((pad, 50), now.strftime("%H:%M"), font=font(260, True), fill=0)
    d.text((pad, 360), now.strftime("%d/%m"), font=font(150, True), fill=0)
    d.text((pad + 470, 400), now.strftime("%A"), font=font(70), fill=0)
    d.text((W - pad, 40), f"updated {now.strftime('%H:%M')}", font=font(26), fill=110, anchor="ra")
    d.line((pad, 590, W - pad, 590), fill=0, width=5)
    # weather now
    d.text((pad, 620), f"{w['temp']}°", font=font(190, True), fill=0)
    d.text((pad + 400, 640), WMO.get(w["code"], "—"), font=font(60, True), fill=0)
    d.text((pad + 400, 720), f"Feels like {w['feels']}°", font=font(40), fill=0)
    d.text((pad + 400, 780), f"High {w['hi']}°  Low {w['lo']}°", font=font(40), fill=0)
    d.text((pad + 400, 840), f"Rain {w['pop']}%   Wind {w['wind']} mph", font=font(40), fill=0)
    d.text((W - pad, 610), PLACE, font=font(30), fill=110, anchor="ra")
    d.line((pad, 960, W - pad, 960), fill=0, width=5)
    # next 3 days
    colw = (W - 2 * pad) // 3
    for i, (day, hi, lo, code, pop) in enumerate(w["days"]):
        cx = pad + i * colw + colw // 2
        d.text((cx, 1000), day, font=font(46, True), fill=0, anchor="ma")
        d.text((cx, 1070), f"{hi}° / {lo}°", font=font(44), fill=0, anchor="ma")
        d.text((cx, 1135), WMO.get(code, ""), font=font(34), fill=60, anchor="ma")
        d.text((cx, 1185), f"Rain {pop}%", font=font(34), fill=60, anchor="ma")
    return img


def main():
    now = dt.datetime.now(TZ)
    img = render(now, get_weather("--demo" in sys.argv))
    img.save(OUT, "PNG", optimize=True)
    print("wrote", OUT, img.size, img.mode)


if __name__ == "__main__":
    main()
