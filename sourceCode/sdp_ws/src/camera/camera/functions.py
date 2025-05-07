import depthai as dai
import numpy as np
import cv2
import config
import math
import pika
import json


# Function to configure the colorCamera node
def colorCameraProperties(camRgb, device):
    rgbCamSocket = dai.CameraBoardSocket.CAM_A  # added this
    camRgb.setBoardSocket(rgbCamSocket)  # added this
    camRgb.setPreviewSize(416, 416)
    camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
    camRgb.setInterleaved(False)
    camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
    camRgb.setFps(config.fps)
    camRgb.initialControl.setManualFocus(0)


    try:
        calibData = device.readCalibration2()
        lensPosition = calibData.getLensPosition(rgbCamSocket)
        if lensPosition:
            camRgb.initialControl.setManualFocus(lensPosition)
    except:
        raise

    return rgbCamSocket


# Function to configure yoloDetectionNetwork Node
def YoloDetectionNetworkProperties(detectionNetwork):
    detectionNetwork.setConfidenceThreshold(0.5)
    detectionNetwork.setNumClasses(80)
    detectionNetwork.setCoordinateSize(4)
    detectionNetwork.setAnchors([10.0, 13.0, 16.0, 30.0, 33.0, 23.0, 30.0, 61.0, 62.0, 45.0, 59.0, 119.0, 116.0, 90.0, 156.0, 198.0, 373.0, 326.0])
    detectionNetwork.setAnchorMasks({"side52": [0, 1, 2], "side26": [3, 4, 5], "side13": [6, 7, 8]})
    detectionNetwork.setIouThreshold(0.5)
    detectionNetwork.setBlobPath(config.nnPath)
    detectionNetwork.setNumInferenceThreads(2)
    detectionNetwork.input.setBlocking(False)



# Function to configure the monoCamera node
def monoCameraProperties(monoLeft, monoRight):
    monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoLeft.setBoardSocket(dai.CameraBoardSocket.CAM_B)
    monoLeft.setFps(config.fps)

    monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoRight.setBoardSocket(dai.CameraBoardSocket.CAM_C)
    monoRight.setFps(config.fps)


# Function to configure the stereo node
def stereoProperties(stereo, rgbCamSocket):
    stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)  # added
    stereo.initialConfig.setConfidenceThreshold(255)
    stereo.setLeftRightCheck(True)
    stereo.setSubpixel(False)
    stereo.setDepthAlign(rgbCamSocket)  # added this
    stereo.setOutputSize(416, 416)     #it makes difference


# Function to normalize the bbox
def frameNorm(frame, bbox):
    normVals = np.full(len(bbox), frame.shape[0])
    normVals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)


# Function to display the frames along with the detections
def displayFrame(name, frame, depthData, hostSpatials, rgbCamSocket, intrinsicsRgb, detections, disp):
    color = (255, 0, 0)
    color2 = (255, 255, 255)  # White color in BGR
    coordinates = []
    
    d = 1 
	
    for detection in detections:
        bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
        cv2.putText(frame, config.labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
        cv2.putText(frame, f"{int(detection.confidence * 100)}%", (bbox[0] + 10, bbox[1] + 40), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

        spatials, cetroid = hostSpatials.calc_spatials(depthData, (bbox[0], bbox[1], bbox[2], bbox[3]), rgbCamSocket, intrinsicsRgb)


        cv2.putText(frame, "X: " + ("{:.3f}m".format(spatials['x'] / 1000) if not math.isnan(spatials['x']) else "--"), (bbox[0], bbox[1] + 60), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        cv2.putText(frame, "Y: " + ("{:.3f}m".format(spatials['y'] / 1000) if not math.isnan(spatials['y']) else "--"), (bbox[0], bbox[1] + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        cv2.putText(frame, "Z: " + ("{:.3f}m".format(spatials['z'] / 1000) if not math.isnan(spatials['z']) else "--"), (bbox[0], bbox[1] + 100), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        
        
        
        cv2.putText(disp, "X: " + ("{:.3f}m".format(spatials['x'] / 1000) if not math.isnan(spatials['x']) else "--"), (bbox[0], bbox[1] + 60), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        cv2.putText(disp, "Y: " + ("{:.3f}m".format(spatials['y'] / 1000) if not math.isnan(spatials['y']) else "--"), (bbox[0], bbox[1] + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        cv2.putText(disp, "Z: " + ("{:.3f}m".format(spatials['z'] / 1000) if not math.isnan(spatials['z']) else "--"), (bbox[0], bbox[1] + 100), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        
        
        cv2.rectangle(disp, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)


        print("label = ", config.labelMap[detection.label])
        print("X: " + ("{:.3f}m".format(spatials['x'] / 1000)))
        print("Y: " + ("{:.3f}m".format(spatials['y'] / 1000)))
        print("Z: " + ("{:.3f}m".format(spatials['z'] / 1000)))
        
        if ( d == 1 and config.labelMap[detection.label] == 'apple'):
            coordinates.append(spatials['x'] / 1000)
            coordinates.append(spatials['y'] / 1000)
            coordinates.append(spatials['z'] / 1000)
            d = d + 1
            send_coordinates(coordinates)
            print("---------------------------------------------------------------")
            print("label ====== ", config.labelMap[detection.label]) 
            print(coordinates)


    
    
    
    cv2.imshow(name, frame)
    cv2.imshow("depth", disp)



def send_coordinates(coordinates):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare a queue
    channel.queue_declare(queue='coordinatesQueue')

    # Send a message
    channel.basic_publish(exchange='', routing_key='coordinatesQueue', body=json.dumps(coordinates))

    print(" [x] Sent coordinates")
    connection.close()


