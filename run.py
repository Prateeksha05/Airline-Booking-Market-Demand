import requests
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

AVIATIONSTACK_API_KEY = "c50689b0b8e9c07a8dfece34c3ee0e46"

def fetch_flights_data():
    url = f"http://api.aviationstack.com/v1/flights?access_key={AVIATIONSTACK_API_KEY}&limit=100"
    response = requests.get(url)
    data = response.json()

    if "error" in data:
        print("API ERROR:", data["error"])
        return pd.DataFrame()

    flights = []
    for item in data.get("data", []):
        airline = item.get("airline", {}).get("name", "")
        flight_number = item.get("flight", {}).get("number", "")
        departure = item.get("departure", {}).get("airport", "")
        departure_country = item.get("departure", {}).get("country", "")
        departure_time = item.get("departure", {}).get("scheduled", "")
        arrival = item.get("arrival", {}).get("airport", "")
        arrival_country = item.get("arrival", {}).get("country", "")
        arrival_time = item.get("arrival", {}).get("scheduled", "")
        flight_status = item.get("flight_status", "")

        if airline and departure and arrival:
            flights.append({
                "airline": airline,
                "flight_number": flight_number,
                "flight_status": flight_status,
                "departure": departure,
                "departure_country": departure_country,
                "departure_time": departure_time,
                "arrival": arrival,
                "arrival_country": arrival_country,
                "arrival_time": arrival_time
            })

    df = pd.DataFrame(flights)
    print("DEBUG DataFrame rows:", len(df))
    return df

def get_top_routes(df):
    if df.empty:
        return [], []
    df["route"] = df["departure"] + " → " + df["arrival"]
    counts = df["route"].value_counts().reset_index()
    counts.columns = ["route", "count"]
    top_routes = counts.head(10)
    return top_routes["route"].tolist(), top_routes["count"].tolist()

def get_top_airlines(df):
    if df.empty or "airline" not in df.columns:
        return [], []
    counts = df["airline"].value_counts().head(10)
    return counts.index.tolist(), counts.values.tolist()

def get_top_airports(df):
    if df.empty or "departure" not in df.columns:
        return [], []
    all_airports = pd.concat([df["departure"], df["arrival"]])
    counts = all_airports.value_counts().head(10)
    return counts.index.tolist(), counts.values.tolist()

def get_status_distribution(df):
    if df.empty or "flight_status" not in df.columns:
        return [], []
    counts = df["flight_status"].value_counts()
    return counts.index.tolist(), counts.values.tolist()

@app.route("/", methods=["GET"])
def index():
    df = fetch_flights_data()

    # Handle filters
    airline_filter = request.args.get("airline", "")
    from_airport = request.args.get("from_airport", "")
    to_airport = request.args.get("to_airport", "")

    if not df.empty:
        if airline_filter:
            df = df[df["airline"].str.contains(airline_filter, case=False, na=False)]

        if from_airport:
            df = df[df["departure"].str.contains(from_airport, case=False, na=False)]

        if to_airport:
            df = df[df["arrival"].str.contains(to_airport, case=False, na=False)]

    # Prepare charts
    routes_labels, routes_data = get_top_routes(df)
    airlines_labels, airlines_data = get_top_airlines(df)
    airports_labels, airports_data = get_top_airports(df)
    status_labels, status_data = get_status_distribution(df)

    # Prepare flight details table
    if df.empty:
        flights_table = []
    else:
        flights_table = df[[
            "airline",
            "flight_number",
            "flight_status",
            "departure",
            "departure_time",
            "arrival",
            "arrival_time"
        ]].fillna("").to_dict(orient="records")

    return render_template(
        "ui.html",
        routes_labels=routes_labels,
        routes_data=routes_data,
        airlines_labels=airlines_labels,
        airlines_data=airlines_data,
        airports_labels=airports_labels,
        airports_data=airports_data,
        status_labels=status_labels,
        status_data=status_data,
        flights_table=flights_table,
        airline_filter=airline_filter,
        from_airport=from_airport,
        to_airport=to_airport
    )

if __name__ == "__main__":
    app.run(debug=True)
