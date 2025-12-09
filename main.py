from __future__ import annotations
from flask_socketio import SocketIO, emit

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
socketio = SocketIO(app, cors_allowed_origins="*")


def notify_new_trade(trade_details):
    socketio.emit('new_trade', trade_details)


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


def check_live_orders(rates):

    for k, v in rates.items():
        ccy_pair = k

        orders = DB_Common().get_orders_by_ccy_pair(ccy_pair)

        if len(orders) > 0:
            for order in orders:
                order_id = order[0]
                direction = order[5]
                outstanding_balance = order[12]
                order_level = order[10]
                current_rate = v[0]
                print(f'GBPUSD: {order_level} / {current_rate}')
                if direction == 'Buy':
                    if float(current_rate) < float(order_level):
                        position = DB_Common().check_position(ccy_pair, outstanding_balance, direction)
                        print(f'position: {position}')
                        if position['status'] == 'ok':
                            trade_details = []
                            DB_Common().fill_order(order_id)
                            clip_amount = outstanding_balance
                            order_status = 'FILLED'
                            outstanding_balance = '0.00'
                            # generate spot trade
                            trade_status = 'EXECUTED'
                            now = datetime.datetime.now()
                            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45
                            timestamp = formatted_time
                            base_ccy = ccy_pair[0:3]
                            base_amount = str(clip_amount)
                            counter_ccy = ccy_pair[3:]
                            rate = current_rate
                            dealt_rate = rate
                            counter_ccy_amount = float(base_amount.replace(',', '')) * float(dealt_rate)
                            markup = '0'
                            profit = '0.00'
                            source = 'Powerfill'

                            trade_details.extend(
                                [trade_status, timestamp, ccy_pair, direction,
                                 base_ccy, "{:,.2f}".format(float(base_amount)),
                                 counter_ccy, "{:,.2f}".format(float(counter_ccy_amount)),
                                 str(rate), str(dealt_rate),
                                 str(markup), str(profit),
                                 source, order_id])

                            orderDetails = []
                            orderDetails.extend([order_id, order_status, outstanding_balance])
                            trade = DB_Common().execute_trade(trade_details)
                            update_position = DB_Common().update_position(ccy_pair, base_amount, direction)
                            current_position = float(update_position['current_position'])
                            max_position = float(update_position['max_limit'])
                            trade = list(trade)
                            trade.extend([current_position, max_position])
                            socketio.emit("order-update", list(orderDetails))
                            socketio.emit("new_trade_api", list(trade))
                        else:
                            trade_details = []
                            clip_amount = position['remaining_balance']
                            if float(clip_amount) > 0:
                                DB_Common().fill_order_clip(order_id, clip_amount, outstanding_balance)
                                order_status = 'FILLING'
                                outstanding_balance = str(float(outstanding_balance) - float(clip_amount))
                                # generate spot trade
                                trade_status = 'EXECUTED'
                                now = datetime.datetime.now()
                                formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45
                                timestamp = formatted_time
                                base_ccy = ccy_pair[0:3]
                                base_amount = str(clip_amount)
                                counter_ccy = ccy_pair[3:]
                                rate = current_rate
                                dealt_rate = rate
                                counter_ccy_amount = float(base_amount.replace(',', '')) * float(dealt_rate)
                                markup = '0'
                                profit = '0.00'
                                source = 'Powerfill'

                                trade_details.extend(
                                    [trade_status, timestamp, ccy_pair, direction,
                                     base_ccy, "{:,.2f}".format(float(base_amount)),
                                     counter_ccy, "{:,.2f}".format(float(counter_ccy_amount)),
                                     str(rate), str(dealt_rate),
                                     str(markup), str(profit),
                                     source, order_id])

                                orderDetails = []
                                orderDetails.extend([order_id, order_status, outstanding_balance])
                                trade = DB_Common().execute_trade(trade_details)
                                update_position = DB_Common().update_position(ccy_pair, base_amount, direction)
                                current_position = float(update_position['current_position'])
                                max_position = float(update_position['max_limit'])
                                trade = list(trade)
                                trade.extend([current_position, max_position])
                                socketio.emit("order-update", list(orderDetails))
                                socketio.emit("new_trade_api", list(trade))

                if direction == 'Sell':
                    if float(current_rate) > float(order_level):
                        trade_details = []
                        position = DB_Common().check_position(ccy_pair, outstanding_balance, direction)
                        if position['status'] == 'ok':
                            DB_Common().fill_order(order_id)
                            clip_amount = outstanding_balance
                            order_status = 'FILLED'
                            outstanding_balance = '0.00'
                            # generate spot trade
                            trade_status = 'EXECUTED'
                            now = datetime.datetime.now()
                            formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45
                            timestamp = formatted_time
                            base_ccy = ccy_pair[0:3]
                            base_amount = str(clip_amount)
                            counter_ccy = ccy_pair[3:]
                            rate = current_rate
                            dealt_rate = rate
                            counter_ccy_amount = float(base_amount.replace(',', '')) * float(dealt_rate)
                            markup = '0'
                            profit = '0.00'
                            source = 'Powerfill'

                            trade_details.extend(
                                [trade_status, timestamp, ccy_pair, direction,
                                 base_ccy, "{:,.2f}".format(float(base_amount)),
                                 counter_ccy, "{:,.2f}".format(float(counter_ccy_amount)), str(rate), str(dealt_rate),
                                 str(markup), str(profit),
                                 source, order_id])

                            orderDetails = []
                            orderDetails.extend([order_id, order_status, outstanding_balance])
                            trade = DB_Common().execute_trade(trade_details)
                            update_position = DB_Common().update_position(ccy_pair, base_amount, direction)
                            current_position = float(update_position['current_position'])
                            max_position = float(update_position['max_limit'])
                            trade = list(trade)
                            trade.extend([current_position, max_position])
                            socketio.emit("order-update", list(orderDetails))
                            socketio.emit("new_trade_api", list(trade))
                        else:
                            clip_amount = position['remaining_balance']
                            if float(clip_amount) > 0:
                                DB_Common().fill_order_clip(order_id, clip_amount, outstanding_balance)
                                order_status = 'FILLING'
                                outstanding_balance = str(float(outstanding_balance) - float(clip_amount))
                                # generate spot trade
                                trade_status = 'EXECUTED'
                                now = datetime.datetime.now()
                                formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45
                                timestamp = formatted_time
                                base_ccy = ccy_pair[0:3]
                                base_amount = str(clip_amount)
                                counter_ccy = ccy_pair[3:]
                                rate = current_rate
                                dealt_rate = rate
                                counter_ccy_amount = float(base_amount.replace(',', '')) * float(dealt_rate)
                                markup = '0'
                                profit = '0.00'
                                source = 'Powerfill'

                                trade_details.extend(
                                    [trade_status, timestamp, ccy_pair, direction,
                                     base_ccy, "{:,.2f}".format(float(base_amount)),
                                     counter_ccy, "{:,.2f}".format(float(counter_ccy_amount)),
                                     str(rate), str(dealt_rate),
                                     str(markup), str(profit),
                                     source, order_id])

                                orderDetails = []
                                orderDetails.extend([order_id, order_status, outstanding_balance])
                                trade = DB_Common().execute_trade(trade_details)
                                update_position = DB_Common().update_position(ccy_pair, base_amount, direction)
                                current_position = float(update_position['current_position'])
                                max_position = float(update_position['max_limit'])
                                trade = list(trade)
                                trade.extend([current_position, max_position])
                                socketio.emit("order-update", list(orderDetails))
                                socketio.emit("new_trade_api", list(trade))


