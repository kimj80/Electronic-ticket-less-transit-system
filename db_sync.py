

"""
Have a separate pull freq and push freq. Each should run independent of one another


--- Sync Logic ---
If online actions have happened then we need to pull the full details to apply to cards (card status, card sub, etc.)
Do a full sync when first starting up so the bus is totally synced with remote DB.

Sliding windows in memory
    pull_window_time_size = sync_freq + time_buffer(20s) + failed_sync_time_add
    sync_freq = 60s
    variable pull rates +- rand(5s)

Pull Transactions from online database

Push all local transactions up to remote DB


Remove cards that aren't in the remote database anymore.


__________________

Pulls down remote actions
sends up everything



"""

from datetime import datetime
import time
import db_connect


def sync_card(remote_cursor, local_cursor):
    remote = db_connect.get_cards(remote_cursor)
    local = db_connect.get_cards(local_cursor)

    for rem in remote:
        if rem not in local:
            # drop local Card to overwrite if card is different
            db_connect.delete_card(local_cursor, rem[0])
            # add remote card to local
            db_connect.Insert_New_Card(*rem, local_cursor)
    print("sync_card complete")
    return

def sync_card_subscription(remote_cursor, local_cursor):
    remote = db_connect.get_card_subscription(remote_cursor)
    local = db_connect.get_card_subscription(local_cursor)

    for rem in remote:
        if rem not in local:
            # drop local sub to overwrite if different
            db_connect.delete_card_subscription(local_cursor, rem[0])
            # add remote sub to local
            db_connect.Insert_New_Card_Subscription(*rem, local_cursor)
    print("sync_card_subscription complete")
    return

def sync_subscription(remote_cursor, local_cursor):
    remote = db_connect.get_subscription(remote_cursor)
    local = db_connect.get_subscription(local_cursor)

    for rem in remote:
        if rem not in local:
            # drop local sub to overwrite if different
            db_connect.delete_subscription(local_cursor, rem[0])
            # add remote sub to local
            db_connect.Insert_New_Subscription(*rem, local_cursor)
    print("sync_subscription complete")
    return

def sync_subscription_zone(remote_cursor, local_cursor):
    remote = db_connect.get_subscription_zone(remote_cursor)
    local = db_connect.get_subscription_zone(local_cursor)

    for rem in remote:
        if rem not in local:
            # drop local sub_zone to overwrite if different
            db_connect.delete_subscription_zone(local_cursor, rem[0])
            # add remote sub_zone to local
            db_connect.Insert_New_Subscription_Zone(*rem, local_cursor)
    print("sync_subscription_zone complete")
    return

def sync_travel_zone(remote_cursor, local_cursor):
    remote = db_connect.get_travel_zone(remote_cursor)
    local = db_connect.get_travel_zone(local_cursor)

    for rem in remote:
        if rem not in local:
            # drop local travel_zone to overwrite if different
            db_connect.delete_travel_zone(local_cursor, rem[0])
            # add remote travel_zone to local
            db_connect.Insert_New_Travel_Zone(*rem, local_cursor)
    print("sync_travel_zone complete")
    return

def sync_card_action(remote_cursor, local_cursor):
    remote = db_connect.get_card_actions(remote_cursor)
    local = db_connect.get_card_actions(local_cursor)

    for rem in remote:
        if rem not in local:
            # drop local Card_Action to overwrite if different
            db_connect.delete_card_actions(local_cursor, rem[0])
            # add remote Card_Action to local
            db_connect.Insert_New_Card_Action(*rem, local_cursor)
    print("sync_card_action complete")
    return

def sync_transaction_types(remote_cursor, local_cursor):
    remote = db_connect.get_transaction_types(remote_cursor)
    local = db_connect.get_transaction_types(local_cursor)

    for rem in remote:
        if rem not in local:
            # drop local Card_Action to overwrite if different
            db_connect.delete_transaction_types(local_cursor, rem[0])
            # add remote Card_Action to local
            db_connect.Insert_New_transaction_types(*rem, local_cursor)
    print("sync_transaction_types complete")
    return

# Full sync of local database from remote
def full_local_db_update(sync_frequency_s):
    while(1):
        try:
            print("Starting Sync on Boot Sequence")
            local_conn, local_cursor = db_connect.open_db_conn("local")
            remote_conn, remote_cursor = db_connect.open_db_conn("remote")

            local_cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
            remote_cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

            sync_transaction_types(remote_cursor, local_cursor)
            sync_card(remote_cursor, local_cursor)
            sync_travel_zone(remote_cursor, local_cursor)
            sync_subscription(remote_cursor, local_cursor)
            sync_card_subscription(remote_cursor, local_cursor)
            sync_subscription_zone(remote_cursor, local_cursor)
            sync_card_action(remote_cursor, local_cursor)

            local_cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
            remote_cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

            db_connect.close_db_con(remote_conn, remote_cursor)
            db_connect.close_db_con(local_conn, local_cursor)
            print("SUCCESS! Sync on Boot Sequence Complete")
            return True
        except KeyboardInterrupt as k:
            quit()
        except Exception as e:
            print(e)
            print("Full sync failed. Will retry in {} seconds".format(sync_frequency_s))
            time.sleep(sync_frequency_s)

