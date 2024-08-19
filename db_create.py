
import db_connect

# Create LOCAL database if it doesn't exist
# Can also delete old database if variable delete_old_db is set to "DANGER" and used.
def create_local_db(delete_old_db = False):
    # connect to DB with optional arg create_new set to true
    conn, cursor = db_connect.open_db_conn("local", True)

    # Create db
    localdb = db_connect.local_db_config.copy()
    db_name = localdb.pop('database')

    # Deletes old database before creating new one
    if(delete_old_db == "DANGER"):
        sql = "DROP DATABASE IF EXISTS {}".format(db_name)
        cursor.execute(sql)
        print("Local Database Deleted!!!")

    sql = "CREATE DATABASE IF NOT EXISTS {}".format(db_name)
    cursor.execute(sql)

    sql = "USE {}".format(db_name)
    cursor.execute(sql)
    conn.commit()
    
    if(delete_old_db):
        return

    # create tables specific to local DB
    Create_Transaction_Type_Table(cursor)
    
    Create_Local_Card_Table(cursor)

    # create tables common between local and remote db
    create_common_tables(cursor)

    # conn.commit()
    fill_Default_Travel_Zone(cursor)
    fill_transaction_types_table(cursor)
    db_connect.close_db_con(conn, cursor)
    return

# Create REMOTE database if it doesn't exist
# Can also delete old database if variable delete_old_db is set to "DANGER" and used.
def create_remote_db(delete_old_db = False):
    # connect to DB with optional arg create_new set to true
    conn, cursor = db_connect.open_db_conn("remote", True)
    
    remotedb = db_connect.remote_db_config.copy()
    db_name = remotedb.pop('database')

    # Deletes old database before creating new one
    if(delete_old_db == "DANGER"):
        sql = "DROP DATABASE IF EXISTS {}".format(db_name)
        cursor.execute(sql)
        print("Remote Database Deleted!!!")
    
    # Create db
    sql = "CREATE DATABASE IF NOT EXISTS {}".format(db_name)
    cursor.execute(sql)

    sql = "USE {}".format(db_name)
    cursor.execute(sql)
    conn.commit()

    if(delete_old_db):
        return

    # create tables specific to remote DB
    Create_Transaction_Type_Table(cursor)
    Create_Remote_Card_Table(cursor)
    # create tables common between local and remote db
    create_common_tables(cursor)

    # conn.commit()
    fill_Default_Travel_Zone(cursor)
    fill_transaction_types_table(cursor)

    db_connect.close_db_con(conn, cursor)
    return

# Create tables shared between the 2 databases (local/remote)
def create_common_tables(cursor):
    Create_Travel_Zone_Table(cursor)
    Create_Subscription(cursor)
    Create_Subscription_Zones_Table(cursor)
    Create_Card_Subscriptions_Table(cursor)
    Create_Card_Action_Table(cursor)
    Create_Transaction_Type_Table(cursor)

