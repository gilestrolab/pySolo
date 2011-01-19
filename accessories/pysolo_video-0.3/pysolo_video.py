#!/usr/bin/env python
from VideoCapture import Device
import numpy as np
from scipy.misc import fromimage, toimage
from scipy.cluster import vq

from ImageDraw import Draw
#import ImageChops
from PIL import ImageFont, Image, ImageChops

import os, sys, datetime, time
from sys import platform

import cPickle

class VirtualCam(object):
    '''
        A Virtual cam to be used to pick images from a folder rather than a webcam
    '''
    def __init__(self, path, step = None, start = None, end = None):
        self.path = path
        self.fileList = self.populateList(start, end, step)
        self.currentFrame = 0
        self.loop = False

        fp = os.path.join(self.path, self.fileList[0])
        self.resolution = Image.open(fp).size
        
        #what is the path for the arial and arialbd fonts in mac?
        if 'linux' in platform: #linux
            self.normalfont = ImageFont.truetype('/usr/share/fonts/truetype/msttcorefonts/arial.ttf', 12)
        elif 'darwin' in platform: #macos
            self.normalfont = ImageFont.truetype('/Library/Fonts/ArialHB.ttf', 12)
        else: #windows
            self.normalfont = ImageFont.truetype('C:\\Windows\\fonts\\arial.ttf', 12)

        self.font = None


    def __getFileTime__(self, fname):
        '''
        Return the time of most recent content modification of the file fname
        '''
        return os.stat(fname)[-2]

    def getImage(self, timestamp=0, boldfont=0, textpos='bl'):
        """Returns a PIL Image instance.

        timestamp:  0 ... no timestamp (the default)
                    1 ... simple timestamp
                    2 ... timestamp with shadow
                    3 ... timestamp with outline

        boldfont:   0 ... normal font (the default)
                    1 ... bold font

        textpos:    The position of the timestamp can be specified by a string
                    containing a combination of two characters.  One character
                    must be either t or b, the other one either l, c or r.

                    t ... top
                    b ... bottom

                    l ... left
                    c ... center
                    r ... right

                    The default value is 'bl'

        """
        n = self.currentFrame
        fp = os.path.join(self.path, self.fileList[n])

        self.currentFrame += 1

        try:
            im = Image.open(fp)
        except:
            print 'error with image %s' % fp
            raise
        ##from opencv import highgui
        ##im = highgui.cvLoadImage(fp)

        if timestamp:
            width, height = self.resolution
            textcolor = 0xffffff
            shadowcolor = 0x000000

            fileTime = self.__getFileTime__(fp)
            text = time.asctime(time.localtime(fileTime))

            if boldfont:
                self.font = self.boldfont
            else:
                self.font = self.normalfont
            tw, th = self.font.getsize(text)
            tw -= 2
            th -= 2
            if 't' in textpos:
                y = -1
            elif 'b' in textpos:
                y = height - th - 2
            else:
                raise ValueError, "textpos must contain exactly one out of 't', 'b'"
            if 'l' in textpos:
                x = 2 
            elif 'c' in textpos:
                x = (width - tw) / 2
            elif 'r' in textpos:
                x = (width - tw) - 2
            else:
                raise ValueError, "textpos must contain exactly one out of 'l', 'c', 'r'"
            draw = Draw(im)
            if timestamp == 2: # shadow
                draw.text((x+1, y), text, font=self.font, fill=shadowcolor)
                draw.text((x, y+1), text, font=self.font, fill=shadowcolor)
                draw.text((x+1, y+1), text, font=self.font, fill=shadowcolor)
            else:
                if timestamp >= 3: # thin border
                    draw.text((x-1, y), text, font=self.font, fill=shadowcolor)
                    draw.text((x+1, y), text, font=self.font, fill=shadowcolor)
                    draw.text((x, y-1), text, font=self.font, fill=shadowcolor)
                    draw.text((x, y+1), text, font=self.font, fill=shadowcolor)
                if timestamp == 4: # thick border
                    draw.text((x-1, y-1), text, font=self.font, fill=shadowcolor)
                    draw.text((x+1, y-1), text, font=self.font, fill=shadowcolor)
                    draw.text((x-1, y+1), text, font=self.font, fill=shadowcolor)
                    draw.text((x+1, y+1), text, font=self.font, fill=shadowcolor)
            draw.text((x, y), text, font=self.font, fill=textcolor)
        
        return im
    

    def populateList(self, start, end, step):
        '''
        Populate the file list
        '''
        
        fileList = []
        fileListTmp = os.listdir(self.path)

        for fileName in fileListTmp:
            if '.tif' in fileName or '.jpg' in fileName:
                fileList.append(fileName)

        fileList.sort()
        return fileList[start:end:step]

    def isLastFrame(self):
        '''
        Are we processing the last frame in the folder?
        '''
        l = len(self.fileList)
        if (self.currentFrame == l) and not self.loop:
            return True
        elif (self.currentFrame == l) and self.loop:
            self.currentFrame = 0
            return False
        else:
            return False
            
    
    def getResolution(self):
        '''
        Return the resolution of the virtual camera, 
        namely the resolution of the first file in the folder
        '''
        return self.resolution
    
    def GetAverageImage(self, n = 50):
        '''
        Return an image that is the average of n frames equally distanced from each other
        '''
        tot_frames = len( self.fileList)
        step = tot_frames / n

        avg_list = self.fileList[::step]
        n = len(avg_list)
        
        x, y = self.resolution
        avg_array = np.zeros((y, x, 3))
        
        for i in range(n):
            fp = os.path.join(self.path, avg_list[i])
            avg_array += fromimage( Image.open(fp), flatten = False )

            
        return toimage(avg_array / len(avg_array))



