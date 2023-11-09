from flask import Flask, render_template, request
import requests
from datetime import date, timedelta
from dateutil.parser import parse
import pandas as pd

app = Flask(__name__, template_folder='templates')

def is_valid_date(selected_date):
    today = date.today()
    max_date = today + timedelta(days=1)
    min_date = date(2022, 11, 1)
    return min_date <= selected_date <= max_date

def get_prices(selected_date, price_class):
    try:
        url = f"https://www.elprisetjustnu.se/api/v1/prices/{selected_date.year}/{selected_date.strftime('%m-%d')}_{price_class}.json"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            error_message = f"API Request Failed (Status Code {response.status_code})"
            return {"error": error_message}

    except Exception as e:
        return {"error": f"Error: {str(e)}"}

price_classes = {
    "SE1": "Luleå / Norra Sverige",
    "SE2": "Sundsvall / Norra Mellansverige",
    "SE3": "Stockholm / Södra Mellansverige",
    "SE4": "Malmö / Södra Sverige"
}

def format_time(prices):
    if "hour" in prices and "minute" in prices:
        return f"{prices['hour']:02d}:{prices['minute']:02d}"
    return "N/A"
@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None
    selected_date = None
    max_date_str = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')

    if request.method == "POST":
        price_class = request.form["price_class"]
        selected_date_str = request.form["selected_date"]
        selected_date = parse(selected_date_str).date()

        if not is_valid_date(selected_date):
            error_message = "Ogiltigt datum. Ange ett giltigt datum inom gränserna."
        elif price_class not in price_classes:
            error_message = "Ogiltig prisklass."
        else:
            prices = get_prices(selected_date, price_class)
            if "error" not in prices:
                price_data = []

                for price in prices:
                    timestamp = price["time_start"].split("T")[1][:5]
                    price_data.append({
                        "SEK per KWh": price["SEK_per_kWh"],
                        "EUR per KWh": price["EUR_per_kWh"],
                        "timestamp": timestamp,
                        "PRISKLASS": price_classes[price_class]
                    })

                # Create a Pandas DataFrame with the price data
                df = pd.DataFrame(price_data)

                return render_template("result.html", prices_df=df.to_html(classes='table table-striped table-hover mt-4', index=False, escape=False, render_links=True), max_date_str=max_date_str)
            else:
                error_message = prices["error"]

    return render_template("index.html", error_message=error_message, price_classes=price_classes, selected_date=selected_date, max_date_str=max_date_str)

# Add your existing code for the error handler

@app.errorhandler(404)
def page_not_found(e):
    return "Sidan kunde inte hittas.", 404

if __name__ == "__main__":
    app.run(debug=True)