def Create_Local_Card_Table(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS card( \
        card_ID VARCHAR(256) NOT NULL, \
        manufacturer_id VARCHAR(50) NOT NULL,\
        user INT, \
        status INT NOT NULL, \
        balance INT NOT NULL, \
        expiry DATETIME NOT NULL, \
        PRIMARY KEY(card_ID)) \
        ENGINE = InnoDB;")
    print("created card table")
    return

def Create_Remote_Card_Table(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS card( \
        card_ID VARCHAR(256) NOT NULL, \
        manufacturer_id VARCHAR(50) NOT NULL,\
        user INT, \
        status INT NOT NULL, \
        balance INT NOT NULL, \
        expiry DATETIME NOT NULL, \
        PRIMARY KEY(card_ID), \
        CONSTRAINT user_constraint FOREIGN KEY(user) REFERENCES auth_user(id))\
        ENGINE = InnoDB;")
    print("created card table")
    return

def Create_Card_Subscriptions_Table(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS card_subscription( \
        card VARCHAR(256) NOT NULL, \
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
        type INT NOT NULL, \
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
        card_id VARCHAR(256) NOT NULL, \
        zone INT, \
        new_amount INT NOT NULL,\
        charge INT NOT NULL, \
        type INT NOT NULL, \
        time DATETIME NOT NULL, \
        bus_number INT, \
        verification INT, \
        CONSTRAINT cards FOREIGN KEY(card_id) REFERENCES card(card_ID), \
        CONSTRAINT zones FOREIGN KEY(zone) REFERENCES travel_zone(zone_ID), \
        CONSTRAINT transaction_type FOREIGN KEY(type) REFERENCES transaction_types(type_ID), \
        PRIMARY KEY(transaction_ID)) \
        ENGINE = InnoDB;")
    print("created card_action table")
    return

def Create_Transaction_Type_Table(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS transaction_types( \
        type_ID INT NOT NULL, \
        description VARCHAR(256) NOT NULL, \
        location VARCHAR(256) NOT NULL, \
        PRIMARY KEY(type_ID)) \
        ENGINE = InnoDB;")
    print("created transaction_types table")
    return

# Works on both local and remote depending on what cursor gets passed to it
def Empty_Database_Tables(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
    # Common tables
    cursor.execute("TRUNCATE TABLE IF EXISTS card_action;")
    cursor.execute("TRUNCATE TABLE IF EXISTS card_subscription;")
    cursor.execute("TRUNCATE TABLE IF EXISTS subscription_zone;")
    cursor.execute("TRUNCATE TABLE IF EXISTS subscription;")
    cursor.execute("TRUNCATE TABLE IF EXISTS travel_zone;")
    cursor.execute("TRUNCATE TABLE IF EXISTS transaction_types;")
    # Remote specific tables
    cursor.execute("TRUNCATE TABLE IF EXISTS card;")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
    print("Tables Emptied")
    return

# Works on both local and remote depending on what cursor gets passed to it
def drop_database_tables(cursor):
    cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
    # Common tables
    cursor.execute("DROP TABLE IF EXISTS card_action;")
    cursor.execute("DROP TABLE IF EXISTS card_subscription;")
    cursor.execute("DROP TABLE IF EXISTS subscription_zone;")
    cursor.execute("DROP TABLE IF EXISTS subscription;")
    cursor.execute("DROP TABLE IF EXISTS travel_zone;")
    cursor.execute("DROP TABLE IF EXISTS transaction_types;")
    # Remote specific tables
    cursor.execute("DROP TABLE IF EXISTS card;")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
    print("Tables Deleted")
    return


def fill_transaction_types_table(cursor):
    sql = "INSERT INTO transaction_types(type_ID, description, location)VALUES(%s, %s, %s)"
    val = [
        (0, "Default (blank)", "default"),
        (1, "Card Initialization", "card"),
        (2, "Tap on bus", "card"),
        (3, "Tap off bus", "card"),
        (4, "Sync online changes with physical card", "card"),
        (5, "Add balance to card online", "online"),
        (6, "Update card status online", "online"),
        (7, "link card to user account", "web_only"),
        (8, "transfer card funds", "online"),
        (9, "Add subscription time to card", "online"),

    ]
    cursor.executemany(sql, val)

def fill_Default_Travel_Zone(cursor):
    db_connect.Insert_New_Travel_Zone(0, 'Default', 0, cursor)

def fill_Default_Subscriptions(cursor):
    db_connect.Insert_New_Subscription(0, 'Zero', 0, 0, cursor)
    db_connect.Insert_New_Subscription(1, 'Default', 1, 0, cursor)
        
    
    """
    sub_ID INT NOT NULL, \
    title VARCHAR(100) NOT NULL, \
    type INT NOT NULL, \
    rate INT NOT NULL,\
    """


if __name__ == "__main__":

    create_local_db()