class Monitor(object):
    """
        The main monitor class
    """

    def __init__(self, devnum=0, resolution=(800,600), virtual_cam = None ):
        if virtual_cam:
            self.cam = VirtualCam(path=virtual_cam[0], step=virtual_cam[1], start = virtual_cam[2], end = virtual_cam[3])
            resolution = self.cam.getResolution()
            self.numberOfFrames = len(self.cam.fileList)
            self.isVirtualCam = True
        else:
            self.cam = Device(devnum=devnum)
            self.cam.setResolution(*resolution)
            self.numberOfFrames = 0
            self.isVirtualCam = False

        self.resolution = resolution

        self.use_average = False
        self.calculating_average = False
        self.avg_frame_num = 100; self.__n = self.avg_frame_num
        
        self.all_coords = []
        self.points_to_track = []
        self.threshold = 35
        self.imageCount = 0
        
        self.avgImg = self.GetImage()
        self.diffImg = self.GetImage()
        self.__n = 0


    def __drawCrop__(self, img, (x1, y1, x2, y2)):
        '''
        Draw a crop rectangle on img using given coordinates
        '''
        draw = Draw(img)
        draw.rectangle([x1, y1, x2, y2], outline=0xFFFFFF)
        return img

    def __getOnlyChannel__(self, img, channel='R'):
        '''
        Return only the asked channel
        '''
        channel = 'RGB'.find(channel.upper())
        source = img.split()
        return source[channel]

    def __absCoord__(self, fly_n, coords):
        '''
        Transform coordinates from relative to the crop area to relative
        to the entire frame
        '''
        new_coords = []
        
        for (x, y) in coords:
            x1, y1 = self.all_coords[fly_n][0:2]
            new_coords . append( ( x+x1, y+y1 ) )
        return new_coords

    def __white_points__(self, data, threshold):
        '''
        Finds all the white points with intensity value higher than threshold
        '''
        g = np.where(data > threshold)
        points = np.array(zip(g[1], g[0]), "f")
        return points

    def __distance__(self, x1, y1, x2, y2):
        '''
        Calculate the distance between two cartesian points
        '''
        return np.sqrt((x2-x1)**2 + (y2-y1)**2)

    def isLastFrame(self):
        '''
        In case we are using the virtual camera, returns 
        True when we are calling the last frame
        '''
        if self.isVirtualCam:
            return self.cam.isLastFrame()
        else:
            return False
    
    def SetThreshold(self, value):
        '''
        Set the value for the threshold for motion detection
        '''
        self.threshold = value

    def SetUseAverage(self, value, n = None):
        '''
        Do we want to use the average of some images as reference?
        '''
        self.avg_frame_num = n or self.avg_frame_num
        self.use_average = value

        if self.use_average and not self.isVirtualCam:
            x, y = self.lastImg.size
            self.avg_array = np.zeros((y, x, 3))
            self.calculating_average = True
        
        elif self.use_average and self.isVirtualCam:
            self.calculating_average = False
            self.avgImg = self.cam.GetAverageImage(self.avg_frame_num)
            


    def GetUseAverage(self):
        '''
        Are we using the average of some images as reference?
        '''
        return self.use_average

    def AddCropArea(self, (x1, y1, x2, y2), n_flies=1):
        '''
        Add the coords for a new crop area and the number of flies we want to track in that area
        '''
        self.all_coords.append((x1, y1, x2, y2))
        self.points_to_track.append(n_flies)

    def GetCropArea(self, n):
        '''
        Returns the coordinates of the nth crop area
        '''
        if n > len(self.all_coords):
            coords = []
        else:
            coords = self.all_coords[n]
        return coords

    def DelCropArea(self, n):
        '''
        removes the nth crop area from the list
        '''
        self.all_coords.pop(n)
        
    def SaveCropToFile(self, filename):
        '''
        Save the current crop data to a file
        '''
        cf = open(filename, 'w')
        cPickle.dump(self.all_coords, cf)
        cPickle.dump(self.points_to_track, cf)

        cf.close()
        
    def LoadCropFromFile(self, filename):
        '''
        Load the crop data from a file
        '''
        cf = open(filename, 'r')
        self.all_coords = cPickle.load(cf)
        self.points_to_track = cPickle.load(cf)
        cf.close()

    def resizeCrop(self, origSize, newSize):
        '''
        Resize the mask to new size so that it would properly fit
        resized images
        '''
        ox, oy = origSize
        nx, ny = newSize
        xp = float(ox) / nx
        yp = float(oy) / ny
        
        for i, (x1, y1, x2, y2) in enumerate(self.all_coords):
            rx1 = int(x1 / xp); rx2 = int(x2 / xp)
            ry1 = int(y1 / yp); ry2 = int(y2 / yp)
            self.all_coords[i] = (rx1, ry1, rx2, ry2)

        
    def GetNumberOfVials(self):
        '''
        Return how many Cropped area we are analizing
        '''
        return len(self.all_coords)
        

    def SetPointsToTrack(self, value):
        '''
        Set how many points we want to track
        '''
        self.points_to_track = value

    def GetPointsToTrack(self, value):
        '''
        Set how many points we want to track
        '''
        return self.points_to_track



    def GetImage(self, draw_crop = False, **keywords):
        '''
        GetImage(self, draw_crop = False, timestamp=0, boldfont=0, textpos='bl')
        
        Returns the last collected image
        '''
        self.lastImg = self.cam.getImage(**keywords)
        self.imageCount += 1

        if self.use_average and self.calculating_average:
            self.avg_array += fromimage(self.lastImg, flatten = False)
            self.__n += 1
    	    if self.__n == self.avg_frame_num:
                self.avgImg = toimage(self.avg_array / self.__n)
                del self.avg_array
                self.calculating_average = False
                self.__n = 0
                self.SetUseAverage(True)
            
                
        if draw_crop:
            img = self.lastImg.copy()
            for coords in self.all_coords:
                img = self.__drawCrop__(img, coords)
        else:
            img = self.lastImg

        return img


    def GetDiffImg(self, draw_crop = False, **keywords):
        '''
        GetDiffImg(self, draw_crop = False, timestamp=0, boldfont=0, textpos='bl')

        Return the difference between the last collected image and either the average Reference or the previously collected image
        '''
        #What do we compare the image to?
        if self.use_average and not self.calculating_average:
            diff = self.avgImg
        else:
            diff = self.lastImg

        self.diffImg = ImageChops.subtract(self.GetImage(**keywords), diff)

        #Do we want to draw the cropped area?
        if draw_crop:
            for coords in self.all_coords:
                self.diffImg = self.__drawCrop__(self.diffImg, coords)

        return self.diffImg

    def saveImage(self, *args, **kwargs):
        '''
        proxy to saveSnapshot
        '''
        self.cam.saveSnapshot(*args, **kwargs)

    def GetCropImage(self, fly_n, use_diff = True):
        '''
        Return the last image of the crop for fly_n
        '''
        crop_cords = self.all_coords[fly_n]
        if use_diff:
            img = self.GetDiffImg().crop(crop_cords)
        else:
            img = self.GetImage().crop(crop_cords)

        return img

    def compressAllImages(self, compression=90, resolution=(960,720)):
        '''
        good only for virtual cams
        Load all images one by one and save them in a new folder 
        '''
        x,y = resolution[0], resolution[1]
        if self.isVirtualCam:
            in_path = self.cam.path
            out_path = os.path.join(in_path, 'compressed_%sx%s_%02d' % (x, y, compression))
            os.mkdir(out_path)
            
            for img in self.cam.fileList:
                f_in = os.path.join(in_path, img)
                im = Image.open(f_in)
                #print im.size
                if im.size != resolution: 
                    im = im.resize(resolution, Image.ANTIALIAS)
                
                f_out = os.path.join(out_path, img)
                im.save (f_out, quality=compression)

            return True    

        else:
            return False

    def GetXYFly(self, fly_n, diff_img):
        '''
        Returns the coordinates of the fly/flies
        '''

        coords = self.all_coords[fly_n]
        ptt = self.points_to_track[fly_n]
        img = diff_img.crop(tuple(coords))

        X, Y = img.size
        x, y = 0, 0
        coords = []

        imA = fromimage(img, flatten = 1)
        points = self.__white_points__(imA, self.threshold)

        if len(points) > 0:
            codebook, distortion = vq.kmeans(points, ptt)
            for p in codebook:
                x, y = int(p[0]), int(p[1])
                coords.append((x, y))
            if len(coords) > 1 and self.__distance__(coords[-1][0], coords[-1][1], coords[-2][0], coords[-2][1]) < 10: coords.pop()
        return coords

    def DrawXYFly(self, flies, use_diff = True, use_entire = True, draw_crop = False):
        '''
        Return an image with a cross in correspondance of fly  position based on last frame 
        flies can be a list of flies to track or a single fly number (e.g.: [2,3,7] or 1 are both valid)
        use_diff: plot on the regular image or the subtraction image
        use_entire: return only the crop area or the entire frame
        draw_crop: draws also the crop for fly_n
        '''

        if not isinstance(flies, list):
            flies = [flies]
        else:
            use_entire = True

        if use_diff:
            img = self.diffImg
        else:
            img = self.lastImg

        for fly_n in flies:
            coords = self.GetXYFly(fly_n, self.diffImg)
            crop_coords = self.all_coords[fly_n]
            
            if use_entire:
                coords = self.__absCoord__(fly_n, coords)
                crop_coords = (0,0, self.resolution[0], self.resolution[1])
    
            img = img.crop(crop_coords)
            draw = Draw(img)
            for (x, y) in coords:
                draw.line((x-10, y-10) + (x+10, y+10), fill=0xFFFFFF)
                draw.line((x-10, y+10) + (x+10, y-10), fill=0xFFFFFF)
    
            if draw_crop and use_entire:
                img = self.__drawCrop__(img, self.all_coords[fly_n])

        return img

    def DrawXYAllFlies(self, use_diff = True, draw_crop = False):
        '''
        Returns a frame marking the movement of all the flies
        '''
        l = len(self.all_coords)
        return self.DrawXYFly(range(l), use_diff=use_diff, use_entire=True, draw_crop=draw_crop)

