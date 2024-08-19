

import os
import sys
from threading import local
from time import sleep
import RPi.GPIO as GPIO
from termios import tcflush, TCIOFLUSH

import bus_logic
import info_station
import kiosk
import db_connect
import db_create
import db_sync

# TODO - Delete these import once everything is working proper
import local_database_connection
import Local_Remote_Communication


# --- Globals ---
std_in = 0

def kill_with_input(kill_read):
    global std_in
    sys.stdin = os.fdopen(std_in)
    # sys.stdout.flush
    tcflush(sys.stdin, TCIOFLUSH)

    I_LOVE_CMPT496 = input("")
    kill_read.value = 1
    return

def terminal_interface():

    # Need to get standard in to pass to child processes
    global std_in
    std_in = sys.stdin.fileno()

    while(1):
        GPIO.setwarnings(False) # Disable GPIO warnings in terminal
        terminal_type = -1
        try:
            terminal_type = int(input(
                "\n--- Main Menu ---\n"
                "Select terminal purpose\n"+
                "  1 -Bus scanner (read/write)\n"+
                "  2 -Info terminal (read only:card stats)\n"+
                "  3 -kiosk (read/write/init/update\n"+
                "  4 -Sync local database with remote\n"+
                "  5 -Show local database\n"+
                "  6 -Show remote database\n"+
                "  0 -Exit\n"+
                "Selection: "))
        except ValueError as e:
            terminal_type = -1
        while not (0 <= terminal_type <=6):
            try:
                terminal_type = int(input("Invalid. Try again: "))
            except ValueError as e:
                terminal_type = -1
        # 0 -Exit
        if terminal_type == 0:
            GPIO.cleanup() # Terminate connection to scanner
            exit()
        # 1 -Bus scanner (read/write)
        elif terminal_type == 1:
            bus_logic.bus_logic()
        # 2 -Info terminal (read only:card stats)
        elif terminal_type == 2:
            info_station.info_station()
        # 3 -kiosk (read/write/init/update
        elif terminal_type == 3:
            kiosk.kiosk()
        # 4 -Sync local database with remote
        elif terminal_type == 4:
            pass
            #TODO configure syncing menu

        # 5 -Show local database
        elif terminal_type == 5:

            conn, cursor = db_connect.open_db_conn("local")
            print("----- Local Cards -----")
            for c in db_connect.get_cards(cursor):
                print(c)
            print()
            print("\n----- Local Actions -----")
            for a in db_connect.get_card_actions(cursor):
                print(a)
            db_connect.close_db_con(conn,cursor)

        # 6 -Show remote database
        elif terminal_type == 6:
            conn, cursor = db_connect.open_db_conn("remote")
            print("----- Remote Cards -----")
            for c in db_connect.get_cards(cursor):
                print(c)
            print()
            print("\n----- Remote Actions -----")
            for a in db_connect.get_card_actions(cursor):
                print(a)
            db_connect.close_db_con(conn,cursor)


if __name__ == "__main__":

    terminal_interface()



