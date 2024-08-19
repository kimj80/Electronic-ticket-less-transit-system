


from dataclasses import dataclass
import datetime
import secrets
import time

class physical_nfc_card:

    def __init__(self):
        #Card manufacturer ID - Cannot be written to. hard coded in card
        self.man_id = None

        # Card ID 16 byte random hex code - Generated when a new card is created using init_new_card()
        self.id_num = None

        # Card Status
        # 1 byte = values from 0-255
        #   0 - Deactivated
        #   1 - Active
        self.status = None

        # Fare type
        # 1 byte = values from 0-255
        #   0 - Golden Ticket (Free)
        #   1 - Normal Use
        #   2 - Student
        #   3 - Military
        self.fare_type = None

        # Card balance
        # 1 byte for sign: + or -
        # 3 bytes for unsigned int: largest number is 0xFFFFFF or 16777215
        self.balance = None

        # Expiry time of current 2-hour fare product (if touched on)
        self.ride_exp = None

        # Active travel zones (if touched on)
        self.active_zones = None

        # Pass length (if one exists) given in expiry time format Milliseconds
        # Ex. today is Jan 1. Card sub time of 1 week would be TODAY() in ms + 
        self.subscrip_time = None

        # Myki pass expiry date (if one exists)
        self.card_life = None

        # Myki pass travel zones (if one exists)
        self.subscrip_zones = None

        # Last 12 card actions - List of sub-classes.
        self.card_actions = []
        for i in range(12):
            self.card_actions.append(self.card_action())

    @dataclass
    class card_action:

        def __init__(self):
            # Date/time in ms when action ocurred
            self.timestamp = None
            # New balance AFTER action change applied. Tap on for a new ride(3.50), with a starting balance of $11.50, would show $8.00.
            self.new_balance = None
            # Change in balance. ($20 added to a card balance of $6.25 would show +20 and NOT +26.25)
            self.balance_change = None
            # Action performed
            self.action = None
            # Zone ID of action
            self.zone = None
            # Bus number if applicable
            self.bus_number = None
            # Verification number used to check online transactions have been pushed to local card
            self.verification = None

        def __repr__(self):
            buf = "" +\
                "Time: {}\n".format(epoch_to_human_time(self.timestamp)) +\
                "New balance: {}\n".format(self.new_balance) +\
                "Balance change: {}\n".format(self.balance_change) +\
                "Action: {}\n".format(self.action) +\
                "Zone: {}\n".format(self.zone) +\
                "Bus number: {}\n".format(self.bus_number) +\
                "Verification #: {}".format(self.verification)
            return buf

        # Prints with tabs at front for better formatting when printing the whole cards details
        def print_with_tabs(self):
            buf = "" +\
                "  Time: {}  ".format(epoch_to_human_time(self.timestamp)) +\
                "New $: {}  ".format(self.new_balance) +\
                "$ change: {}  ".format(self.balance_change) +\
                "Action: {}  ".format(self.action) +\
                "Zone: {}  ".format(self.zone) +\
                "Bus#: {}  ".format(self.bus_number) +\
                "Verification #: {}  ".format(self.verification)
            return buf

    def __repr__(self):
        string = "---------- NFC CARD ----------\n" +\
            "Manufacturer ID: {}\n".format(self.man_id) +\
            "Card ID: {}\n".format(self.id_num) +\
            "Card status: {}\n".format(self.status) +\
            "Fare type: {}\n".format(self.fare_type) +\
            "Card Balance: {}\n".format(self.balance) +\
            "Ride expiry time: {}\n".format(epoch_to_human_time(self.ride_exp)) +\
            "Active Zones: {}\n".format(self.active_zones) +\
            "Subscription time remaining: {}\n".format(epoch_to_human_time(self.subscrip_time)) +\
            "Card life remaining: {}\n".format(epoch_to_human_time(self.card_life)) +\
            "Subscription zones: {}\n".format(self.subscrip_zones) +\
            " ---- Card actions ----\n"
        for i in range(len(self.card_actions)):
            string = string + " -Action {}:".format(i)
            string = string + self.card_actions[i].print_with_tabs()
            string = string + "\n"
        return string


    # OUTPUT - write to card
    def data_to_hex_for_output(self):
        # Physical card layout with 64 blocks of 16 bytes each. 
        buf = [format(0,'02X')*16]*64

        # 1-2
        if self.id_num != None:
            buf[1] = format(self.id_num, '064X')[:32]
            buf[2] = format(self.id_num, '064X')[32:64]
        
        # 4-6
        if self.status != None:
            buf[4] = format(self.status,'02X')
            buf[4] += (format(0,'02X'))*(16-len(format(self.status,'02X'))//2)
        if self.fare_type != None:
            buf[5] = format(self.fare_type,'02X')
            buf[5] += (format(0,'02X'))*(16-len(format(self.fare_type,'02X'))//2)
        if self.balance != None:
            sign = '+' if self.balance >= 0 else '-'
            buf[6] = sign.encode().hex().upper()
            buf[6] += format(abs(self.balance), '06X')
            buf[6] += (format(0,'02X'))*(16-((len(format(self.balance,'06X')))+len(sign.encode().hex().upper()))//2)

        # 8-10
        if self.ride_exp != None:
            buf[9] = format(self.ride_exp,'016X')
            buf[9] += (format(0,'02X'))*(16-len(format(self.ride_exp,'16X'))//2)
        if self.active_zones != None:
            buf[10] = format(self.active_zones,'04X')
            buf[10] += (format(0,'02X'))*(16-len(format(self.active_zones,'04X'))//2)
        
        # 12-14
        if self.subscrip_time != None:
            buf[12] = format(self.subscrip_time,'016X')
            buf[12] += (format(0,'02X'))*(16-len(format(self.subscrip_time,'016X'))//2)
        if self.card_life != None:
            buf[13] = format(self.card_life,'016X')
            buf[13] += (format(0,'02X'))*(16-len(format(self.card_life,'16X'))//2)
        if self.subscrip_zones != None:
            buf[14] = format(self.subscrip_zones,'04X')
            buf[14] += (format(0,'02X'))*(16-len(format(self.subscrip_zones,'04X'))//2)

        # 16-62
        for i in range(12):
            buf[(i*4)+16] = ''
            # Block 1/3 in section
            if self.card_actions[i].timestamp != None:
                buf[(i*4)+16] += format(self.card_actions[i].timestamp,'016X')
            else:
                buf[(i*4)+16] += (format(0,'02X'))*(8-(len(buf[(i*4)+16])//2))

            if self.card_actions[i].new_balance != None:
                sign = '+' if self.card_actions[i].new_balance >= 0 else '-'
                buf[(i*4)+16] += sign.encode().hex().upper()
                buf[(i*4)+16] += format(abs(self.card_actions[i].new_balance),'06X')
            else:
                buf[(i*4)+16] += (format(0,'02X'))*(4-(len(buf[(i*4)+16])//2))

            if self.card_actions[i].balance_change != None:
                sign = '+' if self.card_actions[i].balance_change >= 0 else '-'
                buf[(i*4)+16] += sign.encode().hex().upper()
                buf[(i*4)+16] += format(abs(self.card_actions[i].balance_change),'06X')
            else:
                buf[(i*4)+16] += (format(0,'02X'))*(4-(len(buf[(i*4)+16])//2))
            buf[(i*4)+16] += (format(0,'02X'))*(16-(len(buf[(i*4)+16])//2))

            # Block 2/3 in sector
            buf[(i*4)+17] = ''
            if self.card_actions[i].action != None:
                buf[(i*4)+17] += format(self.card_actions[i].action,'02X')
            else:
                buf[(i*4)+17] += (format(0,'02X'))*(1-(len(buf[(i*4)+17])//2))

            if self.card_actions[i].zone != None:
                buf[(i*4)+17] += format(self.card_actions[i].zone,'04X')
            else:
                buf[(i*4)+17] += (format(0,'02X'))*(2-(len(buf[(i*4)+17])//2))

            if self.card_actions[i].bus_number != None:
                buf[(i*4)+17] += format(self.card_actions[i].bus_number,'04X')
            else:
                buf[(i*4)+17] += (format(0,'02X'))*(2-(len(buf[(i*4)+17])//2))

            if self.card_actions[i].verification != None:
                buf[(i*4)+17] += format(self.card_actions[i].zone,'08X')
            else:
                buf[(i*4)+17] += (format(0,'02X'))*(2-(len(buf[(i*4)+17])//2))

            buf[(i*4)+17] += (format(0,'02X'))*(16-(len(buf[(i*4)+17])//2))

        """
        # ----- Comment-in to print buffer before sending to be written
        for i in range(64):
            # print("b",i,":",len(buf[i]), sep="",end="  ")
            print(len(buf[i]), sep="",end="  ")
            if i!=0 and i%8==0:
                print('')
        print("\n-----")
        """

        buf_mod = ['']*64
        for i in range(64):
            block = ['']*16
            for j in range(len(buf[i])//2):
                block[j] = int( (buf[i][j*2] + buf[i][j*2+1]), 16)
            buf_mod[i] = list(block)

        return buf_mod


    # INPUT
    # Get input hex array: [[ ]*16]*64  and populate fields
    def hex_to_datafields(self, hex_in):
        
        for x in range(64):
            hex_in[x] = bytearray(hex_in[x]).hex()

        man_id = ''
        for i in range(16):
            man_id += (hex_in[0][i])
        self.man_id = int(man_id, 16)

        # 1-2
        id = ''
        for i in range(32):
            id  += hex_in[1][i]
        for i in range(32):
            id  += hex_in[2][i]
        self.id_num = int(id, 16)

        # # 4-6
        stat = ''
        stat += hex_in[4][0]
        stat += hex_in[4][1]
        self.status = int(stat, 16)

        f_type = ''
        f_type += hex_in[5][0]
        f_type += hex_in[5][1]
        self.fare_type = int(f_type, 16)

        sign = ''
        sign += hex_in[6][0]
        sign += hex_in[6][1]
        sign = bytearray.fromhex(sign).decode()
        balance = ''
        for i in range(6):
            balance += hex_in[6][i+2]
        self.balance = int(balance, 16)
        self.balance = (self.balance *-1) if sign == "-" else self.balance

        # # 8-10
        ride_exp = ''
        for i in range(16):
            ride_exp += hex_in[9][i]
        self.ride_exp = int(ride_exp, 16)

        zones = ''
        for i in range(4):
            zones += hex_in[10][i]
        self.active_zones = int(zones, 16)

        # # 12-14
        sub_time = ''
        for i in range(16):
            sub_time += hex_in[12][i]
        self.subscrip_time = int(sub_time, 16)

        card_life = ''
        for i in range(16):
            card_life += hex_in[13][i]
        self.card_life = int(card_life, 16)

        travel_zones = ''
        for i in range(4):
            travel_zones += hex_in[14][i]
        self.subscrip_zones = int(travel_zones, 16)

        # # 16-62
        for i in range(12):

            # Block 1/3 in section
            time_stamp = ''
            for j in range(16):
                time_stamp += hex_in[(i*4)+16][j]
            self.card_actions[i].timestamp = int(time_stamp, 16)

            sign = ''
            sign += hex_in[(i*4)+16][16]
            sign += hex_in[(i*4)+16][17]
            sign = bytearray.fromhex(sign).decode()
            new_balance = ''
            for j in range(6):
                new_balance += hex_in[(i*4)+16][j+18]
            self.card_actions[i].new_balance = int(new_balance, 16)
            if sign == "-":
                self.card_actions[i].new_balance = self.card_actions[i].new_balance * -1

            sign = ''
            sign += hex_in[(i*4)+16][24]
            sign += hex_in[(i*4)+16][25]
            sign = bytearray.fromhex(sign).decode()
            balance_change = ''
            for j in range(6):
                balance_change += hex_in[(i*4)+16][j+26]
            self.card_actions[i].balance_change = int(balance_change, 16)
            if sign == "-":
                self.card_actions[i].balance_change = self.card_actions[i].balance_change * -1

            # block 2/3 in section
            action = ''
            for j in range(2):
                action += hex_in[(i*4)+17][j]
            self.card_actions[i].action = int(action, 16)

            zone = ''
            for j in range(4):
                zone += hex_in[(i*4)+17][j+2]
            self.card_actions[i].zone = int(zone, 16)

            bus_number = ''
            for j in range(4):
                bus_number += hex_in[(i*4)+17][j+6]
            self.card_actions[i].bus_number = int(bus_number, 16)

            verification = ''
            for j in range(8):
                verification += hex_in[(i*4)+17][j+10]
            self.card_actions[i].verification = int(verification, 16)

        return

    def init_new_card(self, card_style = None):

        # If card style == 1 then generate a random card with poisitive values for testing database features
        # Note! These card actions will also be random and will not represent a true balance held in self.balance
        if card_style == 1:
            # self.man_id = None
            self.id_num = int(secrets.token_hex(32), base=16)
            self.status = 1
            self.fare_type = 1
            self.balance = secrets.randbelow(99900)
            self.ride_exp = (time.time_ns() // 1_000_000) + secrets.randbelow(7200000) # Time now + max 2h
            self.active_zones = secrets.randbelow(65536)
            self.subscrip_time = secrets.randbelow(13)
            self.card_life = time.time_ns() // 1_000_000 + secrets.randbelow(126230400000) # Time now + max 4 years
            self.subscrip_zones = 4

            for v in range(12):
                self.card_actions[v].timestamp = time.time_ns() // 1_000_000 + secrets.randbelow(604800000 ) # Time now - max 1 week
                self.card_actions[v].new_balance = secrets.randbelow(500) # 5 dollars max
                self.card_actions[v].balance_change = self.card_actions[v].new_balance + secrets.randbelow(250) # Max change 2.50 from new balance above
                self.card_actions[v].action = secrets.randbelow(20)
                self.card_actions[v].zone = secrets.randbelow(50)
                self.card_actions[v].bus_number = secrets.randbelow(999)
                self.card_actions[v].verification = secrets.randbelow(20)


        # Default value for card INIT. Real blank card.
        else: 
            # self.man_id = None
            self.id_num = int(secrets.token_hex(4), base=16) #! Changed from original token_hex(32) for a shorter card ID in demo videos
            self.status = 1
            self.fare_type = 1
            self.balance = 0
            self.ride_exp = time.time_ns() // 1_000_000
            self.active_zones = 0
            self.subscrip_time = 0
            self.card_life = (time.time_ns() // 1_000_000) + 126227808000 # 4 Years from now.
            self.subscrip_zones = 4
            
            # Add Card initialization action to physical card
            self.card_actions[0].timestamp = time.time_ns() // 1_000_000
            self.card_actions[0].new_balance = 0
            self.card_actions[0].balance_change = 0
            self.card_actions[0].action = 1
            self.card_actions[0].zone = 0
            self.card_actions[0].bus_number = 0
            self.card_actions[0].verification = secrets.randbelow(65536)

            # Zero out reamaining slots
            for v in range(11):
                self.card_actions[v+1].timestamp = 0
                self.card_actions[v+1].new_balance = 0
                self.card_actions[v+1].balance_change = 0
                self.card_actions[v+1].action = 0
                self.card_actions[v+1].zone = 0
                self.card_actions[v+1].bus_number = 0
                self.card_actions[v+1].verification = 0

    # add new card action into card actions by overwriting oldest one
    def update_oldest_card_action(self, new_action: card_action):
        oldest_action = 0
        for x in range(len(self.card_actions)):
            if self.card_actions[x].timestamp < self.card_actions[oldest_action].timestamp:
                oldest_action = x
                if self.card_actions[oldest_action].timestamp == 0: # Empty slot in card can automatically be filled.
                    break
        self.card_actions[oldest_action] = new_action
        # todo - test this function and make sure it works

    def check_data_integrity(self):
        #todo - finish all data checks... lol
        assert 0x00 <= self.id_num <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, "Invalid ID Number"
        assert 0 <= self.status <= 255, "Invalid status"

def epoch_to_human_time(epoch_in):
    try:
        time = datetime.datetime.fromtimestamp(int(epoch_in)/1000)
        return time.strftime('%Y-%m-%d %H:%M:%S.%f')
    except:
        return None


if __name__ == '__main__':
    a = physical_nfc_card()
    a.init_new_card()
    a.ride_exp = time.time_ns() // 1_000_000
    a.card_life = time.time_ns() // 1_000_000


    output = a.data_to_hex_for_output()
    b = physical_nfc_card()
    b.hex_to_datafields(output)

    print(a)
    print(b)

    out2 = b.data_to_hex_for_output()

    print( output == out2)

    c = physical_nfc_card()
    print(len(c.card_actions))


