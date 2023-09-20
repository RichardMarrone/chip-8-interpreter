import random
import numpy as np

class VM:

    PROGRAM_SECTION_START = 0x200

    def __init__(self):

        # 16 8-bit registers 
        self.register_v = np.zeros(16, dtype=np.uint8)

        # start program counter at beginning address in memory of 0x200
        self.pc = 0x200

        # 16-bit index register
        self.index = 0x00

        # are we currently holding execution while we wait for keypress
        self.waiting_key = False

        # 16 x 16 bit value stack
        self.stack = np.zeros(16, dtype=np.uint16) 

        # 8-bit stack pointer
        self.sp = 0

        # 8-bit delay timer
        self.delay_timer = 0

        # 8-bit sound timer
        self.sound_timer = 0 #TODO need to actually make sound

        # 64x32 bit frame buffer (each representing monochrome pixel)
        # All setting of pixels are done through use of sprites that
        # are always 8xn where n is the pixel height of each sprite
        self.frame_buffer = np.zeros((32, 64), dtype=np.uint8)

        # 4096 bytes of addressable memory
        # program/data space will live between 0x200 - 0xFFF
        self.memory = np.zeros(4096, dtype=np.uint8)

        # 0x0 - 0x080 reserved for Font Set
        # font set allows for 0-9 and A-F to be printed
        # each char fits within an 8x5 grid
        self.font_bytes = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,		# 0
            0x20, 0x60, 0x20, 0x20, 0x70,		# 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,		# 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,		# 3
            0x90, 0x90, 0xF0, 0x10, 0x10,		# 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,		# 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,		# 6
            0xF0, 0x10, 0x20, 0x40, 0x40,		# 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,		# 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,		# 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,		# A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,		# B
            0xF0, 0x80, 0x80, 0x80, 0xF0,		# C
            0xE0, 0x90, 0x90, 0x90, 0xE0,		# D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,		# E
            0xF0, 0x80, 0xF0, 0x80, 0x80		# F
        ]

        self.load_font_set()

    def load_font_set(self):
        for i in range(len(self.font_bytes)):
            self.memory[i] = self.font_bytes[i]

    def debug_render_frame_buffer(self):
        for row in self.frame_buffer:
            for col in row:
                if col == 0:
                    print(' ', end='')
                else:
                    print('█', end='')
            print()

    def clear_frame_buffer(self):
        for row in range(len(self.frame_buffer)):
            for col in range(row):
                self.frame_buffer[row][col] = 0
    
    def tick_timers(self): # TODO only works when we run processor at 60Hz :|
        if self.sound_timer > 0:
            self.sound_timer -= 1
        
        if self.delay_timer > 0:
            self.delay_timer -= 1

    def load_program(self, path):
        offset = 0
        with open(path,'rb') as fp:
            while True:
                byte = fp.read(1)
                if not byte:
                    break
                self.memory[self.PROGRAM_SECTION_START + offset] = int(byte.hex(), 16)
                offset += 1

    def step(self, keyboard, keyboard_signal):
        low = self.memory[self.pc]
        high = self.memory[self.pc + 1]
        low_low = hex((low >> 4) & 0xf)[2:]
        low_high = hex(low & 0xf)[2:]
        high_low = hex((high >> 4) & 0xf)[2:]
        high_high = hex(high & 0xf)[2:]

        # Todo: need better error here, 0 is falsey
        # if not low or not high:
        #     raise Exception(f'Error occurred attempting to read from memory at {self.pc} or {self.pc + 1}')
        match (low_low, low_high, high_low, high_high):
            case ('0', '0', 'e', '0'): # CLS. Clear Frame Buffer
                self.clear_frame_buffer()
                self.pc += 2
            case ('0', '0', 'e', 'e'): # RET. pop address from stack and move pc there
                ret_addr = self.stack[self.sp]
                self.sp -= 1 
                self.pc = ret_addr
                self.pc += 2
            case ('0', _, _, _): # SYS addr. 0nnn jump to machine code routine at nnn
                print('not impl')
                self.pc += 2
            case ('1', _, _, _): # JMP instruction
                new_addr = '0x' + low_high + high_low + high_high
                self.pc = int(new_addr, 16)
            case ('2', _, _, _): # CALL addr. subroutine call, push current pc to stack, set PC to NNN
                self.sp += 1
                self.stack[self.sp] = self.pc
                new_addr = '0x' + low_high + high_low + high_high
                self.pc = int(new_addr, 16)
            case ('3', _, _, _): # SE Vx, byte. 3xkk Skip next instruction if vx = kk
                val = high
                if self.register_v[int(low_high, 16)] == val:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('4', _, _, _): # SNE Vx, byte. 4xkk Skip next instruction if vx != kk
                val = high
                if self.register_v[int(low_high, 16)] != val:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('5', _, _, '0'): # SE Vx, Vy. 5xy0 Skip next instruction if vx = vy
                if self.register_v[int(low_high, 16)] == self.register_v[int(high_low, 16)]:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('6', _, _, _): # LD Vx, byte. 6xkk set vx = kk
                self.register_v[int(low_high, 16)] = high
                self.pc += 2
            case ('7', _, _, _): # ADD Vx, byte. 7xkk set vx = vx + kk
                vx = self.register_v[int(low_high, 16)]
                self.register_v[int(low_high, 16)] = (vx + high) & 0xFF
                self.pc += 2
            case ('8', _, _, '0'): # LD Vx, Vy. 8xy0 set vx = vy
                self.register_v[int(low_high, 16)] = self.register_v[int(high_low, 16)]
                self.pc += 2
            case ('8', _, _, '1'): # OR Vx, Vy. 8xy1 set vx = vx OR vy
                vx = self.register_v[int(low_high, 16)]
                vy = self.register_v[int(high_low, 16)]
                self.register_v[int(low_high, 16)] = vx | vy
                self.pc += 2
            case ('8', _, _, '2'): # AND Vx, Vy. 8xy2 set vx = vx AND vy
                vx = self.register_v[int(low_high, 16)]
                vy = self.register_v[int(high_low, 16)]
                self.register_v[int(low_high, 16)] = vx & vy
                self.pc += 2
            case ('8', _, _, '3'): # XOR Vx, Vy. 8xy3 set vx = vx XOR vy
                vx = self.register_v[int(low_high, 16)]
                vy = self.register_v[int(high_low, 16)]
                self.register_v[int(low_high, 16)] = vx ^ vy
                self.pc += 2
            case ('8', _, _, '4'): # ADD Vx, Vy. 8xy4 set vx = vx + vy, set vf = carry
                vx = self.register_v[int(low_high, 16)]
                vy = self.register_v[int(high_low, 16)]
                n = vx + vy # TODO numpy is somehow getting into registers with its 8 bit values and causing overflow. Need to ensure register writes are python ints
                if (n > 255): # set carry flag (confirm the reset to 0 here)
                    self.register_v[15] = 1
                else:
                    self.register_v[15] = 0
                self.register_v[int(low_high, 16)] = n & 0xff # lowest 8 bits
                self.pc += 2
            case ('8', _, _, '5'): # SUB Vx, Vy. 8xy5 set vx = vx - vy, set VF = NOT borrow
                vx = self.register_v[int(low_high, 16)]
                vy = self.register_v[int(high_low, 16)]
                if vx > vy:
                    self.register_v[15] = 1
                else:
                    self.register_v[15] = 0
                self.register_v[int(low_high, 16)] = vx - vy
                self.pc += 2
            case ('8', _, _, '6'): # SHR Vx {, vy} 8xy6 set vx = vx SHR 1, set VF = LSB of vx
                vx = self.register_v[int(low_high, 16)]

                self.register_v[15] = vx & 1
                
                self.register_v[int(low_high, 16)] = vx >> 1
                self.pc += 2
            case ('8', _, _, '7'): # SUBN Vx, Vy. 8xy7 set vx = vy - vx, set VF = NOT borrow
                vx = self.register_v[int(low_high, 16)]
                vy = self.register_v[int(high_low, 16)]
                if vy > vx:
                    self.register_v[15] = 1
                else:
                    self.register_v[15] = 0
                self.register_v[int(low_high, 16)] = vy - vx
                self.pc += 2
            case ('8', _, _, 'e'): # SHL Vx {, Vy} 8xye set vx = vx SHL 1, set VF = MSB of vx
                vx = self.register_v[int(low_high, 16)]
                self.register_v[15] = vx >> 7
                self.register_v[int(low_high, 16)] = (vx << 1) & 0xff
                self.pc += 2
            case ('9', _, _, '0'): # SNE Vx, Vy. 9xy0 skip next if vx != vy
                if self.register_v[int(low_high, 16)] != self.register_v[int(high_low, 16)]:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('a', _, _, _): # LD I, addr. Annn set I = nnn
                addr = '0x' + low_high + high_low + high_high
                self.index = int(addr, 16)
                self.pc += 2
            case ('b', _, _, _): # JP v0, addr. Jump to location nnn + addr
                addr = '0x' + low_high + high_low + high_high
                new_addr = int(addr, 16) + self.register_v[0]
                self.pc = new_addr
            case ('c', _, _, _): # RND Vx, byte. Cxkk Set Vx = random byte & kk
                kk = '0x' + high_low + high_high
                self.register_v[int(low_high, 16)] = random.randint(0,255) & int(kk, 16)
                self.pc += 2
            case ('d', _, _, _): # DRW Vx, Vy, nibble. Dxyn Display n-byte sprite starting at memory location I to (Vx, Vy). Set VF = collision
                vx = self.register_v[int(low_high, 16)] & 0x3f # mod 64 for wrap
                vy = self.register_v[int(high_low, 16)] & 0x1f # mod 32 for wrap
                n = int('0x' + high_high, 16)
                
                # sprites that are always 8 × N where N is the pixel height of the sprite
                for offset in range(n):
                    binary_string = format(self.memory[self.index + offset], '08b')
                    bit_list = list(map(int, binary_string))
                    for bit_index in range(8):
                        frame_bit = self.frame_buffer[(vy + offset) & 0x1f][(vx + bit_index) & 0x3f] # TODO sometimes IndexError: list index out of range
                        bit_list_bit = bit_list[bit_index]
                        if frame_bit == 1 and bit_list_bit == 1:
                            self.register_v[15] = 1
                        self.frame_buffer[(vy + offset) & 0x1f][(vx + bit_index) & 0x3f] ^= bit_list_bit
                self.pc += 2
            case ('e', _, '9', 'e'): # SKP Vx. ex9e skip next instr if key with value vx is pressed
                vx = self.register_v[int(low_high, 16)]
                if (keyboard[vx] == 1):
                    self.pc += 2
                self.pc += 2
            case ('e', _, 'a', '1'): # SKNP Vx. exa1 skip next instr if key with value vx is not pressed
                vx = self.register_v[int(low_high, 16)]
                if (keyboard[vx] == 0):
                    self.pc += 2
                self.pc += 2
            case ('f', _, '0', '7'): #LD Vx, DT fx07. set vx = delay timer 
                self.register_v[int(low_high, 16)] = self.delay_timer
                self.pc += 2
            case ('f', _, '0', 'a'): #LD Vx, K. fx0a wait for key, store value of key in vx
                if (self.waiting_key and keyboard_signal): # we were waiting but we've just recv'd signal
                    self.register_v[int(low_high, 16)] = keyboard.index(1) # TODO may be buggy because we are only looking for 1 key press at a time. If multiple held, this fails
                    self.pc += 2
                # otherwise wait for key press   
                self.waiting_key = True
            case ('f', _, '1', '5'): # LD DT, Vx. fx15 Set delay timer = vx
                vx = self.register_v[int(low_high, 16)]
                self.delay_timer = vx
                self.pc += 2
            case ('f', _, '1', '8'): # LD ST, Vx. fx18 Set sound timer = vx
                vx = self.register_v[int(low_high, 16)]
                self.sound_timer = vx
                self.pc += 2
            case ('f', _, '1', 'e'): # ADD I, Vx. fx1e set I = I + Vx
                vx = self.register_v[int(low_high, 16)]
                self.index += vx
                self.pc += 2
            case ('f', _, '2', '9'): # LD F, Vx. fx29 Set I = location of sprite for digit Vx (from font)
                vx = self.register_v[int(low_high, 16)]
                self.index = vx * 5
                self.pc += 2
            case ('f', _, '3', '3'): # LD B, Vx. fx33 Store BCD representation of Vx in memory locations I, I+1, I+2
                # The interpreter takes the decimal
                # value of Vx, and places the hundreds digit in memory at location in I, the tens digit at location I+1, and
                # the ones digit at location I+2.
                vx = self.register_v[int(low_high, 16)]
                hundreds = (vx % 1000) // 100
                tens = (vx % 100) // 10
                units = (vx % 10)
                self.memory[self.index] = hundreds
                self.memory[self.index + 1] = tens
                self.memory[self.index + 2] = units
                self.pc += 2
            case ('f', _, '5', '5'): # LD [I], Vx. fx55 store v0 - vx in memory starting at I
                x = int(low_high, 16)
                for offset in range(x + 1): #TODO should this be + 1?? I think??
                    self.memory[self.index + offset] = self.register_v[offset]
                self.pc += 2
            case ('f', _, '6', '5'): # LD Vx, [I]. fx65 fill v0 - vx with values in memory starting at I
                x = int(low_high, 16)
                for offset in range(x + 1): # TODO should this be + 1?? I Think??
                    self.register_v[offset] = self.memory[self.index + offset]
                self.pc += 2
            case (_, _, _, _):
                print(f'bad instrction {low_low + low_high + high_low + high_high}')
                return
