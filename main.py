from __future__ import annotations
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
from utilities.db_common_functions import DB_Common
from utilities.db_connect import DB_Connect
from utilities.fx_rate_api_utility import FXRateAPIUtility

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


@app.route('/')
def home():
    ccy_pairs = DB_Common().retrieve_ccy_pairs()
    currencies_for_api = [ccy_pair[1] for ccy_pair in ccy_pairs]
    print(currencies_for_api)
    fx_rate_api = FXRateAPIUtility()
    ccy_pair_info = fx_rate_api.get(currencies_for_api)
    print(ccy_pair_info)
    for (k, v) in ccy_pair_info.items():
        print(k, v)

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
        rate = request.form["rate"]

        trade_details.extend([trade_status, timestamp, ccy_pair, direction, base_ccy, base_amount,
                              counter_ccy, counter_ccy_amount, rate])

        print(trade_details)

        DB_Common().execute_trade(trade_details)

        return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), port=5002)
