
from time import sleep
import time
import CMPT_MFRC522
import NFC_card
import scan_terminal_menu
import multiprocessing as mp
import db_connect
import status_LEDs
import db_sync
from datetime import datetime


#! GLOBALS TO TOGGLE FOR DEMO VIDEOS
# Transfer_timeout =  7200000 # 2 hours (use this as DEFAULT for production)
# Transfer_timeout =  60000 # 1 min
Transfer_timeout =  20000 # 20 seconds
checking_for_new_scans = True


# Return False if already scanned recently ( < 10s)
# Return True if not in list or scanned longer than 10s ago. 
def check_if_scanned_already(scan_dict, id_num):
    # 10s = 10000 ms
    time_now = time.time_ns()//1_000_000
    
    # clean out old values from the dictionary
    old_keys = []
    if scan_dict:
        for key, value in scan_dict.items():
            if time_now-value > 10000:
                old_keys.append(key)
    for k in old_keys:
        scan_dict.pop(k)

    # Check for id_num in dict. Add it if not in there
    if scan_dict.get(id_num) == None:
        scan_dict.update({id_num:time_now})
        return True # it's a new card being scanned
    else:
        return False # Card has already been  scanned recently



# Returns 0 if successful
# Returns # representing error if the ride is invalid
#   -1 - Unkown error
#    1 - Invalid card status
#    2 - Insufficient funds
#    3 - Card life expired
def check_if_ride_valid(card:NFC_card.physical_nfc_card):


    # Check if card status valid
    if(card.status == 0):
        return 1 # card deactivated

    # check if balance not negative AND no active subscription AND not already scanned on somewhere else and can riding a transfer
    if (card.balance < 0) and (card.subscrip_time < (time.time_ns()//1_000_000)) \
        and (card.ride_exp < (time.time_ns()//1_000_000) ) :
        return 2

    # Check card life remaining
    if card.card_life < (time.time_ns()//1_000_000):
        return 3 # Card expired

    return 0 # All checks passed - card valid to ride


def charge_card_for_valid_ride(card:NFC_card.physical_nfc_card):
    charge_rate = 350
    
    new_action = NFC_card.physical_nfc_card.card_action()
    new_action.timestamp = (time.time_ns()//1_000_000)
    new_action.action = 2
    new_action.zone = 0
    new_action.bus_number = 0
    new_action.verification = 0

    # check if tapped on recently so ride free with transfer. If yes, no additional charge
    if( card.ride_exp > (time.time_ns()//1_000_000) ):
        new_action.new_balance = card.balance
        new_action.balance_change = 0

    # check for active subscription. If yes: no additional charge for ride
    elif(card.subscrip_time > (time.time_ns()//1_000_000)):
        new_action.new_balance = card.balance
        new_action.balance_change = 0

    # charge user for ride and update touch on time
    else:
        card.ride_exp = (time.time_ns()//1_000_000) + Transfer_timeout
        new_action.new_balance = card.balance-charge_rate
        new_action.balance_change = -charge_rate
        card.balance = card.balance - charge_rate

    # Add created action to card
    card.update_oldest_card_action(new_action)
    
    # Sync card action with local DB
    conn, cursor = db_connect.open_db_conn("local")
    # (transaction_ID, card, zone, new_amount, charge, type, time, bus_number, verification)
    transaction_ID = str(card.id_num)+str(new_action.timestamp)
    db_connect.Insert_New_Card_Action(transaction_ID, card.id_num, new_action.zone,\
        new_action.new_balance, new_action.balance_change, new_action.action,\
        new_action.timestamp, new_action.bus_number, new_action.verification, cursor)
    db_connect.update_balance(cursor, card.id_num, card.balance)
    db_connect.close_db_con(conn, cursor)


def save_card_actions_to_local_DB(card:NFC_card.physical_nfc_card):
    #open local connection
    conn, cursor = db_connect.open_db_conn("local")
    # add any new card actions into local DB that aren't already present
    for i in range(12):
        trans_id = str(card.id_num)+str(card.card_actions[i].timestamp) 
        # Transaction already in local DB. Skip.
        if(db_connect.get_single_card_transaction(cursor, trans_id)):
            continue
        # Transaction is new and needs to be added to local DB
        else:
            db_connect.Insert_New_Card_Action(trans_id, card.id_num, card.card_actions[i].zone,\
                card.card_actions[i].new_balance, card.card_actions[i].balance_change, card.card_actions[i].action,\
                card.card_actions[i].timestamp, card.card_actions[i].bus_number, card.card_actions[i].verification, cursor)
    #close the connection
    db_connect.close_db_con(conn, cursor)


def update_card_with_new_online_actions(card:NFC_card.physical_nfc_card):
    #open local connection
    conn, cursor = db_connect.open_db_conn("local")

    # get all card's actions from local DB
    actions = db_connect.get_card_actions(cursor, card.id_num)
    # Check actions list against Transaction types list for anything that needs to be synced from online
    types = db_connect.get_transaction_types(cursor, "online")
    # Sync any online changes found in actions list not already synced.
    online_acts = []
    synced = []
    for act in actions:
        # Add all synced actions to list for tracking
        if act[5] == 4:
            synced.append(act)
        for t in types:
            if t[0] == act[5]:
                # Online action found. Add it to list so we can then make sure it's been synced to card (action type 4)
                online_acts.append(act)
    new = online_acts.copy()
    for found in online_acts:
        for sync in synced:
            if sync[8] == found[8]:
                for x in new:
                    if x[8] == found[8]:
                        new.remove(found)

    # Sync remaining new actions to card
    for remaining in new: 
        sync_action_to_card(cursor, card, remaining)

    db_connect.close_db_con(conn, cursor)

def sync_action_to_card(cursor, card:NFC_card.physical_nfc_card, act):
    """
    --Action obj reference--
       0: transaction_ID
       1: card
       2: zone
       3: new_amount
       4: charge
       5: type
       6: time
       7: bus_number
       8: verification
    """
    output = [
        str(time.time_ns()//1_000_000)+str(card.id_num),\
        card.id_num,\
        0,\
        None,\
        None,\
        4,\
        time.time_ns()//1_000_000,\
        0,\
        act[8]\
        ]

    # Change card balance online
    if act[5] == 5:
        output[3] = card.balance + act[4]
        output[4] = act[4]
        # Get change in balance and apply it to current card balance
        card.balance = card.balance + act[4]

    # Update card status online
    elif act[5] == 6:
        output[3] = card.balance
        output[4] = 0
        # Apply status update
        new_card = db_connect.get_cards(cursor, card.id_num)
        card.status = new_card[0][3]
    # transfer card funds
    elif act[5] == 8:
        output[3] = card.balance + act[4]
        output[4] = act[4]
        # Get change in balance and apply it to current card balance
        card.balance = card.balance + act[4]

    # Add subscription time to card
    elif act[5] == 9:
        output[3] = card.balance
        output[4] = 0
        # Get change in subscription time and apply it to current card time

        try:
            new_sub = db_connect.get_card_subscription(cursor, card.id_num)
            new_sub = int(new_sub[0][2].timestamp()*1000)
        except:
            new_sub = 0 # Subscription was removed and no longer exists in DB
        card.subscrip_time = new_sub

    else:
        print("Action type not added to sync_action_to_card function")
        return

    db_connect.Insert_New_Card_Action(output[0], output[1], output[2], output[3],\
        output[4], output[5], output[6], output[7], output[8], cursor)
    
    #create a sync action to update card with
    sync_act = NFC_card.physical_nfc_card.card_action
    sync_act.timestamp = output[6]
    sync_act.new_balance = output[3]
    sync_act.balance_change = output[4]
    sync_act.action = output[5]
    sync_act.zone = output[2]
    sync_act.bus_number = output[7]
    sync_act.verification = output[8]

    # Update card actions with new sync action
    card.update_oldest_card_action(sync_act)



"""
---- Tap On Logic ---

pull transactions off of card
save any new ones to the local database
if any new remote transactions happened, apply that to the card (from the local database)
    update ALL card variables to make sure status changes, etc, are applied 
add card action to card to show card has been synced with online transaction
    also add that sync up action to the local database 

run logic on card to see if user can ride the bus
    Card still valid (not expired)
    Active subscription for free ride?

If yes, write transaction to the card and let them ride,
    add same card action the the local database

"""

def bus_logic():

    # todo Start card syncing process in separate thread

    kill_read = mp.Value('i', 0)
    t2 = mp.Process(target=scan_terminal_menu.kill_with_input, daemon=True, args=(kill_read, ) )
    t2.start()
        
    sync_enabled = mp.Value('i', 1)
    sync_thread = mp.Process(target=db_sync.databse_bidirectional_sync, daemon=True, args=(15, sync_enabled) )
    sync_thread.start()

    sleep (4) #! /////////////////////////////////////////////
    reader = CMPT_MFRC522.CMPT_MFRC522()
    scan_dict = {}

    while(1):
        # Create new card object for each scan
        card = NFC_card.physical_nfc_card()

        print("\nHold card to scanner to read card info... \n  (press ENTER for main menu)\n", flush=True)
        if kill_read.value:
            sync_enabled.value = 0
            return

        data = reader.read_full_card()
        while data == None:
            data = reader.read_full_card()
            if kill_read.value:
                sync_enabled.value = 0
                return

        print(" ", flush=True) # print space to ensure the buffer was cleared from requested input
        sleep(0.05)
        card.hex_to_datafields(data)

        #? check if already scanned onto this bus in past 5min. If yes, don't need to run transfers.
        new = check_if_scanned_already(scan_dict, card.id_num)

        #? Save new transactions off of card to local DB.
        #? Update card object with any new online transactions
        if(new and checking_for_new_scans):
            save_card_actions_to_local_DB(card)
            update_card_with_new_online_actions(card)

        #? Check for valid ride
        invalid = check_if_ride_valid(card)
        # print(invalid) #! ///////////////////////////////////////////
        if invalid == 0:

            #? Charge card from DB value and write to database
            charge_card_for_valid_ride(card)

            # update card on scanner
            out = NFC_card.physical_nfc_card.data_to_hex_for_output(card)
            data = reader.write_changes(out)
            while data == None:
                data = reader.write_changes(out)
                if kill_read.value:
                    sync_enabled.value = 0
                    return

            # print(card) #! ///////////////////////////////////////////
            print("Status - Success!")
            print("Current balance:", card.balance)
            if(card.subscrip_time > (time.time_ns()//1_000_000)):
                print("Subscription expires:", NFC_card.epoch_to_human_time(str(card.subscrip_time))[:-7]) #! //////////////////////MIGHT Need human readable time here
            status_LEDs.flash_led("green")

        else: # card is invalid and can't ride
            # update card on scanner
            out = NFC_card.physical_nfc_card.data_to_hex_for_output(card)
            data = reader.write_changes(out)
            while data == None:
                data = reader.write_changes(out)
                if kill_read.value:
                    sync_enabled.value = 0
                    return


            # handle error for invalid reasoning
            #    1 - Invalid card status
            #    2 - Insufficient funds
            #    3 - Card life expired
            if(invalid == 1):
                print("Error - Card inactive!\nYou must activate card before scanning.\n")
            if(invalid == 2):
                print("Error - Insufficient funds!\nPlease purchase funds or subscription before scanning.\n")
            if(invalid == 3):
                print("Error - This card has expired!\nPlease purchase a new card before scanning.\n")
            status_LEDs.flash_led("red")



        #todo visual screen output here if I end up adding it

        print("\n-------------\n")

        sleep(1)


if __name__ == '__main__':
    pass

    out = 5
    i = 2
    while i < 5:
        print(out)
        i += 1
        j = "ok"
    print(j)