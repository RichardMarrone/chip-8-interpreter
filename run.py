import pygame
from pygame.locals import *
import sys
import numpy as np
import cv2
import vm

pygame.init()
display = pygame.display.set_mode((256, 128))
clock = pygame.time.Clock()
chip8 = vm.VM()
chip8.load_program('roms\\Keypad.ch8')
keyboard = [0] * 16 #0x0 - #0xF
key_map = { # Ascii -> hex 0-9 A-F
        48: 0,
        49: 1,
        50: 2,
        51: 3,
        52: 4,
        53: 5,
        54: 6,
        55: 7,
        56: 8,
        57: 9,
        97: 10, #0xA
        98: 11, #0xB
        99: 12, #0xC
        100: 13, #0xD 
        101: 14, #0xE
        102: 15 #0xF
    }

pygame.display.set_caption('Chip-8 Emulator!')
while True: # main game loop
    clock.tick(100) # run at x Hz
    keyboard_signal = False
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            keyboard_signal = True
            if event.key in key_map:
                keyboard[key_map[event.key]] = 1

        if event.type == pygame.KEYUP:
            keyboard_signal = True
            if event.key in key_map:
                keyboard[key_map[event.key]] = 0
    

    chip8.tick_timers() # only works if running @ 60Hz
    chip8.step(keyboard, keyboard_signal)
    # up-scale and rotate frame buffer
    surf_array = chip8.frame_buffer
    np_surf_array = np.swapaxes(surf_array, 0, 1) # TODO need to transpose in pygame??
    scaled = cv2.resize(np_surf_array, dsize=(128,256), interpolation=cv2.INTER_CUBIC)
    surf = pygame.surfarray.make_surface(scaled)
    surf.set_palette_at(0, (255,255,255,255))
    surf.set_palette_at(1, (0,0,255,255))
    display.blit(surf, (0,0))
    pygame.display.update()


