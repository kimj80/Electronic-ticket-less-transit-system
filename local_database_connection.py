import mysql.connector
from mysql.connector import errorcode

# Input connection string information into a struct

config = {
  'host':'localhost',
  'user':'root',
  'password':'root'
}

config_remote = {
    'host': 'test.mariadb.database.azure.com',
    'user': 'test@test',
    'password': 'test',
    'database': 'test'
}
# Function to connect using connection parameters

def connect_to_host(**params):

  try:
    conn = mysql.connector.connect(**config)
    print("Connection established to Local Database")
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      print("Something is wrong with the user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      print("Database does not exist")
    else:
      print(err)
  else:
    cursor = conn.cursor(buffered = True)
    Create_Bus_System(cursor)
    return conn, cursor

def connect_to_host_remote(**config):
  try:
    conn = mysql.connector.connect(**config)
    print("Connection established to Remote Database")
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      print("Something is wrong with the user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      print("Database does not exist")
    else:
      print(err)
  else:
    cursor = conn.cursor()
    return conn, cursor

# After connecting to the server, create the bus_system database if it doesn't already exist
# Use the bus_system

def Create_Bus_System(cursor):
  cursor.execute("CREATE DATABASE IF NOT EXISTS bus_system;")
  cursor.execute("USE bus_system;")
  return


def Create_Card_Table(cursor):
  cursor.execute("CREATE TABLE IF NOT EXISTS card( \
    card_ID INT NOT NULL, \
    manufacturer_id VARCHAR(50) NOT NULL,\
    user INT, \
    status BIT(8) NOT NULL, \
    balance INT NOT NULL, \
    expiry DATETIME NOT NULL, \
    PRIMARY KEY(card_ID), \
    CONSTRAINT user_card FOREIGN KEY(user) REFERENCES auth_user(id)) \
    ENGINE = InnoDB;")

  print("created card table")

  return

def Create_Card_Subscriptions_Table(cursor):
  cursor.execute("CREATE TABLE IF NOT EXISTS card_subscription( \
    card INT NOT NULL, \
    sub INT NOT NULL, \
    expiry DATETIME, \
    PRIMARY KEY(card, sub),\
    CONSTRAINT card_constraint FOREIGN KEY(card) REFERENCES card(card_ID), \
    CONSTRAINT sub_constraint FOREIGN KEY(sub) REFERENCES subscription(sub_ID)) \
    ENGINE = InnoDB;")

  print("created card_subscription table")

  return

def Create_Subscription(cursor):
  cursor.execute("CREATE TABLE IF NOT EXISTS subscription( \
    sub_ID INT NOT NULL, \
    title VARCHAR(100) NOT NULL, \
    type BIT(2) NOT NULL, \
    rate INT NOT NULL,\
    PRIMARY KEY(sub_ID)) \
    ENGINE = InnoDB;")

  print("created subscription table")

  return

def Create_Subscription_Zones_Table(cursor):
  cursor.execute("CREATE TABLE IF NOT EXISTS subscription_zone( \
    sub INT NOT NULL, \
    zone INT NOT NULL, \
    PRIMARY KEY(sub, zone), \
    CONSTRAINT subscription FOREIGN KEY(sub) REFERENCES subscription(sub_id), \
    CONSTRAINT zone FOREIGN KEY(zone) REFERENCES travel_zone(zone_id)) \
    ENGINE = InnoDB;")

  print("created subscription_zone table")

  return

def Create_Travel_Zone_Table(cursor):
  cursor.execute("CREATE TABLE IF NOT EXISTS travel_zone( \
    zone_ID INT NOT NULL, \
    zone_name VARCHAR(256) NOT NULL, \
    ride_charge INT NOT NULL, \
    PRIMARY KEY(zone_id)) \
    ENGINE = InnoDB;")

  print("created travel_zone table")
  
  return

def Create_Card_Action_Table(cursor):
  cursor.execute("CREATE TABLE IF NOT EXISTS card_action( \
    transaction_ID VARCHAR(256) NOT NULL, \
    card INT NOT NULL, \
    zone INT, \
    new_amount INT NOT NULL,\
    charge INT NOT NULL, \
    time DATETIME NOT NULL, \
    bus_number INT, \
    CONSTRAINT cards FOREIGN KEY(card) REFERENCES card(card_ID), \
    CONSTRAINT zones FOREIGN KEY(zone) REFERENCES travel_zone(zone_ID), \
    PRIMARY KEY(transaction_ID)) \
    ENGINE = InnoDB;")

  print("created card_action table")

  return

def Empty_Database_Tables(cursor):
  cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
  cursor.execute("TRUNCATE TABLE card_action;")
  cursor.execute("TRUNCATE TABLE card_subscription;")
  cursor.execute("TRUNCATE TABLE subscription_zone;")
  cursor.execute("TRUNCATE TABLE subscription;")
  cursor.execute("TRUNCATE TABLE travel_zone;")
  cursor.execute("TRUNCATE TABLE card;")
  cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
  
def Delete_Database_Tables(cursor):
  cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
  cursor.execute("DELETE TABLE card_action;")
  cursor.execute("DELETE TABLE user;")
  cursor.execute("DELETE TABLE card_subscription;")
  cursor.execute("DELETE TABLE subscription_zone;")
  cursor.execute("DELETE TABLE subscription;")
  cursor.execute("DELETE TABLE travel_zone;")
  cursor.execute("DELETE TABLE card;")
  cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

def Insert_New_Card_Entry(card_id, manuf_id, user, status, balance, expiry, cursor):
  cursor.execute("INSERT IGNORE INTO card VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" \
     % (card_id, manuf_id, user, status, balance, expiry))
  return None

def Insert_New_Subscription(sub_ID, title, type, rate, cursor):
  cursor.execute("INSERT IGNORE INTO subscription VALUES('%s', '%s', '%s', '%s')" \
     % (sub_ID, title, type, rate))
  return None

def Insert_New_Travel_Zone(zone_ID, zone_name, ride_charge, cursor):
   cursor.execute("INSERT IGNORE INTO travel_zone VALUES('%s', '%s', '%s')" \
     % (zone_ID, zone_name, ride_charge))
   return None

def Insert_New_Card_Action(transaction_ID, card, zone, new_amount, charge, time, bus_number, cursor):
   cursor.execute("INSERT IGNORE INTO card_action VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s')" \
     % (transaction_ID, card, zone, new_amount, charge, time, bus_number))
   return None

def Insert_New_Card_Subscription(card_ID, sub_ID, expiry, cursor):
  cursor.execute("INSERT IGNORE INTO card_subscription VALUES('%s', '%s', '%s')" \
     % (card_ID, sub_ID, expiry))
  return None

def Insert_New_Subscription_Zone(sub_ID, zone_ID, cursor):
  cursor.execute("INSERT IGNORE INTO subscription_zone VALUES('%s', '%s')" \
     % (sub_ID, zone_ID))
  return None

def close_connection(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()

if __name__ == "__main__":
#   main()
    conn, cursor = connect_to_host_remote(**config_remote)

    # Delete_Database_Tables(cursor)

    Create_Card_Table(cursor)
    Create_Travel_Zone_Table(cursor)
    Create_Subscription(cursor)
    Create_Subscription_Zones_Table(cursor)
    Create_Card_Subscriptions_Table(cursor)
    Create_Card_Action_Table(cursor)

    close_connection(conn, cursor)
#     # For Testing Purposes

#     Insert_New_Card_Entry(151, 'M050DHG', 31, 0, 250, '2013-07-22 12:50:05', cursor)
#     Insert_New_Subscription(1, 'Basic Subscription', 1, 3000, cursor)
#     Insert_New_Travel_Zone(1, 'Callingwood', 500, cursor)
#     Insert_New_Card_Action('awd-3454-dfdf', 151, 1, 5000, 500, '2011-03-11 03:11:46.123400', 6, cursor)
#     Insert_New_Card_Subscription(64, 1, '2029-01-22 11:34:06', cursor)
#     Insert_New_Subscription_Zone(1, 1, cursor)


#     conn.commit()
#     cursor.close()
#     conn.close()
#     print("Done.")