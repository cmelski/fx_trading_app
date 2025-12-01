from flask import jsonify

from utilities.db_connect import DB_Connect


class DB_Common():

    def __init__(self):
        self.connection = DB_Connect()

    def retrieve_ccy_pairs(self):
        cursor = self.connection.cursor
        cursor.execute("SELECT * from ccy_pairs order by ccy_pair_id asc;")
        ccy_pairs = cursor.fetchall()
        print(ccy_pairs)
        cursor.close()
        return ccy_pairs

    def execute_trade(self, trade_details):
        cursor = self.connection.cursor
        cursor.execute(f'SELECT * FROM trade_blotter LIMIT 0')
        column_names = [desc[0] for desc in cursor.description]

        new_trade = f"INSERT INTO trade_blotter({column_names[1]}," \
                    f"{column_names[2]}, {column_names[3]}, {column_names[4]}, {column_names[5]}, {column_names[6]}, {column_names[7]}, {column_names[8]}, {column_names[9]}, {column_names[10]}, {column_names[11]}, {column_names[12]}, {column_names[13]})" \
                    f" VALUES('{trade_details[0]}','{trade_details[1]}', '{trade_details[2]}', '{trade_details[3]}', '{trade_details[4]}', '{trade_details[5]}', '{trade_details[6]}', '{trade_details[7]}', '{trade_details[8]}', '{trade_details[9]}', '{trade_details[10]}', '{trade_details[11]}', '{trade_details[12]}');"
        cursor.execute(new_trade)
        self.connection.commit()
        cursor.close()

    def retrieve_trades(self):
        cursor = self.connection.cursor
        cursor.execute("SELECT * from trade_blotter ORDER BY timestamp desc;")
        trades = cursor.fetchall()
        print(trades)
        cursor.close()
        return trades

    def insert_spot_rate(self, time, ccy_pair, rate):
        cursor = self.connection.cursor
        cursor.execute(f'SELECT * FROM spot_rate LIMIT 0')
        column_names = [desc[0] for desc in cursor.description]

        spot_rate = f"INSERT INTO spot_rate({column_names[1]}," \
                    f"{column_names[2]}, {column_names[3]})" \
                    f" VALUES('{time}','{ccy_pair}', '{rate}');"
        cursor.execute(spot_rate)
        self.connection.commit()
        cursor.close()

    def update_spot_rate(self, time, ccy_pair, rate):
        cursor = self.connection.cursor
        cursor.execute(
            f'Update spot_rate '
            f'Set timestamp = %s, spot_rate = %s '
            f'WHERE ccy_pair = %s;',
            (time, rate, ccy_pair,)
        )
        self.connection.commit()
        cursor.close()

    def retrieve_rates(self, ccy_pairs):
        rates = dict()
        cursor = self.connection.cursor

        for ccy_pair in ccy_pairs:

            cursor.execute(
                f'SELECT * FROM spot_rate '
                f'WHERE ccy_pair = %s;',
                (ccy_pair[0],)
            )
            rate = cursor.fetchone()
            print(rate)
            fx_rate = rate[3]
            rates[ccy_pair[0]] = (fx_rate, ccy_pair[1], ccy_pair[2])
        cursor.close()

        return rates

    def delete_rates(self):
        cursor = self.connection.cursor
        cursor.execute("DELETE from spot_rate;")
        self.connection.commit()
        cursor.close()

    def check_position(self, ccy_pair, trade_amount, direction):
        cursor = self.connection.cursor
        response_dict = dict()

        cursor.execute(
            f'SELECT * FROM ccy_pairs '
            f'WHERE ccy_pair = %s;',
            (ccy_pair,)
        )
        ccy_pair = cursor.fetchone()
        cursor.close()

        position = float(ccy_pair[4])  # handles Decimal, strings, 0.00
        amount = float(str(trade_amount).replace(',', ''))
        limit = float(ccy_pair[2])

        print(position, amount, limit)

        if direction == 'Buy':

            if position + amount > limit:
                response_dict['status'] = 'error'
                response_dict['message'] = 'Trade exceeds remaining balance'
                response_dict['remaining_balance'] = ccy_pair[4]
                return response_dict
            else:
                response_dict['status'] = 'ok'
                return response_dict

        elif direction == 'Sell':

            if position - amount < (limit - limit - limit):
                response_dict['status'] = 'error'
                response_dict['message'] = 'Trade exceeds remaining balance'
                response_dict['remaining_balance'] = ccy_pair[4]
                return response_dict
            else:
                response_dict['status'] = 'ok'
                return response_dict

    def update_position(self, ccy_pair, trade_amount, direction):

        cursor = self.connection.cursor
        response_dict = dict()

        cursor.execute(
            f'SELECT * FROM ccy_pairs '
            f'WHERE ccy_pair = %s;',
            (ccy_pair,)
        )
        ccy_pair_info = cursor.fetchone()
        current_position = float(ccy_pair_info[4])  # handles Decimal, strings, 0.00
        amount = float(str(trade_amount).replace(',', ''))

        if direction == 'Buy':
            new_position = current_position + amount
        else:
            new_position = current_position - amount

        print(f'new position {new_position}')

        cursor.execute(
            f'Update ccy_pairs '
            f'Set current_position = %s '
            f'WHERE ccy_pair = %s;',
            (new_position, ccy_pair,)
        )
        self.connection.commit()

        cursor.close()

        response_dict['status'] = 'ok'
        response_dict['current_position'] = new_position
        response_dict['max_limit'] = ccy_pair_info[2]
        return response_dict

    def clear_position(self, ccy_pair):
        cursor = self.connection.cursor
        cursor.execute(
            f'Update ccy_pairs '
            f'Set current_position = 0.00 '
            f'WHERE ccy_pair = %s;',
            (ccy_pair,)
        )
        self.connection.commit()
        cursor.close()

    def get_spot_rate(self, ccy_pair):

        cursor = self.connection.cursor

        cursor.execute(
            f'SELECT * FROM spot_rate '
            f'WHERE ccy_pair = %s;',
            (ccy_pair,)
        )
        rate = cursor.fetchone()
        print(rate)
        cursor.close()

        return rate[3]