@app.route('/api/fetch_rates', methods=['GET'])
def fetch_rates():
    rates = generate_rates()
    check_live_orders(rates)

    # Convert each tuple to a dictionary

    return jsonify({
        "message": "Rates returned successfully",
        "rates": rates
    })


@app.route('/api/submit_trade', methods=['POST'])
def submit_trade_api():
    try:
        print("Raw request data:", request.data)
        data = request.get_json(force=True)
        print("Parsed data:", data)

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        trade_details = []
        ccy_pair = data['ccy_pair']

        ccy_pairs = DB_Common().retrieve_ccy_pairs()
        valid_pair = False
        for pair in ccy_pairs:
            if ccy_pair in pair:
                valid_pair = True
                break

        if not valid_pair:
            return jsonify({"error": "Ccy pair is not valid."}), 400

        direction = data['direction']

        if direction not in ['Buy', 'Sell']:
            return jsonify({"error": "Direction should be 'Buy' or 'Sell'."}), 400

        base_amount = data['base_amt']

        try:
            base_amount = float(base_amount)
        except ValueError:
            return jsonify({"error": "Base amount should be numeric with no more than 2 decimals e.g. 1000000.00"}), 400

        if base_amount <= 0:
            return jsonify({"error": "Base amount should be greater than 0."}), 400

        position_breach = DB_Common().check_position(ccy_pair, str(base_amount), direction)
        print(f'position_breach: {position_breach}')

        if position_breach['status'] == 'error':
            return jsonify({"error": "Trade amount breaches max position limit."}), 400

        markup = data['markup']

        try:
            markup = int(markup)
        except ValueError:
            return jsonify({"error": "Markup should be q whole number e.g. 50."}), 400

        status = 'EXECUTED'
        base_ccy = data['base_ccy']
        if base_ccy != ccy_pair[0:3]:
            return jsonify({"error": f"Base ccy should be {ccy_pair[0:3]}."}), 400

        counter_ccy = data['counter_ccy']

        if counter_ccy != ccy_pair[3:6]:
            return jsonify({"error": f"Counter ccy should be {ccy_pair[3:6]}."}), 400

        source = 'API'
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45'
        timestamp = formatted_time
        spot_rate = DB_Common().get_spot_rate(ccy_pair)
        if int(markup) > 0:
            if direction == 'Buy':
                dealt_rate = "{:,.4f}".format(float(spot_rate) + (float(markup) / 10000))
                profit = round((float(base_amount) * float(dealt_rate) -
                                float(base_amount) * float(spot_rate)), 2)
                markup = float(markup) / 10000
            else:
                dealt_rate = "{:,.4f}".format(float(spot_rate) - (float(markup) / 10000))
                profit = round((float(base_amount) * float(spot_rate) -
                                float(base_amount) * float(dealt_rate)), 2)
                markup = float(markup) / 10000
        else:
            dealt_rate = spot_rate
            profit = "0.00"

        counter_ccy_amt = "{:,.2f}".format(float(dealt_rate) * float(base_amount))
        # profit = "{:,.2f}".format(float(profit))

        order_id = ''

        trade_details.extend([status, timestamp, ccy_pair, direction, base_ccy, "{:,.2f}".format(float(base_amount)),
                              counter_ccy, str(counter_ccy_amt), str(spot_rate), str(dealt_rate), str(markup),
                              str(profit),
                              source, order_id])

        new_trade = DB_Common().execute_trade(trade_details)
        update_position = DB_Common().update_position(ccy_pair, base_amount, direction)
        current_position = float(update_position['current_position'])
        max_position = float(update_position['max_limit'])
        print(f'Current: {current_position}, Max: {max_position}')
        new_trade = list(new_trade)
        new_trade.extend([current_position, max_position])
        print(f'new api trade: {list(new_trade)}')
        # 🔥 EMIT TO ALL CONNECTED FRONT-ENDS

        socketio.emit("new_trade_api", list(new_trade))

        return jsonify({"message": "Trade submitted successfully",
                        "trade": {
                            "trade_id": new_trade[0],
                            "trade_status": new_trade[1],
                            "timestamp": new_trade[2],
                            "ccy_pair": new_trade[3],
                            "direction": new_trade[4],
                            "base_ccy": new_trade[5],
                            "base_amt": new_trade[6],
                            "counter_ccy": new_trade[7],
                            "counter_ccy_amt": new_trade[8],
                            "spot_rate": new_trade[9],
                            "dealt_rate": new_trade[10],
                            "markup": new_trade[11],
                            "profit": new_trade[12],
                            "source": new_trade[13],
                            "order_id": new_trade[14]

                        }
                        }), 201

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500


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

    orders = DB_Common().retrieve_orders()

    return render_template("index.html", ccy_pair_info=ccy_pair_info, trades=trades,
                           orders=orders)

