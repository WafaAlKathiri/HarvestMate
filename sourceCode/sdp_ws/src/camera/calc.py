import math
import numpy as np
import depthai as dai
from numpy import median

class HostSpatialsCalc:
    def __init__(self, device):
        self.calibData = device.readCalibration()
        self.DELTA = 5
        self.THRESH_LOW = 200 # 20cm
        self.THRESH_HIGH = 3000 # 30m

    def _check_input(self, roi, frame): # Check if input is ROI or point. If point, convert to ROI
        if len(roi) == 4: return roi
        if len(roi) != 2: raise ValueError("You have to pass either ROI (4 values) or point (2 values)!")
       
        x = min(max(roi[0], self.DELTA), frame.shape[1] - self.DELTA)
        y = min(max(roi[1], self.DELTA), frame.shape[0] - self.DELTA)
        return (x-self.DELTA,y-self.DELTA,x+self.DELTA,y+self.DELTA)


    def calc_spatials(self, depthData, roi, rgbCamSocket, intrinsicsRgb, averaging_method=np.mean):
        depthFrame = depthData.getFrame()

        roi = self._check_input(roi, depthFrame) # If point was passed, convert it to ROI
        xmin, ymin, xmax, ymax = roi
        
        # Calculate the average depth in the ROI.
        depthROI = depthFrame[ymin:ymax, xmin:xmax]
        inRange = (self.THRESH_LOW <= depthROI) & (depthROI <= self.THRESH_HIGH)

        averageDepth = averaging_method(depthROI[inRange])
        
        
        # to map the bounding boxes
        scalex = 1084/416
        scaley = 1080/416
        
        x1 = int(xmin * scalex) + 10 
        x2 = int(xmax * scalex) - 10 
        y1 = int(ymin * scaley) + 10 
        y2 = int(ymax * scaley) - 10
        
        # The new bbox values
        xmin = x1 + 416
        ymin = y1
        xmax = x2 + 416
        ymax = y2
        
        
        centroid = {
            # To get the centroid of the ROI
            'x': int((xmax + xmin) / 2),
            'y': int((ymax + ymin) / 2)
        }
        
        
        # To find the inverse of the intrinsic matrix 
        intrinsics_inverse = np.linalg.inv(intrinsicsRgb)
        
        
        # using the inverse projection formula to find X and Y 
        uv1 = np.array([centroid['x'], centroid['y'], 1])
        uv_normalized = intrinsics_inverse @ uv1
        Xc = uv_normalized[0] * averageDepth
        Yc = uv_normalized[1] * averageDepth
       

        spatials = {
            'z': averageDepth,
            'x': Xc,
            'y': Yc
        }


        return spatials, centroid
