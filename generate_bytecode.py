import binascii

# load value 0xAA to register v0 
# load value 0x01 to register v1
# add two together with ADD (8xy4)
# my_hex = ['60', 'AA', '61', '01', '80', '14']
# with open('roms\sample.ch8', 'wb') as fp:
#     for hex in my_hex:
#         fp.write(binascii.unhexlify(hex))

# load value 0x005 to register Index ('1' digit in memory)
# DRW 5 byte sprite in index register to 0,0 [default value of v0 = 0]
# LD v1, 0x6 to
# load value 0x00A to register index ('2' digit in memory)
# DRW 5 byte sprite in index register to 6,0 [v1 = 6, v0 = 0]
# Clear Display 
# Return to addr 200
my_hex = ['A0', '05', 'D0', '05','61','06','A0', '0A', 'D1', '05', '00', 'E0', '12', '00']
with open('roms\draw_sample.ch8', 'wb') as fp:
    for hex in my_hex:
        fp.write(binascii.unhexlify(hex))
