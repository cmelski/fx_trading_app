import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
file_path = Path(__file__).parent.parent / "test.env"
load_dotenv(file_path)


def create_db():
    try:
        # Connect to the default database (e.g. 'postgres')
        with psycopg.connect(
                host=os.environ.get('DB_HOST'),
                dbname=os.environ.get('DB_NAME_DEFAULT'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                port=os.environ.get('DB_PORT')
        ) as conn:
            # Enable autocommit mode
            conn.autocommit = True

            with conn.cursor() as cur:
                db_name = os.environ.get('DB_NAME')
                cur.execute(f"CREATE DATABASE {db_name};")
                print("Database created successfully!")

    except psycopg.Error as e:
        print(f"Duplicate DB: {e}")


def create_table():
    # Connect to your target database
    with psycopg.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT')
    ) as conn:
        conn.autocommit = True  # Apply changes immediately (no explicit commit needed)

        with conn.cursor() as cur:
        # ccy pair table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ccy_pairs (
                    ccy_pair_id SERIAL PRIMARY KEY,
                    ccy_pair VARCHAR(6) NOT NULL,
                    trade_limit NUMERIC(12, 2),
                    convention VARCHAR(12),
                    current_position NUMERIC(12, 2)
                );
            """)

            # Trade table

            cur.execute("""
                        CREATE TABLE IF NOT EXISTS trade_blotter (
                            trade_id SERIAL PRIMARY KEY,
                            trade_status VARCHAR(50) NOT NULL,
                            timestamp VARCHAR(50) NOT NULL,
                            ccy_pair VARCHAR(6) NOT NULL,
                            direction VARCHAR(4) NOT NULL,
                            base_ccy VARCHAR(3) NOT NULL,
                            base_amount VARCHAR(50) NOT NULL,
                            counter_ccy VARCHAR(3) NOT NULL,
                            counter_ccy_amount VARCHAR(50) NOT NULL,
                            rate VARCHAR(20),
                            dealt_rate VARCHAR(20),
                            markup VARCHAR(20),
                            profit VARCHAR(50),
                            source VARCHAR(10)
                        );
                    """)

        # rate table

            cur.execute("""
                                CREATE TABLE IF NOT EXISTS spot_rate (
                                    rate_id SERIAL PRIMARY KEY,
                                    timestamp VARCHAR(50) NOT NULL,
                                    ccy_pair VARCHAR(6) NOT NULL,
                                    spot_rate VARCHAR(20)
                                );
                            """)

        print("✅ Tables created successfully!")



