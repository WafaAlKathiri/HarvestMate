#!/usr/bin/env python3

from pathlib import Path
import cv2
import depthai as dai
import numpy as np
import time
from calc import HostSpatialsCalc
import config
import functions
import pika
import base64
import json
import threading
import math


print("Cam3.py started")

stop = True
received = []
msgs = dict()
detections = []
frame = None
frameDisp = None
startTime = time.monotonic()
counter = 0
frame2 = None


# check if the blob file is in the correct path 
print(config.fps)
if not Path(config.nnPath).exists():
    raise FileNotFoundError(f'Required file not found, please run')


pipeline = dai.Pipeline()
device = dai.Device()

# sources and outputs
camRgb = pipeline.create(dai.node.ColorCamera)
detectionNetwork = pipeline.create(dai.node.YoloDetectionNetwork)

xoutRgb = pipeline.create(dai.node.XLinkOut)
xoutRgb.setStreamName("rgb")

nnOut = pipeline.create(dai.node.XLinkOut)
nnOut.setStreamName("nn")

monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)

xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutDepth.setStreamName("depth")

xoutDisp = pipeline.create(dai.node.XLinkOut)
xoutDisp.setStreamName("disp")

xin_frame = pipeline.create(dai.node.XLinkIn)
xin_frame.setStreamName("in_frame")


# Properties
rgbCamSocket = functions.colorCameraProperties(camRgb, device)
functions.YoloDetectionNetworkProperties(detectionNetwork)
functions.monoCameraProperties(monoLeft, monoRight)
functions.stereoProperties(stereo, rgbCamSocket)


# Linking
camRgb.preview.link(xoutRgb.input)
detectionNetwork.out.link(nnOut.input)
xin_frame.out.link(detectionNetwork.input)


monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)
stereo.depth.link(xoutDepth.input)
stereo.disparity.link(xoutDisp.input)



# sync. the depth and RGB frames 
def add_msg(msg, name, seq = None):
    if seq is None:
        seq = msg.getSequenceNum()
    seq = str(seq)
    if seq not in msgs:
        msgs[seq] = dict()
    msgs[seq][name] = msg
    
    
    
def get_msgs():
    global msgs
    sorted_seqs = sorted(msgs.keys(), key=int, reverse=True)
    for seq in sorted_seqs:
        syncMsgs = msgs[seq]
        # Check if we have a complete set of messages for this sequence number
        if len(syncMsgs) == 3:  # 'rgb', 'disp', 'depth' are required
            # Remove the processed sequence to prevent reprocessing
            del msgs[seq]
            return syncMsgs  # Return the latest synchronized msgs
    return None


def callback(ch, method, properties, body):
    
    # calllback function from another_queue 
    print("\n\n\n")
    global received

    received = body.decode()

    print("received from the serial communication node = ", received)
    
    # image processing 
    blue_channel = frame[:, :, 0].flatten()
    green_channel = frame[:, :, 1].flatten()
    red_channel = frame[:, :, 2].flatten()
    planar_image = np.concatenate((blue_channel, green_channel, red_channel))

    in_frame = dai.ImgFrame()
    in_frame.setWidth(416)
    in_frame.setHeight(416)
    in_frame.setType(dai.RawImgFrame.Type.BGR888p)
    in_frame.setData(planar_image)
    q_in_frame.send(in_frame)



    in_nn = qDet.get()   # keep it get() for synchronization
    if in_nn is not None:
        detections = in_nn.detections
        
        
        if frame is not None:
            displayFrame("detetctions", frame, depthData, hostSpatials, rgbCamSocket, intrinsicsRgb, detections, disp)



def frameNorm(frame, bbox):
    # normalization
    normVals = np.full(len(bbox), frame.shape[0])
    normVals[::2] = frame.shape[1]
    return (np.clip(np.array(bbox), 0, 1) * normVals).astype(int)


