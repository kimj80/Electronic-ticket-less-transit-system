
from random import randint
import mysql.connector as mariadb
from mysql.connector import errorcode
from datetime import datetime
import time

import os
from dotenv import load_dotenv
import db_create

load_dotenv()  # load secret environment variables from .env file 

# Parameters for accessing the locally hosted database
local_db_config = {
    'host': os.environ.get("local_db_host"),
    'user': os.environ.get("local_db_user"),
    'password': os.environ.get("local_db_password"),
    'database': os.environ.get("local_db_name")
}

# Parameters for accessing the remotely hosted database
remote_db_config = {
    'host': os.environ.get("remote_db_host"),
    'user': os.environ.get("remote_db_user"),
    'password': os.environ.get("remote_db_password"),
    'database': os.environ.get("remote_db_name")
}

#! ------------------------------
#! ----- Database Connection ----
#! ------------------------------

# Accepts bd_type of: "L" "local", "R" "remote"
# Optional argument "create_new" can be set to true if we need to create a new database 
def open_db_conn(db_type, create_new=False ):

    # Set parameters for db connection
    if isinstance(db_type, str):
        db_type = db_type.lower()

        # REMOTE
        if db_type == "r" or db_type == "remote":
            config = remote_db_config
            # If creating new DB for the first time - pop out database name from dict.
            if create_new:
                config = remote_db_config.copy()
                config.pop('database')

        # LOCAL
        elif db_type == "l" or db_type == "local":
            config = local_db_config
            # If creating new DB for the first time - pop out database name from dict.
            if create_new:
                config = local_db_config.copy()
                config.pop('database')

    else:
        print("Invalid db type")
        return None, None

    # Establish db connection
    try:
        conn = mariadb.connect(**config)
        cursor = conn.cursor()
        # print("Database connection established")
    except mariadb.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with the user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return None, None
    return conn, cursor

