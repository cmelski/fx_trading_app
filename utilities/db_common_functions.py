from utilities.db_connect import DB_Connect


class DB_Common():

    def __init__(self):
        self.connection = DB_Connect()

    def retrieve_ccy_pairs(self):

        cursor = self.connection.cursor
        cursor.execute("SELECT * from ccy_pairs;")
        ccy_pairs = cursor.fetchall()
        print(ccy_pairs)
        cursor.close()
        return ccy_pairs

    def execute_trade(self, trade_details):
        cursor = self.connection.cursor
        cursor.execute(f'SELECT * FROM trade_blotter LIMIT 0')
        column_names = [desc[0] for desc in cursor.description]

        new_trade = f"INSERT INTO trade_blotter({column_names[1]}," \
                   f"{column_names[2]}, {column_names[3]}, {column_names[4]}, {column_names[5]}, {column_names[6]}, {column_names[7]}, {column_names[8]}, {column_names[9]})" \
                   f" VALUES('{trade_details[0]}','{trade_details[1]}', '{trade_details[2]}', '{trade_details[3]}', '{trade_details[4]}', '{trade_details[5]}', '{trade_details[6]}', '{trade_details[7]}', '{trade_details[8]}');"
        cursor.execute(new_trade)
        self.connection.commit()
        cursor.close()

    def retrieve_trades(self):
        cursor = self.connection.cursor
        cursor.execute("SELECT * from trade_blotter;")
        trades = cursor.fetchall()
        print(trades)
        cursor.close()
        return trades