@app.route('/order-action', methods=['POST'])
def order_action():
    data = request.get_json()
    order_id = data.get("id")
    action = data.get("action")

    print("Received:", order_id, action)

    if action == 'cancel':
        order = DB_Common().cancel_order(order_id)
        orderDetails = []
        order_status = order[1]
        outstanding_balance = order[12]
        orderDetails.extend([order_id, order_status, outstanding_balance])
        socketio.emit("order-update", list(orderDetails))


@app.route("/execute_trade/", methods=["POST"])
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
        print(f'Spot Rate: {spot_rate}')
        markup = request.form["pip-markup"]
        source = 'GUI'
        order_id = ''
        print(markup)

        if str(markup) == '0':
            profit = '0.00'
            spot_rate = dealt_rate
        else:
            markup = float(markup) / 10000

            if direction == 'Buy':
                print('reached here')
                profit = round((float(base_amount.replace(',', '')) * float(dealt_rate) -
                                float(base_amount.replace(',', '')) * float(spot_rate)), 2)

            else:
                profit = round((float(base_amount.replace(',', '')) * float(spot_rate) -
                                float(base_amount.replace(',', '')) * float(dealt_rate)), 2)

        trade_details.extend([trade_status, timestamp, ccy_pair, direction, base_ccy, str(base_amount),
                              counter_ccy, str(counter_ccy_amount), str(spot_rate), str(dealt_rate), str(markup),
                              str(profit),
                              source, order_id])

        print(trade_details)

        # response = DB_Common().check_position(ccy_pair, base_amount, direction)

        # if response['status'] == 'ok':
        DB_Common().execute_trade_GUI(trade_details)
        update_position = DB_Common().update_position(ccy_pair, base_amount, direction)

        return redirect(url_for("home"))


