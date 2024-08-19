

from ctypes.wintypes import SERVICE_STATUS_HANDLE
import os
import secrets
import sys
import time
import CMPT_MFRC522
import NFC_card
import scan_terminal_menu
import status_LEDs

import multiprocessing as mp
from time import sleep
import db_connect

def zero_card():
    kill_read = mp.Value('i', 0)
    t2 = mp.Process(target=scan_terminal_menu.kill_with_input, daemon=True, args=(kill_read, ) )
    t2.start()

    reader = CMPT_MFRC522.CMPT_MFRC522() 
    print("\nTap card to scanner to zero out data... \n  (press ENTER for menu)\n")
    old_id = reader.zero_out_card()
    while old_id == None:
        old_id = reader.zero_out_card()
        if kill_read.value:
            return

    #if t2 running: kill it. (means card was scanned and user didn't hit enter)
    if t2.is_alive():
        t2.terminate()
    print(" ", end= '', flush=True) # print space to ensure the buffer was cleared from requested input

    #todo - test card removal from DB
    conn_L, cursor_L = db_connect.open_db_conn("local")
    conn_R, cursor_R = db_connect.open_db_conn("remote")
    # Check connection established
    if(not conn_L or not conn_R):
        return # DB error is printed

    db_connect.delete_card(cursor_L, old_id)
    db_connect.delete_card(cursor_R, old_id)

    db_connect.close_db_con(conn_L, cursor_L)
    db_connect.close_db_con(conn_R, cursor_R)

    print("Card wipe successful\n")
    sleep(1.5)
    return

def print_scanned_card():
    kill_read = mp.Value('i', 0)
    t2 = mp.Process(target=scan_terminal_menu.kill_with_input, daemon=True, args=(kill_read, ) )
    t2.start()

    reader = CMPT_MFRC522.CMPT_MFRC522() 
    card = NFC_card.physical_nfc_card()

    print("\nHold card to scanner to read card info... \n  (press ENTER for main menu)\n", flush=True)
    data = reader.read_full_card()

    while data == None:
        data = reader.read_full_card()
        if kill_read.value:
            return

    #if t2 running: kill it. (means card was scanned and user didn't hit enter)
    if t2.is_alive():
        t2.terminate()
    print(" ", flush=True) # print space to ensure the buffer was cleared from requested input

    card.hex_to_datafields(data)
    print(card)
    return

def init_new_card():
    kill_read = mp.Value('i', 0)
    t2 = mp.Process(target=scan_terminal_menu.kill_with_input, daemon=True, args=(kill_read, ) )
    t2.start()

    reader = CMPT_MFRC522.CMPT_MFRC522() 
    card = NFC_card.physical_nfc_card()

    print("\nTap card to scanner to format new card... \n  (press ENTER for main menu)\n")

    # Get the card manufacturer id
    data = reader.read_full_card()
    while data == None:
        data = reader.read_full_card()
        if kill_read.value:
            return
    card.hex_to_datafields(data)

    # Now we can set values to new card 
    card.init_new_card()

    out = NFC_card.physical_nfc_card.data_to_hex_for_output(card)

    data = reader.write_changes(out)
    while data == None:
        data = reader.write_changes(out)
        if kill_read.value:
            return

    print(card) #! //////////////////////////////////////////////////////////////////////////////////////////////////

    status_LEDs.flash_led("green")

    #todo test insert card operation functionality
    conn, cursor = db_connect.open_db_conn("remote")
    db_connect.Insert_New_Card(card.id_num, card.man_id, None, card.status, card.balance, card.card_life, cursor)
    db_connect.close_db_con(conn, cursor)

    conn, cursor = db_connect.open_db_conn("remote")
    transaction_id = str( str(card.card_actions[0].timestamp) + str(card.id_num) )
    db_connect.Insert_New_Card_Action(transaction_id, card.id_num, card.card_actions[0].zone, card.card_actions[0].new_balance, \
        card.card_actions[0].balance_change, card.card_actions[0].action, card.card_actions[0].timestamp, \
        card.card_actions[0].bus_number, card.card_actions[0].verification, cursor)
    db_connect.close_db_con(conn, cursor)

    conn, cursor = db_connect.open_db_conn("local")
    db_connect.Insert_New_Card(card.id_num, card.man_id, None, card.status, card.balance, card.card_life, cursor)
    db_connect.close_db_con(conn, cursor)

    conn, cursor = db_connect.open_db_conn("local")
    transaction_id = str( str(card.card_actions[0].timestamp) + str(card.id_num) )
    db_connect.Insert_New_Card_Action(transaction_id, card.id_num, card.card_actions[0].zone, card.card_actions[0].new_balance, \
        card.card_actions[0].balance_change, card.card_actions[0].action, card.card_actions[0].timestamp, \
        card.card_actions[0].bus_number, card.card_actions[0].verification, cursor)
    db_connect.close_db_con(conn, cursor)

    #if t2 running: kill it. (means card was scanned and user didn't hit enter)
    if t2.is_alive():
        t2.terminate()
    print(" ", flush=True) # print space to ensure the buffer was cleared from requested input

    print("New card successfully initialized!")
    sleep(1.5)
    return

