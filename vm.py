import random

class VM:

    PROGRAM_SECTION_START = 0x200

    def __init__(self):
        # 16 8-bit registers
        self.registers = {
            'v0': 0,
            'v1': 0,
            'v2': 0,
            'v3': 0,
            'v4': 0,
            'v5': 0,
            'v6': 0,
            'v7': 0,
            'v8': 0,
            'v9': 0,
            'va': 0,
            'vb': 0,
            'vc': 0,
            'vd': 0,
            've': 0,
            'vf': 0
        }

        # start program counter at beginning address in memory of 0x200
        self.pc = 0x200

        # 16-bit index register
        self.index = 0x00

        # 64 byte stack (here for simplicity we make it a list to use .append() and .pop())
        self.stack = [] # TODO maybe use numpy + acutal stack pointer

        # 8-bit stack pointer
        self.sp = 0b0

        # 8-bit delay timer
        self.delay_timer = 0b0 #TODO implement / expose way to tick

        # 8-bit sound timer
        self.sound_timer = 0b0 #TODO implement / expose way to tick + make sound

        # 64x32 bit frame buffer (each representing monochrome pixel)
        # All setting of pixels are done through use of sprites that
        # are always 8xn where n is the pixel height of each sprite
        self.frame_buffer = [[0b0] * 64 for i in range(32)] # TODO maybe use numpy? 

        # 4096 bytes of addressable memory
        # program/data space will live between 0x200 - 0xFFF
        self.memory = [0x00] * 4096

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

    def step(self, keyboard):
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
                ret_addr = self.stack.pop()
                self.pc = ret_addr
                self.sp -= 1 
            case ('0', _, _, _): # SYS addr. 0nnn jump to machine code routine at nnn
                print('not impl')
                self.pc += 2
            case ('1', _, _, _): # JMP instruction
                new_addr = '0x' + low_high + high_low + high_high
                self.pc = int(new_addr, 16)
            case ('2', _, _, _): # CALL addr. subroutine call, push current pc to stack, set PC to NNN
                self.stack.append(self.pc)
                self.sp += 1
                new_addr = '0x' + low_high + high_low + high_high
                self.pc = int(new_addr, 16)
            case ('3', _, _, _): # SE Vx, byte. 3xkk Skip next instruction if vx = kk
                val = high
                if self.registers[f'v{low_high}'] == val:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('4', _, _, _): # SNE Vx, byte. 4xkk Skip next instruction if vx != kk
                val = high
                if self.registers[f'v{low_high}'] != val:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('5', _, _, '0'): # SE Vx, Vy. 5xy0 Skip next instruction if vx = vy
                if self.registers[f'v{low_high}'] == self.registers[f'v{high_low}']:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('6', _, _, _): # LD Vx, byte. 6xkk set vx = kk
                self.registers[f'v{low_high}'] = high
                self.pc += 2
            case ('7', _, _, _): # ADD Vx, byte. 7xkk set vx = vx + kk
                vx = self.registers[f'v{low_high}']
                self.registers[f'v{low_high}'] = (vx + high) & 0xFF
                self.pc += 2
            case ('8', _, _, '0'): # LD Vx, Vy. 8xy0 set vx = vy
                self.registers[f'v{low_high}'] = self.registers[f'v{high_low}']
                self.pc += 2
            case ('8', _, _, '1'): # OR Vx, Vy. 8xy1 set vx = vx OR vy
                vx = self.registers[f'v{low_high}']
                vy = self.registers[f'v{high_low}']
                self.registers[f'v{low_high}'] = vx | vy
                self.pc += 2
            case ('8', _, _, '2'): # AND Vx, Vy. 8xy2 set vx = vx AND vy
                vx = self.registers[f'v{low_high}']
                vy = self.registers[f'v{high_low}']
                self.registers[f'v{low_high}'] = vx & vy
                self.pc += 2
            case ('8', _, _, '3'): # XOR Vx, Vy. 8xy3 set vx = vx XOR vy
                vx = self.registers[f'v{low_high}']
                vy = self.registers[f'v{high_low}']
                self.registers[f'v{low_high}'] = vx ^ vy
                self.pc += 2
            case ('8', _, _, '4'): # ADD Vx, Vy. 8xy4 set vx = vx + vy, set vf = carry
                vx = self.registers[f'v{low_high}']
                vy = self.registers[f'v{high_low}']
                n = vx + vy
                if (n > 255): # set carry flag (confirm the reset to 0 here)
                    self.registers['vf'] = 1
                else:
                    self.registers['vf'] = 0
                self.registers[f'v{low_high}'] = n & 0xff # lowest 8 bits
                self.pc += 2
            case ('8', _, _, '5'): # SUB Vx, Vy. 8xy5 set vx = vx - vy, set VF = NOT borrow
                vx = self.registers[f'v{low_high}']
                vy = self.registers[f'v{high_low}']
                if vx > vy:
                    self.registers['vf'] = 1
                else:
                    self.registers['vf'] = 0
                self.registers[f'v{low_high}'] = vx - vy
                self.pc += 2
            case ('8', _, _, '6'): # SHR Vx {, vy} 8xy6 set vx = vx SHR 1, set VF = LSB of vx
                vx = self.registers[f'v{low_high}']

                self.registers['vf'] = vx & 1
                
                self.registers[f'v{low_high}'] = vx >> 1
                self.pc += 2
            case ('8', _, _, '7'): # SUBN Vx, Vy. 8xy7 set vx = vy - vx, set VF = NOT borrow
                vx = self.registers[f'v{low_high}']
                vy = self.registers[f'v{high_low}']
                if vy > vx:
                    self.registers['vf'] = 1
                else:
                    self.registers['vf'] = 0
                self.registers[f'v{low_high}'] = vy - vx
                self.pc += 2
            case ('8', _, _, 'e'): # SHL Vx {, Vy} 8xye set vx = vx SHL 1, set VF = MSB of vx
                vx = self.registers[f'v{low_high}']
                msb_set = (vx & 0b10000000) == 0b10000000
                if msb_set:
                    self.registers['vf'] = 1
                else:
                    self.registers['vf'] = 0
                self.registers[f'v{low_high}'] = vx << 1
                self.pc += 2
            case ('9', _, _, '0'): # SNE Vx, Vy. 9xy0 skip next if vx != vy
                if self.registers[f'v{low_high}'] != self.registers[f'v{high_low}']:
                    self.pc += 2 # perform actual skip
                self.pc += 2
            case ('a', _, _, _): # LD I, addr. Annn set I = nnn
                addr = '0x' + low_high + high_low + high_high
                self.index = int(addr, 16)
                self.pc += 2
            case ('b', _, _, _): # JP v0, addr. Jump to location nnn + addr
                addr = '0x' + low_high + high_low + high_high
                new_addr = int(addr, 16) + self.registers['v0']
                self.pc = new_addr
            case ('c', _, _, _): # RND Vx, byte. Cxkk Set Vx = random byte & kk
                kk = '0x' + high_low + high_high
                self.registers[f'v{low_high}'] = random.randint(0,255) & int(kk, 16)
                self.pc += 2
            case ('d', _, _, _): # DRW Vx, Vy, nibble. Dxyn Display n-byte sprite starting at memory location I to (Vx, Vy). Set VF = collision
                vx = self.registers[f'v{low_high}'] & 0x3f # mod 64 for wrap
                vy = self.registers[f'v{high_low}'] & 0x1f # mod 32 for wrap
                n = int('0x' + high_high, 16)
                
                # sprites that are always 8 × N where N is the pixel height of the sprite
                for offset in range(n):
                    binary_string = format(self.memory[self.index + offset], '08b')
                    bit_list = list(map(int, binary_string))
                    for bit_index in range(8):
                        frame_bit = self.frame_buffer[(vy + offset) & 0x1f][(vx + bit_index) & 0x3f] # TODO sometimes IndexError: list index out of range
                        bit_list_bit = bit_list[bit_index]
                        if frame_bit == 1 and bit_list_bit == 1:
                            self.registers['vf'] = 1
                        self.frame_buffer[(vy + offset) & 0x1f][(vx + bit_index) & 0x3f] ^= bit_list_bit
                self.pc += 2
            case ('e', _, '9', 'e'): # SKP Vx. ex9e skip next instr if key with value vx is pressed
                vx = self.registers[f'v{low_high}']
                if (keyboard[vx] == 1):
                    self.pc += 2
                self.pc += 2
            case ('e', _, 'a', '1'): # SKNP Vx. exa1 skip next instr if key with value vx is not pressed
                vx = self.registers[f'v{low_high}']
                if (keyboard[vx] == 0):
                    self.pc += 2
                self.pc += 2
            case ('f', _, '0', '7'): #LD Vx, DT fx07. set vx = delay timer 
                self.registers[f'v{low_high}'] = self.delay_timer
                self.pc += 2
            case ('f', _, '0', 'a'): #LD Vx, K. fx0a wait for key, store value of key in vx
                # TODO pause execution while waiting for key, then read and process
                self.pc += 2
            case ('f', _, '1', '5'): # LD DT, Vx. fx15 Set delay timer = vx
                vx = self.registers[f'v{low_high}']
                self.delay_timer = vx
                self.pc += 2
            case ('f', _, '1', '8'): # LD ST, Vx. fx18 Set sound timer = vx
                vx = self.registers[f'v{low_high}']
                self.sound_timer = vx
                self.pc += 2
            case ('f', _, '1', 'e'): # ADD I, Vx. fx1e set I = I + Vx
                vx = self.registers[f'v{low_high}']
                self.index += vx
                self.pc += 2
            case ('f', _, '2', '9'): # LD F, Vx. fx29 Set I = location of sprite for digit Vx (from font)
                vx = self.registers[f'v{low_high}']
                self.index = vx * 5
                self.pc += 2
            case ('f', _, '3', '3'): # LD B, Vx. fx33 Store BCD representation of Vx in memory locations I, I+1, I+2
                # The interpreter takes the decimal
                # value of Vx, and places the hundreds digit in memory at location in I, the tens digit at location I+1, and
                # the ones digit at location I+2.
                vx = self.registers[f'v{low_high}']
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
                    self.memory[self.index + offset] = self.registers[f'v{hex(x)[2:]}']
                self.pc += 2
            case ('f', _, '6', '5'): # LD Vx, [I]. fx65 fill v0 - vx with values in memory starting at I
                x = int(low_high, 16)
                for offset in range(x + 1): # TODO should this be + 1?? I Think??
                    self.registers[f'v{hex(x)[2:]}'] = self.memory[self.index + offset]
                self.pc += 2
            case (_, _, _, _):
                print(f'bad instrction {low_low + low_high + high_low + high_high}')
                return
# vm = VM()
# vm.load_program('roms\maze.ch8')
# keyboard = [0] * 0xf #0x0 - #0xF
# while True:
#     vm.step(keyboard)
#     vm.debug_render_frame_buffer()