# function to display the frames
def displayFrame(name, frame, depthData, hostSpatials, rgbCamSocket, intrinsicsRgb, detections, disp):

    global received

    
    color = (255, 0, 0)
    color2 = (255, 255, 255)  # White color in BGR
    coordinates = []
    bbox2 = []
    frameLabels = []
    
    d = 1
    m = 0 
    c = 0 

    for detection in detections:

        ver = 1
        bbox = frameNorm(frame, (detection.xmin, detection.ymin, detection.xmax, detection.ymax))
        cv2.putText(disp, config.labelMap[detection.label], (bbox[0] + 10, bbox[1] + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)

        # to calculate the spatial coordinates of each detection
        spatials, cetroid = hostSpatials.calc_spatials(depthData, (bbox[0], bbox[1], bbox[2], bbox[3]), rgbCamSocket, intrinsicsRgb)
                
        cv2.putText(disp, "X: " + ("{:.3f}m".format(spatials['x'] / 1000) if not math.isnan(spatials['x']) else "--"), (bbox[0], bbox[1] + 60), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        cv2.putText(disp, "Y: " + ("{:.3f}m".format(spatials['y'] / 1000) if not math.isnan(spatials['y']) else "--"), (bbox[0], bbox[1] + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        cv2.putText(disp, "Z: " + ("{:.3f}m".format(spatials['z'] / 1000) if not math.isnan(spatials['z']) else "--"), (bbox[0], bbox[1] + 100), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color2)
        
        
        cv2.rectangle(disp, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

        # only pass apples and oranges
        if (config.labelMap[detection.label] == "apple" or config.labelMap[detection.label] == "orange"):
            print("Inside comp")
            if ( received[0] == '2' and ver == 1):
                print("inside received")
                if ( bbox[0] < 90 and bbox[1] < 150 and bbox[2] > 250 and bbox[3] > 300 ) : 
                    print("bbox comp")

                    bbox2.append(bbox[0])
                    bbox2.append(bbox[1])
                    bbox2.append(bbox[2])
                    bbox2.append(bbox[3]) 

                    print("bbox[0] = ", bbox[0])
                    print("bbox[1] = ", bbox[1])
                    print("bbox[2] = ", bbox[2])
                    print("bbox[3] = ", bbox[3])        
        
                    coordinates.append(spatials['x'] / 1000)
                    coordinates.append(spatials['y'] / 1000)
                    coordinates.append(spatials['z'] / 1000)

                    frameLabels.append(config.labelMap[detection.label])

                    ver == 2 

            else:
                bbox2.append(bbox[0])
                bbox2.append(bbox[1])
                bbox2.append(bbox[2])
                bbox2.append(bbox[3]) 

                print("bbox[0] = ", bbox[0])
                print("bbox[1] = ", bbox[1])
                print("bbox[2] = ", bbox[2])
                print("bbox[3] = ", bbox[3])        
        
                coordinates.append(spatials['x'] / 1000)
                coordinates.append(spatials['y'] / 1000)
                coordinates.append(spatials['z'] / 1000)

                frameLabels.append(config.labelMap[detection.label])



    for i in range(0, len(coordinates), 3):
        print(frameLabels[c], end='')
        print(" :   ", end = '')
        print(coordinates[i:i+3])
        c = c + 1 
        

    print("\n\n\n\n")  
    
    fileName = "/home/sdp19/sdp_ws/src/classification/classification/image9" + str(m) + ".jpg" 
    cv2.imwrite(fileName, disp)
    

    fileName2 = "/home/sdp19/Desktop/disp.jpg" 
    cv2.imwrite(fileName2, disp)
    
    m = m + 1

    # serializing data into JSON format before sending them to mixed_data queue
    data = serialize_data(frame, frameLabels, coordinates, bbox2)
    channel2.basic_publish(exchange='', routing_key='mixed_data', body=data.encode())



def start_consuming():
    
    channel = connection.channel()
    channel.queue_declare(queue='another_queue')
    channel.basic_consume(queue = 'another_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()
    
    

def serialize_data(frame, frameLabels, coordinates, bbox):
    
    # Serializing data into JSON format 
    print("\n\n\n\n")
    print("frameLabels = ", frameLabels)

    _,buffer = cv2.imencode('.jpg', frame)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    bbox2 = [int(i) for i in bbox]
    
    coordinates2 = [float(i) for i in coordinates]

    # if it is the verification phase
    if (received[0] == '2'):
        rest_of_received = received[1:]
        frameLabels.append("2")
        frameLabels.append(rest_of_received)


        print("frameLabels = ", frameLabels)


    data = {
        "frame": image_base64,
        "frameLabels" : frameLabels,
        "coordinates": coordinates2,
        "bbox": bbox2
        }
    
    return json.dumps(data) 



# RabbitMQ Connection
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel2 = connection.channel()

channel2.queue_declare(queue='mixed_data')


thread = threading.Thread(target=start_consuming)
thread.start()


with device:
    device.startPipeline(pipeline)

    hostSpatials = HostSpatialsCalc(device)

    q_in_frame = device.getInputQueue(name="in_frame")
    qDet = device.getOutputQueue(name="nn", maxSize=4, blocking=False)


    # Getting the intrinsic matrix
    calibData = device.readCalibration()
    intrinsicsRgb = calibData.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, 1920, 1080)
    print("Intrinsic Parameters of RGB Camera (1080P):")
    print(intrinsicsRgb)

    prev_time = time.monotonic()

    while True:

        current_time = time.monotonic()
        frame_response_time = current_time - prev_time
        #print(f"Frame response time: {frame_response_time} seconds")


        for name in ['rgb', 'disp', 'depth']:
            msg = device.getOutputQueue(name).tryGet()
            if msg is not None:
                add_msg(msg, name)
        
        prev_time = current_time
                
        
        synced = get_msgs()
        if synced:
        
            frame = synced["rgb"].getCvFrame()
            depthData = synced["depth"]
            disp = synced["disp"].getFrame()
            
            cv2.imshow("rgb", frame)
            cv2.imshow("disp", disp)
            

            key = cv2.waitKey(1)

            if key == ord('q'):
                break


cv2.destroyAllWindows()
connection.close()
thread.join()