def get_card_balance(balance):
    sys.stdin = os.fdopen(scan_terminal_menu.std_in)

    new_balance = input("\nEnter card balance change in pennies between -99999 to 99999\n"+\
                        " or enter'x' to cancel. New Balance: ")
    try:
        if new_balance == 'x' or new_balance == 'X':
            print("\nOperaton canceled. No changes made.")
            sleep(1.5)
            balance.value = 777777
            return
        new_balance = int(new_balance)
        assert (-99999 <= new_balance <= 99999)
    except:
        new_balance = None

    while(new_balance==None):
        try:
            new_balance = input("\nInvalid Number. Enter 'x' to cancel.\nEnter balance change in pennies between -99999 to 99999: ")
            if new_balance == 'x':
                print("\nOperaton canceled. No changes made.")
                sleep(1.5)
                balance.value = 777777
                return
            new_balance = int(new_balance)
            assert (-99999 <= new_balance <= 99999)
        except:
            new_balance = None

    # A good balance was entered
    balance.value = new_balance
    return

def change_card():
    balance = mp.Value('i', 0)
    t = mp.Process(target=get_card_balance, daemon=True, args=(balance, ) )
    t.start()
    t.join()

    # If special int 777777 (out of range for normal return) is given then user input x to cancel scan.
    if balance.value == 777777:
        return

    # Start Reader
    reader = CMPT_MFRC522.CMPT_MFRC522()
    #create card object to save card into
    card = NFC_card.physical_nfc_card()

    # write updated object data to physical card
    print("\nTap card to scanner to update card... \n  (press ENTER for main menu)")
    kill_read = mp.Value('i', 0)
    t2 = mp.Process(target=scan_terminal_menu.kill_with_input, daemon=True, args=(kill_read, ) )
    t2.start()

    # read card first to get all info on card
    data_in = reader.read_full_card()
    while data_in == None:
        data_in = reader.read_full_card()
        if kill_read.value:
            return
    
    # Save read-in card data to change
    card.hex_to_datafields(data_in)

    # create new card action for update balance
    act = NFC_card.physical_nfc_card.card_action()
    act.timestamp = time.time_ns() // 1_000_000
    act.new_balance = card.balance + balance.value
    act.balance_change = balance.value
    act.action = 4
    act.zone = 0
    act.bus_number = 0
    act.verification = secrets.randbelow(65536)

    # Update card object with balance and action
    card.update_oldest_card_action(act)
    card.balance = card.balance + balance.value
    out = NFC_card.physical_nfc_card.data_to_hex_for_output(card)

    # Write changes to card
    data = reader.write_changes(out)
    while data == None:
        data = reader.write_changes(out)
        if kill_read.value:
            return

    #if t2 running: kill it. (means card was scanned and user didn't hit enter)
    if t2.is_alive():
        t2.terminate()
    print(" ", flush=True) # print space to ensure the buffer was cleared from requested input

    # TODO Lots of testing here!
    # --- add changes to the card in the remote and local database
    # REMOTE DB
    conn, cursor = db_connect.open_db_conn("remote")
    # Add Card action
    transaction_ID = str(act.timestamp) + str(card.id_num) 
    db_connect.Insert_New_Card_Action(transaction_ID, card.id_num, act.zone, act.new_balance, act.balance_change,\
        act.action, act.timestamp, act.bus_number, act.verification, cursor)
    # Add Card's update
    db_connect.update_balance(cursor, card.id_num, card.balance)
    db_connect.close_db_con(conn, cursor)
    
    # LOCAL DB
    conn, cursor = db_connect.open_db_conn("local")
    # Add Card action
    transaction_ID = str(act.timestamp) + str(card.id_num) 
    db_connect.Insert_New_Card_Action(transaction_ID, card.id_num, act.zone, act.new_balance, act.balance_change,\
        act.action, act.timestamp, act.bus_number, act.verification, cursor)
    # Add Card's update
    db_connect.update_balance(cursor, card.id_num, card.balance)
    db_connect.close_db_con(conn, cursor)
    
    status_LEDs.flash_led("green")

    print("\nCard updated\n")
    sleep(1.5)
    return


def kiosk():
    opt = -1
    while(opt != 0):
        try:
            opt = int(input(
                "\n--- Kiosk Menu ---\n"
                "Select operation\n"+
                "  1 -Erase card (zero out)\n"+
                "  2 -Initialize new card\n"+
                "  3 -Print scanned card\n"+
                "  4 -Add balance to card\n"+
                "  0 -Back to Main Menu\n"+
                "Selection: "))
        except ValueError as e:
            opt = -1
        while not (0 <= opt <=4):
            try:
                opt = int(input("Invalid. Try again: "))
            except ValueError as e:
                opt = -1

        # Return to main menu
        if opt == 0:
            return

        # Zero out card
        elif opt == 1:
            t1 = mp.Process(target=zero_card)
            t1.start()
            t1.join()

        # Initialize new card
        elif opt == 2:
            t1 = mp.Process(target=init_new_card)
            t1.start()
            t1.join()

        # Print scanned card
        elif opt == 3:
            t1 = mp.Process(target=print_scanned_card)
            t1.start()
            t1.join()

        # Modify values on card
        elif opt == 4:
            
            """
            I'm not ready for this much work... go for it if you dare but I'm waiting to 
            fill out the rest of number 4 here until after the demo on 2022-02-15
            For now it can do balance. We should add some others later into the change_card() function
            """
            t2 = mp.Process(target=change_card)
            t2.start()
            t2.join()



