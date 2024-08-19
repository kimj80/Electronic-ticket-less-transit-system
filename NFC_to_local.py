import mysql.connector
from mysql.connector import errorcode
import local_database_connection
import NFC_card
import datetime
import time


global config

config = {
  'host':'localhost',
  'user':'root',
  'password':'root', 
  
}

# Checks to see whether a card is listed in the database
def is_in_local_database(physical_nfc_card, cursor):
    cursor.execute("SELECT * FROM card WHERE card_id="+str(physical_nfc_card.id_num))
    rows = cursor.fetchmany(size=1)
    if (len(rows) == 0):
        return False
    else:
        return True

# Retrieves the current balance of a card in the local database

def get_balance(physical_nfc_card, cursor):
    cursor.execute("SELECT balance FROM card WHERE card_id="+str(physical_nfc_card.id_num))
    rows = cursor.fetchmany(size=1)
    if rows[0] == "None":
        print("No balance on this card")
    else:
        result = str(rows[0]).replace('(','').replace(')','').replace(',','')
        print("Current balance for card ID number "+str(physical_nfc_card.id_num)+" is " + result)
        return result

# Retrieves a card's status from the database

def get_status (physical_nfc_card, cursor):
    # every card must have an initial status
    cursor.execute("SELECT status FROM card WHERE card_id="+str(physical_nfc_card.id_num))
    rows = cursor.fetchmany(size=1)
  
    result = str(rows[0]).replace('(','').replace(')','').replace(',','')
    print("Current status for card ID number "+str(physical_nfc_card.id_num)+" is " + result)
    return result

# Checks the card subscription and returns an array of valid zones for the card
# If the card has no subscription then returns None

def get_valid_zones (physical_nfc_card, cursor):
    cursor.execute("SELECT card, sub FROM card_subscription where card ="+str(physical_nfc_card.id_num))
    rows = cursor.fetchmany(size=1)
    if len(rows) == 0:
        print("This card has no subscription and therefore no valid zones")
        return None
    else:
        card_subscription = str(rows[0]).replace(")","").replace("(","").replace(",","").split(" ")
        cursor.execute("SELECT zone FROM subscription_zone WHERE sub ="+str(card_subscription[1]))
        rows = cursor.fetchall()
        result = str(rows).replace('(','').replace(')','').replace(',','').replace("[","").replace("]","").split(" ")
        return result

    
# Updates the card balance in the database by the amount specified
# After updating the database, changes the balance on the physical card

def update_card_balance(physical_nfc_card, cursor, amount):
   
    cursor.execute("SELECT balance FROM card where card_id = "+str(physical_nfc_card.id_num))
    rows = cursor.fetchmany(size=1)
    result = int(str(rows[0]).replace('(','').replace(')','').replace(',',''))

    final_balance = result + amount
    cursor.execute("UPDATE card SET balance = " + str(final_balance) + " WHERE card_id=" + str(physical_nfc_card.id_num))

    # Update the physical card balance to match with the database

    physical_nfc_card.balance = final_balance

    return final_balance

# Adds any new card actions from the physical card into the database

def update_card_actions(physical_nfc_card, cursor):

    #Check if there are any new actions to add to the local database

    if len(physical_nfc_card.card_actions) == 0:
        print("No new card actions to update.")
        return None

    else:
        actions = physical_nfc_card.card_actions 

        for action in actions:

            human_time = NFC_card.epoch_to_human_time(action.timestamp)
            datetime_time = datetime.datetime.strptime(human_time, "%Y-%m-%d %H:%M:%S.%f")  
            transaction_id = str(physical_nfc_card.id_num) + "-" + str(human_time)
    
            cursor.execute("INSERT IGNORE INTO card_action (transaction_id, card, zone, amount, charge, time, bus_number) VALUES ("+"'"+
            str(transaction_id)+"'"+", "+"'"+str(physical_nfc_card.id_num)+"'"+", "+"'"+
            str(1)+"'"+", "+"'"+str(action.balance_change)+"'"+", "+"'"+str(action.new_balance)+"'"+", "+"'"+str(human_time)+"'"+", "+"'"
            +str(action.bus_number)+"'"+")")

# Adds a new card action to a physical nfc card

def insert_card_action(physical_nfc_card, cursor, date, amount, change, zone, bus_number):

    new_card_action = physical_nfc_card.card_action
    new_card_action.timestamp = date
    new_card_action.balance_change = change
    new_card_action.zone = zone
    new_card_action.bus_number = bus_number
    new_card_action.new_balance = physical_nfc_card.balance + change

    # Add the action to the physical card
    # First check if the list is full

    if len(physical_nfc_card.card_actions == 12):
        # In this case the list is full
        # We save all of the current actions in the database and overwrite the oldest action on the card
        update_card_actions(physical_nfc_card, cursor)
        physical_nfc_card.card_actions[0] = new_card_action
    
    else:
        # There is space to add this action to the end of the list
        physical_nfc_card.card_actions.append(new_card_action)

    
# This function handles the scanning of a physical card
# Makes necessary changes to the physical card and the local DB

def on_scan_physical_card(physical_nfc_card, cursor, current_zone, current_date, bus_number):

    card_balance = physical_nfc_card.balance
    valid_zones = physical_nfc_card.subscrip_zones

    if (physical_nfc_card.status == 3):
        # Reject the card action, the card is suspended
        print("Rejected.")
    elif (physical_nfc_card.status == 4):
        # Reject the card action, the card is expired
        print("Rejected.")
    elif current_zone not in valid_zones:
        # The card will be up charged
        # Get the fee for the current zone from the database
        fee = 50
        if (card_balance - fee < 0):
            # reject the action due to insufficient balance
            print("Rejected.")
        else: 
            physical_nfc_card.balance = card_balance - fee
            update_card_balance(physical_nfc_card, cursor, fee*(-1))
            insert_card_action(physical_nfc_card, current_date, fee, physical_nfc_card.balance, current_zone, bus_number)
            
    else:

        # Check if the card subscription has expired

        if (physical_nfc_card.subscrip_time < current_date):
            # The subscription has expired
            # Get the fee for the zone
            fee = 50
            if (card_balance - fee < 0):
                # reject the action due to insufficient balance
                print("Rejected.")
            else: 
                physical_nfc_card.balance = card_balance - fee
                update_card_balance(physical_nfc_card, cursor, fee*(-1))
                insert_card_action(physical_nfc_card, current_date, fee, physical_nfc_card.balance, current_zone, bus_number)
        else:

            # The card has a valid subscription which is not expired
            fee = 0
            insert_card_action(physical_nfc_card, current_date, fee, physical_nfc_card.balance, current_zone, bus_number)

    


def main():

    # Establish connection to the local DB

    my_conn, my_cursor = local_database_connection.connect_to_host(**config)

    # New card object for testing (not an actual card)

    a = NFC_card.physical_nfc_card()

    # Iniitalize the card

    a.init_new_card()

    print(a)

    # Testing -- Check to see if the card is active in the local database

    print(is_in_local_database(a, my_cursor))
    # above statement returns False


    # Change the card ID to one that is already in the local DB, below statement returns true
    a.id_num = 64
    print(is_in_local_database(a, my_cursor))
    # returns True


    print(get_balance(a, my_cursor))

    update_card_balance(a, my_cursor, -500)
    print(get_balance(a, my_cursor))

    update_card_actions(a, my_cursor)

    get_valid_zones(a, my_cursor)

    my_conn.commit()
    my_cursor.close()
    my_conn.close()

    print("Done.")

if __name__ == "__main__":
    main()

