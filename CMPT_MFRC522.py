
from time import sleep
import mfrc522


class CMPT_MFRC522:

    READER = None

    KEY = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]
    SAFE_BLOCKS_FOR_WRITING = [1,2,4,5,6,8,9,10,12,13,14,16,17,18,20,21,22,24,25,26,\
        28,29,30,32,33,34,36,37,38,40,41,42,44,45,46,48,49,50,52,53,54,56,57,58,60,61,62]

    def __init__(self):
        self.READER = mfrc522.MFRC522()

    def read(self):
        id, text = self.read_no_block()
        while not id:
            id, text = self.read_no_block()
        return id, text

    def read_id(self):
        id = self.read_id_no_block()
        while not id:
            id = self.read_id_no_block()
        return id

    def read_id_no_block(self):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        return self.uid_to_num(uid)

    def read_no_block(self):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None, None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None, None
        id = self.uid_to_num(uid)
        self.READER.MFRC522_SelectTag(uid)
        status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, 19, self.KEY, uid)
        data = []
        text_read = ''
        if status == self.READER.MI_OK:
            for block_num in self.BLOCK_ADDRS:
                block = self.READER.MFRC522_Read(block_num)
                if block:
                    data += block
                if data:
                    text_read = ''.join(chr(i) for i in data)
        self.READER.MFRC522_StopCrypto1()
        return id, text_read

    def write(self, text):
        id, text_in = self.write_no_block(text)
        while not id:
            id, text_in = self.write_no_block(text)
        return id, text_in

    def write_no_block(self, text):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None, None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None, None
        id = self.uid_to_num(uid)
        self.READER.MFRC522_SelectTag(uid)
        status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, 19, self.KEY, uid)
        self.READER.MFRC522_Read(19)
        if status == self.READER.MI_OK:
            data = bytearray()
            data.extend(bytearray(text.ljust(len(self.BLOCK_ADDRS) * 16).encode('ascii')))
            i = 0
            for block_num in self.BLOCK_ADDRS:
                self.READER.MFRC522_Write(block_num, data[(i*16):(i+1)*16])
                i += 1
        self.READER.MFRC522_StopCrypto1()
        return id, text[0:(len(self.BLOCK_ADDRS) * 16)]

    def write_changes(self, changes):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        self.READER.MFRC522_SelectTag(uid)

        card_id = []
        for block_num in range(64):
            status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, block_num, self.KEY, uid)
            if status == self.READER.MI_OK:
                existing = self.READER.MFRC522_Read(block_num)

                if (existing != changes[block_num]) and (block_num in self.SAFE_BLOCKS_FOR_WRITING):
                    self.READER.MFRC522_Write(block_num, changes[block_num][0:16])

        self.READER.MFRC522_StopCrypto1()
        return True

    def zero_out_card(self):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        self.READER.MFRC522_SelectTag(uid)

        # Read existing card ID before it gets wiped
        card_id = []
        for block_num in [1,2]:
            status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, block_num, self.KEY, uid)
            if status == self.READER.MI_OK:
                block = self.READER.MFRC522_Read(block_num)
                if block:
                    for x in range(len(block)):
                        card_id.append(hex(block[x])[2:])
                else:
                    return None
        id = ''
        for i in range(32):
            id  += card_id[i]
        # id_num = int(id, 16)

        blank = [[int("0",16)]*16]*64
        for block_num in range(64):
            status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, block_num, self.KEY, uid)
            if status == self.READER.MI_OK:
                if block_num in self.SAFE_BLOCKS_FOR_WRITING:
                    self.READER.MFRC522_Write(block_num, blank[block_num][0:16])

        self.READER.MFRC522_StopCrypto1()
        return int(id, 16)


    def uid_to_num(self, uid):
        n = 0
        for i in range(0, 5):
            n = n * 256 + uid[i]
        return n

    def dump_card(self):
        temp_level = self.READER.logger.getEffectiveLevel()
        self.READER.logger.setLevel('DEBUG')
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        id = self.uid_to_num(uid)
        self.READER.MFRC522_SelectTag(uid)
        self.READER.MFRC522_DumpClassic1K(self.KEY, uid)
        self.READER.logger.setLevel(temp_level)

    def read_full_card(self):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        self.READER.MFRC522_SelectTag(uid)

        data = []
        for block_num in range(64):
            status = self.READER.MFRC522_Auth(self.READER.PICC_AUTHENT1A, block_num, self.KEY, uid)
            if status == self.READER.MI_OK:
                block = self.READER.MFRC522_Read(block_num)
                if block:
                    data.append(block)
                else:
                    return None
        self.READER.MFRC522_StopCrypto1()
        return data # return text_read in list form


if __name__ == '__main__':

    reader = CMPT_MFRC522()

    # reader.dump_card()
    # print(reader.read_id_no_block())
    data = reader.read_full_card()

    print(data)
    print("\n-------------------------------------------------\n")
    for i in range(64):
        print("Block ", i, " - ", sep="", end="")
        print(bytes(data[i]))

        # for j in data[i]:
        #     print( bytes((j)).hex() )

    print("\n-------------------------------------------------\n")
    for i in range(64):
        print("Block ", i, " - ", sep="", end="")
        for j in range(0,16,2):
            print(hex(data[i][j])[2:].zfill(2).upper(), end=" ")
            print(hex(data[i][j+1])[2:].zfill(2).upper(), end=" ")
        print()

    print("\n")

    print("--- Hex strings ---")
    buf = [[]]*64
    for i in range(64):
        string = ''
        for j in range(0,16,2):
            string += hex(data[i][j])[2:].zfill(2).upper()
            string += hex(data[i][j+1])[2:].zfill(2).upper()
        buf[i] = string
    print(buf)

    byte_array = bytearray.fromhex(buf[0])
    print("---bytes---\n",byte_array)
    print("again", byte_array.hex())
    print("len:", len(byte_array))

    print(type(data))
    print(len(data))
    print(len(data[0]))

    reader = CMPT_MFRC522()
    print("---Changes---")
    reader.write_changes(data)