@app.route("/execute_order/", methods=["POST"])
def execute_order():
    if request.method == "POST":
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # e.g., '2025-11-14 14:30:45'
        order_details = []
        order_status = 'LIVE'
        timestamp = formatted_time
        ccy_pair = request.form["oe-pair"]
        direction = request.form["oe-direction"]
        order_amount = request.form["oe-amount"]
        base_ccy = ccy_pair[0:3]
        counter_ccy = ccy_pair[3:]
        # rate
        rate = request.form["oe-rate"]
        source = 'GUI'
        level = request.form["oe-level"]
        order_type = 'Take Profit'
        reference = request.form["oe-reference"]
        outstanding_balance = order_amount

        order_details.extend([order_status, timestamp, order_type, ccy_pair, direction, base_ccy, order_amount,
                              counter_ccy, rate, level, source, outstanding_balance, reference])

        print(order_details)

        # response = DB_Common().check_position(ccy_pair, base_amount, direction)

        # if response['status'] == 'ok':
        DB_Common().execute_order_GUI(order_details)

        return redirect(url_for("home"))


if __name__ == "__main__":
    # app.run(debug=app.config.get("DEBUG", False), port=5002)
    socketio.run(
        app,
        debug=app.config.get("DEBUG", False),
        port=5002,
        allow_unsafe_werkzeug=True
    )