def get_online_actions(cursor, timeframe):
    timeframe = datetime.fromtimestamp(timeframe / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f")
    val = (timeframe, )
    sql = "SELECT * FROM card_action WHERE \
            (type = 5 OR \
            type = 6 OR \
            type = 8 OR \
            type = 9) AND \
            time > %s"
    cursor.execute(sql, val)
    rows = cursor.fetchall()
    return rows

def get_local_actions(cursor, timeframe):
    
    timeframe = datetime.fromtimestamp(timeframe / 1e3).strftime("%Y-%m-%d %H:%M:%S.%f")
    val = (timeframe, )
    sql = "SELECT * FROM card_action WHERE time > %s"
    cursor.execute(sql, val)
    rows = cursor.fetchall()
    return rows

def send_action(transaction_ID, card, zone, new_amount, charge, type, time, bus_number, verification, cursor):
    sql = "INSERT INTO card_action VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = (transaction_ID, card, zone, new_amount, charge, type, time, bus_number, verification)
    cursor.execute(sql, val)

def perform_db_sync (activity_window):
    try:
        # open local and remote DB connections
        local_conn, local_cursor = db_connect.open_db_conn("local")
        remote_conn, remote_cursor = db_connect.open_db_conn("remote")

        # Pull down all "Online" transactions from in window
        online_actions = get_online_actions(remote_cursor, activity_window)
        # Get all local transactions from in window
        local_actions = get_local_actions(local_cursor, activity_window)

        # Send all local actions up to remote DB
        if local_actions:
            for act_loc in local_actions:
                # if action involved charge: update the online card balance too
                if act_loc[4] != 0:
                    local_card = db_connect.get_cards(local_cursor, act_loc[1])
                    db_connect.update_balance(remote_cursor, act_loc[1], local_card[0][4])

                try:
                    send_action(*act_loc, remote_cursor)
                    remote_conn.commit()
                except Exception as e:
                    # print("Error while sending local actions up to remote DB")
                    # print(e)
                    pass

        # Apply online actions to local db
        if online_actions:
            for act_rem in online_actions:

                # 5 -    Add balance to card online :       Online
                # 6 -    Update card status online :        Online
                # 8 -    transfer card funds either direction :    Online
                # 9 -    Add or remove subscription time to card : Online

                # if balance, status, or transfer: get remote card too
                if act_rem[5] == 5 or act_rem[5] == 6 or act_rem[5] == 8:
                    rem_card = db_connect.get_cards(local_cursor, act_rem[1])
                    local_cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
                    db_connect.delete_card(local_cursor, act_rem[1])
                    db_connect.Insert_New_Card(*(rem_card[0]), local_cursor)
                    local_cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
                # if status: get card
                #todo if add or remove card sub: get card subs from online
                if act_rem[5] == 9:
                    db_connect.delete_card_subscription(local_cursor, act_rem[1])
                    new_sub = db_connect.get_card_subscription(remote_cursor, act_rem[1])
                    if new_sub:
                        db_connect.Insert_New_Card_Subscription(*(new_sub[0]), local_cursor)
                    else:
                        pass # Subscription was removed

                try:
                    send_action(*act_rem, local_cursor)
                    local_conn.commit()
                except Exception as e:
                    # print("Error while sending remote actions to local DB")
                    # print(e)
                    pass

        # Close connections
        db_connect.close_db_con(local_conn, local_cursor)
        db_connect.close_db_con(remote_conn, remote_cursor)
        # print('Ran sync cycle') #! ///////////////////////////
    except KeyboardInterrupt as k:
        quit()
    except Exception as e:
        print("Problem in the sync cycle")
        print(e)


# returns time in MS
def t_ms():
    return time.time_ns()//1_000_000

def databse_bidirectional_sync(sync_frequency_s, sync_enabled):
    # Database does a working sync every "freqency" seconds
    freq = sync_frequency_s * 1000 # Convert s to ms
    
    # Include a time buffer in the window to ensure nothing is missed when syncing transactions
    sync_time_buffer = 20 * 1000 # 20 second buffer in ms

    # Make sure the local database is fully up to date when starting sync for the first time
    sync_start = t_ms()
    full_local_db_update(sync_frequency_s)
    sync_end = t_ms()
    # infinite sync loop until thread is killed
    while(sync_enabled.value == 1):

        time.sleep(sync_frequency_s)
        if(sync_enabled.value == 0):
            break

        overhead = sync_end - sync_start

        sync_start = t_ms()

        activity_window = sync_start - freq - sync_time_buffer - overhead

        perform_db_sync(activity_window)

        sync_end = t_ms()

    print("shutting down sync thread")


if __name__ == "__main__":

    databse_bidirectional_sync(10)