#!/usr/bin/env python
####################################################
#
# Use this program to view offline the activity of flies
# you must specify the path where the images are stored
#
# you can either create a new mask
# or load an existing one
#
#
# This program is part of pySolo
# http://www.pysolo.net
# 
#####################################################


from pysolo_video import *
import pygame
from pygame.locals import *

try:
    import psyco
    psyco.full()
except:
    pass

def offlineProcessor(vc, mask_name, resize_mask=((960,720),(960,720)), crop_way=(0,0)):

    
    mon1 = Monitor(virtual_cam = vc )

    mon1.SetUseAverage(False)
    mon1.SetThreshold(75) #threshold value used to calculate position of the fly
    
    try:
        mon1.LoadCropFromFile(mask_name)
        print 'Successfully loaded mask %s' % mask_name
    except:
        print 'I tried to load mask %s but could not suceed. Does it exist?' % mask_name
    
    if resize_mask[0] != resize_mask[1]:
        print 'Resizing mask from %sx%s to %sx%s' % (resize_mask[0][0], resize_mask[0][1], resize_mask[1][0], resize_mask[1][1])
        mon1.resizeCrop(*resize_mask)

    number_of_flies = mon1.GetNumberOfVials()
    flies_per_vial = 1
    
    coords = [(0,0)] * number_of_flies 
    last_coords = [[(0,0)]] * number_of_flies
    frame_num = 0
    fpv = flies_per_vial -1
    
    outFile = '%s.pvf' % mask_name.split('.')[0]
    
    of = open(outFile, 'w')
    
    print 'Proceeding with the analysis of %s flies\nResults will be saved in file %s' % (number_of_flies, outFile)
    
    while not mon1.isLastFrame():

        frame_num +=1
        if frame_num % 100 == 0: print 'processed %s frames' % frame_num
        diff_img = mon1.GetDiffImg()

        for fly_n in range(number_of_flies):
            c = mon1.GetXYFly(fly_n, diff_img)
            if c == []: c = last_coords[fly_n]
            coords[fly_n] = c
            last_coords[fly_n] = c

        t = '%s\t' % frame_num
        for fc in coords:
            t += '%s,%s\t' % (fc[fpv][0], fc[fpv][1])

        t += '\n'
        of.write(t)
    
    of.close()

def offlineViewer(vc, mask_name, resize_mask=((960,720),(960,720)), crop_way=(0,0), loop=False):

    
    mon1 = Monitor(virtual_cam = vc )

    try:
        mon1.LoadCropFromFile(mask_name)
        print 'Loading mask: %s' % mask_name
    except:
        print 'A Mask with name %s has not been found and will be created. Use your mouse to do so.\nPress any key when done to save the mask or Exit the window to abort without saving' % mask_name

    if resize_mask[0] != resize_mask[1]:
        print 'Resizing mask from %sx%s to %sx%s' % (resize_mask[0][0], resize_mask[0][1], resize_mask[1][0], resize_mask[1][1])
        mon1.resizeCrop(*resize_mask)

    mon1.SetUseAverage(False)
    mon1.SetThreshold(75) #threshold value used to calculate position of the fly
    mon1.SetLoop(True)
    
    fps = 30.0
    pygame.init()
    resolution = mon1.resolution
    window = pygame.display.set_mode(resolution)
    pygame.display.set_caption("Offline Analysis")
    screen = pygame.display.get_surface()

    while not mon1.isLastFrame():
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

        ## Shows the image with the currenlty cropped areas
        #im = mon1.GetImage(draw_crop = True, timestamp = 2)
        
        ## Shows the image with the fly position
        mon1.GetDiffImg(draw_crop = False, timestamp = 2)
        im = mon1.DrawXYAllFlies(use_diff = False, draw_crop = True)

        pg_img = pygame.image.frombuffer(im.tostring(), im.size, im.mode)
        screen.blit(pg_img, (0,0))
        pygame.display.flip()
        pygame.time.delay(int(1000 * 1.0/fps))
            


if __name__ == '__main__':

    #where are the images we want to create the mask for?
    #path = 'C:/sleepData/videoData/2009/03/0318'
    #path = '/data/moredata/Video/2009/02/0219'
    path = '/home/gg/Desktop/reflydetection/'


    #enter mask name. If the mask exists will be loaded and used
    #else, it will be created
    mask_name = 'default.mask'
    resize_mask = ((800,600), (800,600))

    #method to be used when adding new crop areas 
    #crop_way = (0,0) ## The new area is defined using the mouse and select a rectangle
    crop_way = (10,150) ## click in the middle of the area to draw a fixed size rectangle
    
    
    vc = [path, None, None, None] #step, start, end
    
    #offlineViewer(vc, mask_name, resize_mask, crop_way, loop=True)
    offlineProcessor(vc, mask_name, resize_mask, crop_way)
