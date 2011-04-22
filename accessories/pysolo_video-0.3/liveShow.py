#!/usr/bin/env python
from pysolo_video import *
import cv

class previewShow:
    
    def __init__(self, monitor_number, resolution, mask_name, resize_mask, crop_way, preview):
        '''
        Initialize constants and variables
        '''
        self.mon = Monitor(monitor_number, resolution=resolution)
           
        if  self.mon.LoadCropFromFile(mask_name): print ("Loading mask: %s" % mask_name)
        else: print ("A Mask with name %s has not been found and will be created. Use your mouse to do so.\n"
                     "Press any key when done to save the mask or Exit the window to abort without saving"
                      % mask_name )

        if resize_mask[0] != resize_mask[1]:
            print 'Resizing mask from %sx%s to %sx%s' % (resize_mask[0][0], resize_mask[0][1], resize_mask[1][0], resize_mask[1][1])
            self.mon.resizeCrop(*resize_mask)
        
        self.mon.SetUseAverage(False)
        self.mon.SetThreshold(75)
        self.preview = preview
        
    def Play(self):
        '''
        Show images in realtime and creates the mask
        '''
        cv.NamedWindow("w1", cv.CV_WINDOW_AUTOSIZE)
        cv.SetMouseCallback( "w1", self.on_mouse)

        self.drag_start = None      # Set to (x,y) when mouse starts drag
        self.track_window = None    # Set to rect when the mouse drag finishes

        while True:

            c = cv.WaitKey(33) & 255

            if c == 115: #s
                self.mon.SaveCropToFile(mask_name)
                sys.exit(0)
            elif c == 113: #q
                sys.exit(0)

            if self.preview: ## Shows the image with the fly position
                self.mon.GetDiffImg(draw_crop = False)
                im = self.mon.DrawXYAllFlies(use_diff = False, draw_crop = True)

            else: ## Shows the image with the currenlty cropped areas
                im = self.mon.GetImage(draw_crop = True)

            im_cv = cv.CreateImageHeader(im.size, cv.IPL_DEPTH_8U, 3)  # create empty RGB image
            cv.SetData(im_cv, im.tostring(), im.size[0]*3)
            #cv.CvtColor(im_cv, im_cv, cv.CV_RGB2BGR)
            
            cv.ShowImage("w1", im_cv)

    def on_mouse(self, event, x, y, flags, param):
        '''
        Handle Mouse Events
        '''
        if event == cv.CV_EVENT_LBUTTONDOWN:
            self.drag_start = (x, y)
            
        elif event == cv.CV_EVENT_LBUTTONUP:
            self.drag_end = (x, y)
            self.mon.AddCropArea( (self.drag_start[0], self.drag_start[1], self.drag_end[0], self.drag_end[1]) )
            
            self.drag_start = None
            self.drag_end = None

            
        elif event == cv.CV_EVENT_MOUSEMOVE and self.drag_start:
            #img1 = cv.CloneImage(img)
            #cv.Rectangle(img1, self.drag_start, (x, y), (0, 0, 255), 1, 8, 0)
            #cv.ShowImage("img", img1)
            pass



if __name__ == '__main__':
    monitor = 0 #set to 0 for the first webcam, 1 for the second and so on
    resolution = (640,480)
    mask_name = 'default.mask'
    resize_mask = ((640,480), resolution)
    preview = True
    
    #method to be used when adding new crop areas 
    #crop_way = (0,0) ## The new area is defined using the mouse and select a rectangle
    crop_way = (12,120) ## click in the middle of the area to draw a fixed size rectangle
    
    l = previewShow (monitor, resolution, mask_name, resize_mask, crop_way, preview)
    l.Play()
