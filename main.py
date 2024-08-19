
import CMPT_MFRC522
import NFC_card
import scan_terminal_menu
import time
import status_LEDs



def examples_for_how_to_use_NFC_card_objects_AND_Read_write_ops():
    print("\n######################### Start ##################################\n")

    print("*******Straight from card before any changes*******")
    reader = CMPT_MFRC522.CMPT_MFRC522()
    print(reader.read_full_card())


    print("*******New code object (no read)*******")
    a = NFC_card.physical_nfc_card()
    print(a)
    
    print("*******Old data from card*******")
    reader = CMPT_MFRC522.CMPT_MFRC522()
    a.hex_to_datafields(reader.read_full_card())
    print(a)

    print("*******Card init function*******")
    a.init_new_card()
    print(a)

    print("*******New changes written*******")
    reader = CMPT_MFRC522.CMPT_MFRC522()
    reader.write_changes(a.data_to_hex_for_output())
    print(a)

    print("*******Straight from card*******")
    reader = CMPT_MFRC522.CMPT_MFRC522()
    print(reader.read_full_card())

    print("*******New B card read in*******")
    reader = CMPT_MFRC522.CMPT_MFRC522()
    b = NFC_card.physical_nfc_card()
    b.hex_to_datafields(reader.read_full_card())
    print(b)


    print("*******Single changes made to B card read in*******")
    
    reader = CMPT_MFRC522.CMPT_MFRC522()
    b.hex_to_datafields(reader.read_full_card())

    #### Changes ####
    b.id_num = int(99999999999999999999999999999999999999999999999999999999999999999999999999999)
    b.status = 5
    b.fare_type = 5
    b.balance = 5555
    b.touch_status = 5
    # b.ride_exp = time.time_ns() // 1_000_000
    b.active_zones = 555
    b.subscrip_time = 5
    b.card_life = time.time_ns() // 1_000_000
    b.subscrip_zones = 4
    # for v in range(12):
    for v in range(5):
        b.card_actions[v].timestamp = time.time_ns() // 1_000_000
        b.card_actions[v].new_balance = 555+v
        b.card_actions[v].balance_change = -55+v
        b.card_actions[v].action = 55+v
        b.card_actions[v].zone = 55+v
        b.card_actions[v].bus_number = 555+v

    reader = CMPT_MFRC522.CMPT_MFRC522()
    reader.write_changes(b.data_to_hex_for_output())

    reader = CMPT_MFRC522.CMPT_MFRC522()
    b.hex_to_datafields(reader.read_full_card())
    print(b)

if __name__ == '__main__':

    print("Hello world!")

    # examples_for_how_to_use_NFC_card_objects_AND_Read_write_ops()
    
    status_LEDs.setup_LEDs()

    scan_terminal_menu.terminal_interface()
