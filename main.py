from __future__ import annotations

import time
from datetime import date, datetime
import datetime
import requests
from pathlib import Path
import psutil
from dotenv import load_dotenv

# import psycopg2
import psycopg
from flask import Flask, abort, render_template, redirect, url_for, flash, request, jsonify, Response
from functools import wraps
from flask import abort
import smtplib
import os
from email.message import EmailMessage
import csv
import sys, shutil, os.path
from flask import send_file

from utilities import db_create
from utilities import generic_utilities as gu
from utilities.db_common_functions import DB_Common
from utilities.db_connect import DB_Connect
from utilities.fx_rate_api_utility import FXRateAPIUtility
from flask_caching import Cache

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

file_path = Path(__file__).parent.parent / "test.env"
load_dotenv(file_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config["CACHE_TYPE"] = "SimpleCache"  # in-memory cache
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # 5 minutes
cache = Cache(app)

db_create.create_db()
db_create.create_table()


def to_dict(self):
    # Method 1.
    dictionary = {}
    # Loop through each column in the data record
    for column in self.__table__.columns:
        # Create a new dictionary entry;
        # where the key is the name of the column
        # and the value is the value of the column
        dictionary[column.name] = getattr(self, column.name)
        print(dictionary)
        return dictionary


@cache.cached()
def get_rates_api():
    ccy_pairs = DB_Common().retrieve_ccy_pairs()
    currencies_for_api = [ccy_pair[1] for ccy_pair in ccy_pairs]
    print(currencies_for_api)
    fx_rate_api = FXRateAPIUtility()
    ccy_pair_info = fx_rate_api.get_from_api(currencies_for_api)
    return ccy_pair_info


def generate_rates():
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45
    ccy_pairs = DB_Common().retrieve_ccy_pairs()
    currencies_for_db = [(ccy_pair[1], ccy_pair[2], ccy_pair[4]) for ccy_pair in ccy_pairs]
    print(currencies_for_db)
    ccy_pair_info = DB_Common().retrieve_rates(currencies_for_db)
    ccy_pair_info_updated = gu.generate_random_rates(ccy_pair_info)
    # DB_Common().delete_rates()
    for (k, v) in ccy_pair_info_updated.items():
        DB_Common().update_spot_rate(formatted_time, k, v[0])

    print(f'ccy_pair_info_updated: {ccy_pair_info_updated}')
    return ccy_pair_info_updated


@app.route('/api/fetch_rates', methods=['GET'])
def fetch_rates():
    rates = generate_rates()

    # Convert each tuple to a dictionary

    return jsonify({
        "message": "Rates returned successfully",
        "rates": rates
    })


@app.template_filter('format_million')
def format_million(value):
    return f"{value / 1_000_000:.2f}M"  # 5000000 -> 5.00M


@app.template_filter('format_number')
def format_number(value):
    return "{:,.2f}".format(float(value.replace(',', '')))  # 5000000 -> 5,000,000


@app.route('/')
def home():
    ccy_pair_info = generate_rates()
    print(ccy_pair_info)

    trades = DB_Common().retrieve_trades()

    return render_template("index.html", ccy_pair_info=ccy_pair_info, trades=trades)


@app.route("/execute_trade/", methods=["GET", "POST"])
def execute_trade():
    if request.method == "POST":
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45'
        trade_details = []
        trade_status = 'EXECUTED'
        timestamp = formatted_time
        ccy_pair = request.form["pair"]
        direction = request.form["direction"]
        base_amount = request.form["base_amount"]
        base_ccy = ccy_pair[0:3]
        counter_ccy_amount = request.form["counter_amount"]
        counter_ccy = ccy_pair[3:]
        # dealt rate
        dealt_rate = request.form["rate"]
        # spot rate
        spot_rate = request.form["spot_rate"]
        markup = request.form["pip-markup"]
        source = 'GUI'
        print(markup)

        if str(markup) == '0':
            profit = '0.00'
        else:
            markup = float(markup) / 10000

            if direction == 'Buy':
                print('reached here')
                profit = round((float(base_amount.replace(',', '')) * float(dealt_rate) -
                                float(base_amount.replace(',', '')) * float(spot_rate)), 2)

            else:
                profit = round((float(base_amount.replace(',', '')) * float(spot_rate) -
                                float(base_amount.replace(',', '')) * float(dealt_rate)), 2)

        trade_details.extend([trade_status, timestamp, ccy_pair, direction, base_ccy, base_amount,
                              counter_ccy, str(counter_ccy_amount), spot_rate, dealt_rate, str(markup), str(profit), source])

        print(trade_details)

        # response = DB_Common().check_position(ccy_pair, base_amount, direction)

        # if response['status'] == 'ok':
        DB_Common().execute_trade(trade_details)
        update_position = DB_Common().update_position(ccy_pair, base_amount, direction)

        return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), port=5002)
