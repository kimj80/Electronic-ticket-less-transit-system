import local_database_connection
from datetime import datetime

global config_local
global config_remote

config_local = {
  'host':'localhost',
  'user':'test',
  'password':'test',
}

config_remote = {
    'host': 'test.mariadb.database.azure.com',
    'user': 'test@test',
    'password': 'test',
    'database': 'test'
}

def close_connection(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()

def push_to_remote(local_cursor, remote_cursor):
    
    cards = get_local_cards(local_cursor)
    actions = get_local_card_actions(local_cursor)
    update_card_actions_remote(actions, remote_cursor, local_cursor)
    
    return None

def pull_from_remote(local_cursor, remote_cursor):

    actions = get_remote_card_actions(remote_cursor)
    update_card_actions_local(actions, remote_cursor, local_cursor)

    return None

def update_card_status_local(local_cursor, remote_cursor):
    remote_cursor.execute("SELECT status from card")
    rows = remote_cursor.fetchall()
    
    for i in range(0,len(rows)):
        status = rows[i][3]
        local_cursor.execute("UPDATE card SET status = "+str(status)+" WHERE card_id = "+str(rows[i][0]))

    return None

# Updates the balance of a card in the remote DB after a transaction has taken place

def update_balance_remote_db(remote_cursor, card_ID, amount):

    remote_cursor.execute("UPDATE card SET balance = "+str(amount)+" WHERE card_id = "+str(card_ID))

def update_balance_local_db(local_cursor, card_ID, amount):

    local_cursor.execute("UPDATE card SET balance = "+str(amount)+" WHERE card_id = "+str(card_ID))

# Adds a card action to the remote DB and updates the balance of that card in the remote DB

def add_card_action_local_db(local_cursor, card_ID, charge, zone, bus_number):

    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S.%f")

    local_cursor.execute("SELECT balance FROM card WHERE card_id = " + "'"+str(card_ID)+"'")
    current_balance = local_cursor.fetchall()
    current_balance_str = str(current_balance[0])
    int_balance = int(current_balance_str.replace(",","").strip("(").strip(")"))
    new_balance = charge + int_balance

    transaction_id = str(card_ID) + "-" + dt_string

    local_cursor.execute("INSERT IGNORE INTO card_action (transaction_id, card, zone, new_amount, charge, time, bus_number) VALUES ("+"'"+
            transaction_id+"'"+", "+"'"+str(card_ID)+"'"+", "+"'"+
            zone+"','"+str(new_balance)+"'"+", "+"'"+str(charge)+"'"+", "+"'"+dt_string+"','"+bus_number+"')")

    update_balance_local_db(local_cursor, card_ID, new_balance)

def add_card_action_remote_db(remote_cursor, card_ID, charge):

    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S.%f")

    remote_cursor.execute("SELECT balance FROM card WHERE card_id = " + "'"+str(card_ID)+"'")
    current_balance = remote_cursor.fetchall()
    current_balance_str = str(current_balance[0])
    int_balance = int(current_balance_str.replace(",","").strip("(").strip(")"))
    new_balance = charge + int_balance

    transaction_id = str(card_ID) + "-" + dt_string

    remote_cursor.execute("INSERT IGNORE INTO card_action (transaction_id, card, amount, charge, time) VALUES ("+"'"+
            transaction_id+"'"+", "+"'"+str(card_ID)+"'"+", "+"'"+
            str(new_balance)+"'"+", "+"'"+str(charge)+"'"+", "+"'"+dt_string+"')")

    update_balance_remote_db(remote_cursor, card_ID, new_balance)

def get_remote_card_actions(remote_cursor):
    remote_cursor.execute("SELECT * FROM card_action")
    rows = remote_cursor.fetchall()
    return rows

# Returns a list of card actions from the local database
def get_card_actions(cursor):
    cursor.execute("SELECT * FROM card_action")
    rows = cursor.fetchall()
    return rows

def get_cards(cursor):
    cursor.execute("SELECT * FROM card")
    rows = cursor.fetchall()
    return rows

def show_database(cursor):
    cards = get_cards(cursor)
    actions = get_card_actions(cursor)
    print("\nLOCAL CARDS:")
    for i in range(0, len(cards)):
        print(cards[i]) 
    print("\n")    
    print("\nLOCAL ACTIONS:")
    for i in range(0, len(actions)):
        print(actions[i])
    return

def update_cards(cards, remote_cursor):
    if len(cards) > 0:
        for i in range(0, len(cards)):
            try:
                remote_cursor.execute("INSERT IGNORE INTO card (card_id, manufacturer_id, user, status, balance, expiry) VALUES(" +"'"+
                str(cards[0][0])+"'"+", "+"'"+str(cards[0][1])+"'"+", "+"'"+
                str(cards[0][2])+"'"+", "+"'"+str(1)+"'"+", "+"'"+str(cards[0][4])+"'"+", "+"'"+str(cards[0][5])+"'"+")")
            except:
                print("Update failed.")
         
    else:
        print("No new cards to add")
    return None

def update_card_actions_local(actions, remote_cursor, local_cursor):

    if len(actions) > 0:
        for i in range(0,len(actions)):  

            if str(actions[i][2] == "None"):
                zone = "0"  
                bus_number="0"    
            else:
                zone = str(actions[i][2])
                bus_number = str(actions[i][6])  

            local_cursor.execute("INSERT IGNORE INTO card_action (transaction_id, card, zone, new_amount, charge, time, bus_number) VALUES ("+"'"+
            str(actions[i][0])+"'"+", "+"'"+str(actions[i][1])+"'"+", "+"'"+
            zone +"'"+", "+"'"+str(actions[i][3])+"'"+", "+"'"+str(actions[i][4])+"'"+", "+"'"+str(actions[i][5])+"'"+", "+"'"
            +bus_number+"'"+")")

            # Now that the remote has access to all the card transactions including the most recent ones
            # We must make sure the remote card balance reflects the most recent transaction

            local_cursor.execute("SELECT * from card_action WHERE card = "+str(actions[i][1])+" ORDER BY time ASC")
            most_recent_trans = local_cursor.fetchall()
            string_balance = str(most_recent_trans[i][3])
 

            int_balance = string_balance.replace(",","").strip("(").strip(")")

            # Now update the balance on each of the cards in the remote database
            local_cursor.execute("UPDATE card SET balance = "+str(int_balance)+" WHERE card_ID = "+str(actions[i][1]))

            print("success")

    else:
        print("No new card actions to add")
    return None

def sync_databases():
    #todo - complete this for demo 2022-03-01
    pass


# Updates the card actions in the remote database

def update_card_actions_remote(actions, remote_cursor, local_cursor):

    # Gather all transactions in the local database and prepare to push to the remote database

    if len(actions) > 0:
        for i in range(0,len(actions)):            
             
            remote_cursor.execute("INSERT IGNORE INTO card_action (transaction_id, card, zone, amount, charge, time, bus_number) VALUES ("+"'"+
            str(actions[i][0])+"'"+", "+"'"+str(actions[i][1])+"'"+", "+"'"+
            str(actions[i][2])+"'"+", "+"'"+str(actions[i][3])+"'"+", "+"'"+str(actions[i][4])+"'"+", "+"'"+str(actions[i][5])+"'"+", "+"'"
            +str(actions[i][6])+"'"+")")

            # Now that the remote has access to all the card transactions including the most recent ones
            # We must make sure the remote card balance reflects the most recent transaction

            remote_cursor.execute("SELECT * from card_action WHERE card = "+str(actions[i][1])+" ORDER BY time ASC")
            most_recent_trans = remote_cursor.fetchall()
            string_balance = str(most_recent_trans[i][3])
 
            int_balance = string_balance.replace(",","").strip("(").strip(")")

            # Now update the balance on each of the cards in the remote database
            remote_cursor.execute("UPDATE card SET balance = "+str(int_balance)+" WHERE card_id = "+str(actions[i][1]))

            print("success")
                
    else:
        print("No new card actions to add")
    return None

def main():

    # Open two new connections, one to the local database and one to the remote database

    my_local_conn, my_local_cursor = local_database_connection.connect_to_host(**config_local)
    my_remote_conn, my_remote_cursor = local_database_connection.connect_to_host_remote(**config_remote)


    # For the purpose of the demo, we will insert sample data into both databases

    local_database_connection.Insert_New_Card_Entry('132', 'ABCDEFG', '31', 1, 2000, '2030-01-01 12:12:12', my_local_cursor )
    local_database_connection.Insert_New_Card_Entry('133', 'HKGN7Z2', '31', 1, 500, '2030-01-01 12:12:12', my_local_cursor )
    local_database_connection.Insert_New_Card_Entry('134', 'FJFDKS5', '31', 1, 3000, '2030-01-01 12:12:12', my_local_cursor )
    
    local_database_connection.Insert_New_Card_Entry('132', 'ABCDEFG', '31', 1, 2000, '2030-01-01 12:12:12', my_remote_cursor )
    local_database_connection.Insert_New_Card_Entry('133', 'HKGN7Z2', '31', 1, 500, '2030-01-01 12:12:12', my_remote_cursor )
    local_database_connection.Insert_New_Card_Entry('134', 'FJFDKS5', '31', 1, 3000, '2030-01-01 12:12:12', my_remote_cursor )

    while True:
        print("-----APPLICATION MENU-------")
        print("Please select an option below:")
        print("1 - Show Cards in Local Database")
        print("2 - Show Card Actions in Local Database")
        print("3 - Show Cards in Remote Database")
        print("4 - Show Cards Actions in Remote Database")
        print("5 - Add Balance to a Card")
        print("6 - Tap a Card Onto a Bus ($3.00)")
        print("7 - Exit")

        val = int(input("Enter your choice: "))

        if (val == 1):
            my_local_cursor.execute("SELECT * from card")
            local_rows = my_local_cursor.fetchall()
            print("\nLOCAL CARDS:\n")
            for i in range(0,len(local_rows)):
                print(local_rows[i])
            print("\n\n")
        elif (val == 2):
            my_local_cursor.execute("SELECT * from card_action")
            local_rows = my_local_cursor.fetchall()
            
            if (len(local_rows) == 0):
                print("\nNo actions to show.\n")

            else:
                print("\nLOCAL CARD ACTIONS:\n")
                for i in range(0,len(local_rows)):
                    print(local_rows[i])
                print("\n\n")

        elif (val == 3):
            my_remote_cursor.execute("SELECT * from card")
            remote_rows = my_remote_cursor.fetchall()
            print("\n\nREMOTE CARDS:\n")
            for i in range(0,len(remote_rows)):
                print(remote_rows[i])
            print("\n\n")

        elif (val == 4):
            my_remote_cursor.execute("SELECT * from card_action")
            local_rows = my_remote_cursor.fetchall()
            if (len(local_rows) == 0):
                print("\nNo actions to show.\n")
            else:
                print("\nREMOTE CARD ACTIONS:\n")
                for i in range(0,len(local_rows)):
                    print(local_rows[i])
                print("\n\n")

        elif (val == 5):
            card = input("Enter the ID of the card you wish to add balance to: ")
            my_remote_cursor.execute("SELECT * FROM card WHERE card_id = "+str(card))
            rows = my_remote_cursor.fetchall()
            if len(rows) == 0:
                print("Not a valid card. Please try again.")
            else:
                amount = int(input("Enter the amount to add: "))
                add_card_action_remote_db(my_remote_cursor, str(card), amount)
                pull_from_remote(my_local_cursor, my_remote_cursor)
                print("Balance has been updated!")
        elif (val == 6):
            card = input("Enter the ID of the card to travel: ")
            my_local_cursor.execute("SELECT * FROM card WHERE card_ID = "+str(card))
            rows = my_local_cursor.fetchall()
            if len(rows) == 0:
                print("Not a valid card. Please try again.")
            else:
                travel_zone = input("Please enter the zone you will be traveling in: ")
                bus_number = input("Enter your bus number: ")
                add_card_action_local_db(my_local_cursor, str(card), -3, travel_zone, bus_number)
                push_to_remote(my_local_cursor, my_remote_cursor)
                print("Successfully tapped on!")
        elif (val == 7):
            print("Goodbye")
            break
        else:
            break

    close_connection(my_local_conn, my_local_cursor)
    close_connection(my_remote_conn, my_remote_cursor)

if __name__ == "__main__":
    main()