# CLose connection passed in (local or remote)
def close_db_con(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()


#! ------------------------------
#! ----- INSERT New Entries -----
#! ------------------------------

def Insert_New_Card(card_id, manuf_id, user, status, balance, expiry, cursor):
    try:
        sql = "INSERT  INTO card VALUES (%s, %s, %s, %s, %s, %s)"
        expiry = datetime.fromtimestamp(expiry / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f")
        val = (card_id, manuf_id, user, status, balance, expiry)
        cursor.execute(sql, val)
    except:
        sql = "INSERT  INTO card VALUES (%s, %s, %s, %s, %s, %s)"
        val = (card_id, manuf_id, user, status, balance, expiry)
        cursor.execute(sql, val)

def Insert_New_Subscription(sub_ID, title, type, rate, cursor):
    sql = "INSERT  INTO subscription VALUES(%s, %s, %s, %s)"
    val = (sub_ID, title, type, rate)
    cursor.execute(sql, val)

def Insert_New_Travel_Zone(zone_ID, zone_name, ride_charge, cursor):
    sql = "INSERT  INTO travel_zone VALUES(%s, %s, %s)"
    val = (zone_ID, zone_name, ride_charge)
    cursor.execute(sql, val)

# TODO Added "type" that was forgotten. If this is breaking check that first.
def Insert_New_Card_Action(transaction_ID, card, zone, new_amount, charge, type, time, bus_number, verification, cursor):
    try:
        sql = "INSERT  INTO card_action VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        time = datetime.fromtimestamp(time / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f")
        val = (transaction_ID, card, zone, new_amount, charge, type, time, bus_number, verification)
        cursor.execute(sql, val)
    except:
        sql = "INSERT  INTO card_action VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (transaction_ID, card, zone, new_amount, charge, type, time, bus_number, verification)
        cursor.execute(sql, val)

def Insert_New_Card_Subscription(card_ID, sub_ID, expiry, cursor):
    try:
        sql = "INSERT  INTO card_subscription VALUES(%s, %s, %s)"
        expiry = datetime.fromtimestamp(expiry / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f")
        val = (card_ID, sub_ID, expiry)
        cursor.execute(sql, val)
    except:
        sql = "INSERT  INTO card_subscription VALUES(%s, %s, %s)"
        val = (card_ID, sub_ID, expiry)
        cursor.execute(sql, val)

def Insert_New_Subscription_Zone(sub_ID, zone_ID, cursor):
    sql = "INSERT  INTO subscription_zone VALUES(%s, %s)"
    val = (sub_ID, zone_ID)
    cursor.execute(sql, val)

def Insert_New_transaction_types(type_ID, description, location, cursor):
    sql = "INSERT INTO transaction_types(type_ID, description, location)VALUES(%s, %s, %s)"
    val = (type_ID, description, location)
    cursor.execute(sql, val)

#! -----------------------------------
#! ----- UPDATE Existing Entries -----
#! -----------------------------------

# Updates the balance of a card in the remote DB
def update_balance(cursor, card_ID, amount):
    sql = "UPDATE  card SET balance = %s WHERE card_id = %s"
    val = (amount, card_ID)
    cursor.execute(sql, val)

# Updates the user id of a card in the remote DB. If no user given, default removes linked user from card
def update_user(cursor, card_ID, user=None):
    sql = "UPDATE  card SET user = %s WHERE card_id = %s"
    val = (user, card_ID)
    cursor.execute(sql, val)


#! ------------------------------------
#! ----- SELECT Existing Entries ------
#! ------------------------------------

# Returns a list of card actions from the local database for a specific card_ID. No card entry specified defaults to return all card actions
def get_card_actions(cursor, card_ID=None):
    if card_ID:
        sql = "SELECT * FROM card_action WHERE card_id = %s"
        val = (card_ID, )
        cursor.execute(sql, val)
    else :
        sql = "SELECT * FROM card_action"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

# Returns a card transaction from the database
def get_single_card_transaction(cursor, transaction_ID):
    sql = "SELECT * FROM card_action WHERE transaction_ID = %s"
    val = (transaction_ID, )
    cursor.execute(sql, val)
    rows = cursor.fetchall()
    return rows

# Returns a list of cards from the local database
def get_cards(cursor, card_ID=None):
    if card_ID:
        sql = "SELECT * FROM card WHERE card_ID = %s"
        val = (card_ID, )
        cursor.execute(sql, val)
    else :
        sql = "SELECT * FROM card"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

# Return list of tansaction types. Filtered on location field if given.
def get_transaction_types(cursor, location=None):
    if location:
        sql = "SELECT * FROM transaction_types WHERE location = %s"
        val = (location, )
        cursor.execute(sql, val)
    else :
        sql = "SELECT * FROM transaction_types"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

def get_card_subscription(cursor, card_ID=None):
    if card_ID:
        sql = "SELECT * FROM card_subscription WHERE card = %s"
        val = (card_ID, )
        cursor.execute(sql, val)
    else:
        sql = "SELECT * FROM card_subscription"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

def get_subscription(cursor, sub_ID=None):
    if sub_ID:
        sql = "SELECT * FROM subscription WHERE sub_ID = %s"
        val = (sub_ID, )
        cursor.execute(sql, val)
    else:
        sql = "SELECT * FROM subscription"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

def get_subscription_zone(cursor, sub=None):
    if sub:
        sql = "SELECT * FROM subscription_zone WHERE sub = %s"
        val = (sub, )
        cursor.execute(sql, val)
    else:
        sql = "SELECT * FROM subscription_zone"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

def get_travel_zone(cursor, zone_ID=None):
    if zone_ID:
        sql = "SELECT * FROM travel_zone WHERE zone_ID = %s"
        val = (zone_ID, )
        cursor.execute(sql, val)
    else:
        sql = "SELECT * FROM travel_zone"
        cursor.execute(sql)
    rows = cursor.fetchall()
    return rows

#! ------------------------------------
#! ----- DELETE Existing Entries ------
#! ------------------------------------

# Delete card from database
def delete_card(cursor, card_ID):
    sql = "DELETE FROM card WHERE card_ID = %s"
    val = (card_ID, )
    cursor.execute(sql, val)

def delete_card_subscription(cursor, card_ID):
    sql = "DELETE FROM card_subscription WHERE card = %s"
    val = (card_ID, )
    cursor.execute(sql, val)

def delete_subscription(cursor, sub_ID):
    sql = "DELETE FROM subscription WHERE sub_ID = %s"
    val = (sub_ID, )
    cursor.execute(sql, val)

def delete_subscription_zone(cursor, sub):
    sql = "DELETE FROM subscription_zone WHERE sub = %s"
    val = (sub, )
    cursor.execute(sql, val)

def delete_travel_zone(cursor, zone_ID):
    sql = "DELETE FROM travel_zone WHERE zone_ID = %s"
    val = (zone_ID, )
    cursor.execute(sql, val)

def delete_card_actions(cursor, card_ID):
    sql = "DELETE FROM card_action WHERE card_id = %s"
    val = (card_ID, )
    cursor.execute(sql, val)

def delete_transaction_types(cursor, location=None):
    sql = "SELECT * FROM transaction_types WHERE location = %s"
    val = (location, )
    cursor.execute(sql, val)


if __name__ == "__main__":

    conn, cursor = open_db_conn("remote")

    # ---- DROP LOCAL AND REMOTE ----
    conn, cursor = open_db_conn("local")
    db_create.drop_database_tables(cursor)
    close_db_con(conn, cursor)


