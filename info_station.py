
import CMPT_MFRC522
import NFC_card
import scan_terminal_menu

from time import sleep
import multiprocessing as mp

def info_station():
    while(1):
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

        print(card) #todo delete this print and replace with something cleaner for an info terminal output.

        sleep(1)
        # Loop to keep scanning

if __name__ == '__main__':
    pass

