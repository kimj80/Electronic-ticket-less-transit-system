

import multiprocessing as mp
from time import sleep

import CMPT_MFRC522
import NFC_card

def do_stuff():
    
    reader = CMPT_MFRC522.CMPT_MFRC522() 
    card = NFC_card.physical_nfc_card()
    
    data = reader.read_full_card()
    
    print("before while:", data, flush=True)

    while data == None:
        data = reader.read_full_card()
        print(".", end="", flush=True)

    card.hex_to_datafields(data)
    print(card)

if __name__ == "__main__":

    t2 = mp.Process(target=do_stuff)
    t2.start()


    sleep(1)
    input("INPUT:")
    
    print()
    print("Done")