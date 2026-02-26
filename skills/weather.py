from model.llm_wrapper import say
from datetime import datetime
from pathlib import Path
import json
import requests

def instruction():
    return '"city": string (empty if not provided), "state": string (empty if not provided), "country_code": string (empty if not provided). NEVER use placeholders like "current location", "current state", "current country". Use empty string instead.'
def shape():
    return '"weather","args":{"city":"", "state":"", "country_code":""}'

WEATHER_CODES = {
    0:  "Clear sky",
    1:  "Mainly clear",
    2:  "Partly cloudy",
    3:  "Overcast",

    45: "Fog",
    48: "Rime fog",

    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",

    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",

    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",

    66: "Light freezing rain",
    67: "Heavy freezing rain",

    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",

    77: "Snow grains",

    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",

    85: "Slight snow showers",
    86: "Heavy snow showers",

    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}


def parseTime(req):
    time = []
    temperature_2m = []
    precipitation = []
    weathercode = []

    temperature_2m_max = req.get("daily", {}).get("temperature_2m_max", [])
    temperature_2m_min = req.get("daily", {}).get("temperature_2m_min", [])
    precipitation_sum = req.get("daily", {}).get("precipitation_sum", [])
    weathercode_daily = req.get("daily", {}).get("weathercode", [])
    hours = ""
    week = ""

    for i in range(24):
        time.append(req.get("hourly", {}).get("time", [])[i])
        temperature_2m.append(req.get("hourly", {}).get("temperature_2m", [])[i])
        precipitation.append(req.get("hourly", {}).get("precipitation", [])[i])
        weathercode.append(req.get("hourly", {}).get("weathercode", [])[i])
        hours += f'{{"t":"{time[i][-5:]}", "temp":{temperature_2m[i]}, "precip":{precipitation[i]}, "weather":"{str(weathercode[i]).replace(str(weathercode[i]), WEATHER_CODES[weathercode[i]])}"}},\n'

    date = []
    weathercode_week = []
    max_week = []
    min_week = []
    precip_sum_week = []

    for i in range(7):
        date.append(req.get("daily", {}).get("time", [])[i])
        weathercode_week.append(req.get("daily", {}).get("weathercode", [])[i])
        max_week.append(req.get("daily", {}).get("temperature_2m_max", [])[i])
        min_week.append(req.get("daily", {}).get("temperature_2m_min", [])[i])
        precip_sum_week.append(req.get("daily", {}).get("precipitation_sum", [])[i]) 
        weekday = datetime.strptime(date[i], "%Y-%m-%d")
        week += f'{{"d":"{date[i]} {weekday.strftime("%A")}", "temp_max":{max_week[i]}, "temp_min":{min_week[i]}, "precip":{precip_sum_week[i]}, "weather":"{WEATHER_CODES[weathercode_week[i]]}"}},\n'

    today = datetime.strptime(date[0], "%Y-%m-%d")

    return f"""
{{
    "daily": {{
        "todays_date": {date[0]} {today.strftime("%A")},
        "high": {temperature_2m_max[0]},
        "low": {temperature_2m_min[0]},
        "precipitation_sum": {precipitation_sum[0]},
        "weather": "{WEATHER_CODES[weathercode_daily[0]]}"
    }},
    "hourly": [
    {hours}
    ],
    "weekly": [
    {week}
    ]
}}
"""

def getWeather(text, city, state=None, country=None):
    lat, lon = getCoords(city, state, country)
    print(lat, lon)
    web = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&timezone=auto&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&current=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,rain,showers,snowfall,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,pressure_msl,visibility&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,cloud_cover,visibility,wind_speed_10m,wind_direction_10m,wind_gusts_10m,pressure_msl,weathercode&daily=weathercode,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,sunrise,sunset&forecast_days=7"
    req = requests.get(web).json()
    print(req)
    print(parseTime(req))
    prompt = f"""
    User message:
    {text}

    Weather data:
    {parseTime(req)}

    Rules:
    - Assume the data is in Fahrenheit.
    - Answer ONLY what the user asked. No extra summary.
    - Use ONLY the JSON above.
    - If the user mentions "week" or "this week" or "7 days", use weekly[] ONLY.
    - If the user asks about a specific time (e.g., 12 / 12:00 / noon), use hourly[] ONLY and match hourly[].t == "12:00".
    - Otherwise, use daily.
    - Do NOT use words like currently/right now/expected/tonight/tomorrow.
    - Treat it as snow if the selected entry's "weather" text contains "snow" (case-insensitive).
    - If the question is "how much will it snow today", use daily.precipitation_sum ONLY IF daily.weather contains "snow".

    Write your answer in ONE sentence:
    """

    return say(prompt, env="groq", type="chat")

def getCoords(city, state, country_code):
    if city == "":
        webip = 'http://ip-api.com/json/'
        req = requests.get(webip).json()
        return req.get("lat"), req.get("lon")

    location = f"{city} {state} {country_code}"
    web = f"https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "weather-assistant/1.0 (personal demo project)"
    }
    params = {
        "q": location,
        "format": "json",
        "limit": 1
    }

    req = requests.get(web, params=params, headers=headers)
    print(req.status_code)
    print(req.headers.get("content-type"))
    print(req.text[:200])
    data = req.json()
    lat, lon = data[0]["lat"], data[0]["lon"]
    return lat, lon

def main(args, text):
    if not isinstance(args, dict) or args == "":
        return "I didn't understand your request."
    try:
        city = args["city"]
        state = args["state"]
        country = args["country_code"]
        
        return getWeather(text, city, state, country)
    except Exception as e:
        return ("Something isn't quite right with your request", e)

if __name__ == "__main__":
    main()
