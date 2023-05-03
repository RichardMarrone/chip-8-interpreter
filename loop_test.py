# import time

# RATE = 1/500

# while True:
#     start_time = time.time()
#     print('Test')
#     end_time = time.time()
#     remain = start_time + 0.25 - end_time
#     if remain > 0:
#         time.sleep(remain)

# vx = 255
# hundreds = (vx % 1000) // 100
# tens = (vx % 100) // 10
# units = (vx % 10)

# print(hundreds, tens, units)
import pygame
from pygame.locals import *
import sys
import numpy as np
import cv2
import vm

pygame.init()
display = pygame.display.set_mode((400, 300))
clock = pygame.time.Clock()
chip8 = vm.VM()
chip8.load_program('roms\\Sierpinski.ch8')
keyboard = [0] * 0xf #0x0 - #0xF

pygame.display.set_caption('Chip-8 Emulator!')
while True: # main game loop
    clock.tick(1000) # run at x Hz
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        # if event.type == pygame.KEYDOWN:
        #     match event.key:
        #         case pygame.K_0:
        #             keyboard[0] = 1

    chip8.tick_timers() # only works if running @ 60Hz
    chip8.step(keyboard)
    # extract frame buffer and up-scale
    surf_array = chip8.frame_buffer
    np_surf_array = np.asarray(surf_array, dtype='uint8')
    np_surf_array = np.swapaxes(np_surf_array, 0, 1) # TODO need to transpose in pygame??
    scaled = cv2.resize(np_surf_array, dsize=(256,512), interpolation=cv2.INTER_LINEAR_EXACT)
    surf = pygame.surfarray.make_surface(scaled)


    display.blit(surf, (0,0))
    pygame.display.update()


