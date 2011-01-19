#!/usr/bin/env python
from pysolo_video import *

import pygame
from pygame.locals import *


def liveShow(monitor_number, resolution, mask_name, resize_mask, crop_way):
    '''
    Show images in realtime and creates the mask
    '''

    #res = resolution
    mon1 = Monitor(monitor_number, resolution=resolution)

    try:
        mon1.LoadCropFromFile(mask_name)
        print 'Loading mask: %s' % mask_name
    except:
        print 'A Mask with name %s has not been found and will be created. Use your mouse to do so.\nPress any key when done to save the mask or Exit the window to abort without saving' % mask_name

    if resize_mask[0] != resize_mask[1]:
        print 'Resizing mask from %sx%s to %sx%s' % (resize_mask[0][0], resize_mask[0][1], resize_mask[1][0], resize_mask[1][1])
        mon1.resizeCrop(*resize_mask)

    
    mon1.SetUseAverage(False)
    mon1.SetThreshold(75)
    preview_flies_movement = True

    fps = 30.0
    pygame.init()
    window = pygame.display.set_mode(resolution)
    pygame.display.set_caption("Live Show")
    screen = pygame.display.get_surface()

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == KEYDOWN:
                mon1.SaveCropToFile(mask_name)
                sys.exit(0)

            if event.type == MOUSEBUTTONDOWN:
                x, y = event.pos
            if event.type == MOUSEBUTTONUP:
                x1, y1 = event.pos
            
                if crop_way == (0,0):
                    mon1.AddCropArea((x,y,x1,y1))
                else:
                    x_offset = crop_way[0]
                    y_offset = crop_way[1]
                    mon1.AddCropArea((x1-x_offset,y1-y_offset,x1+x_offset,y1+y_offset))

        if preview_flies_movement:
            ## Shows the image with the fly position
            mon1.GetDiffImg(draw_crop = False, timestamp = 2)
            im = mon1.DrawXYAllFlies(use_diff = False, draw_crop = True)

        else:
        ## Shows the image with the currenlty cropped areas
            im = mon1.GetImage(draw_crop = True, timestamp = 2)


        pg_img = pygame.image.frombuffer(im.tostring(), im.size, im.mode)
        screen.blit(pg_img, (0,0))
        pygame.display.flip()
        pygame.time.delay(int(1000 * 1.0/fps))


if __name__ == '__main__':
    monitor = 0 #set to 0 for the first webcam, 1 for the second and so on
    resolution = (960,720)
    mask_name = 'default.mask'
    resize_mask = ((640,480), resolution)
    
    #method to be used when adding new crop areas 
    #crop_way = (0,0) ## The new area is defined using the mouse and select a rectangle
    crop_way = (12,120) ## click in the middle of the area to draw a fixed size rectangle
    
    liveShow(monitor, resolution, mask_name, resize_mask, crop_way)
