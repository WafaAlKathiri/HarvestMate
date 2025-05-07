import rclpy
from rclpy.node import Node
import numpy as np
import os
import time
from PIL import Image
from classification import classify_coral
from classification import common
from classification.dataset import read_label_file
from classification.edgetpu import make_interpreter
from custom_msgs.msg import PointDictionary
from geometry_msgs.msg import PointStamped
from geometry_msgs.msg import Point
import numpy as np
from datetime import datetime

# added these modules
import threading
import pika
import json
import base64
import cv2

import tensorflow as tf
from tensorflow.keras.preprocessing import image

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

node_start = time.time()

i = 0 
verify = False 
verifiedLabel = None 

bbox_ver = []

callbackEnd = 0 
callbackStart = 0 


# Creating classify image node from the Node class
class classify_im(Node):

    def __init__(self):
    
        super().__init__('classify_im') 
        

        # Creating a variable that will publish the results to the classificationResult topic
        self.publisher_ = self.create_publisher(PointDictionary, 'classificationResult', 10)
        
        
        # specifying the tflite model path
        self.model = '/home/sdp19/sdp_ws/src/classification/classification/modelC.tflite'


        model_loding_startTime = datetime.now()
        # loading the classification model
        self.model = tf.saved_model.load(r"/home/sdp19/sdp_ws/src/classification/classification/modelC")
        model_loding_endTime = datetime.now()
    
        self.dataset_labels = ['Ripe Apple', 'Ripe Orange', 'Rotten Apple', 'Rotten Orange', 'UnRipe']



        print("model loading started at: ", model_loding_startTime)
        print("model loading ended at: ", model_loding_endTime)

        print("model loading time is: ", model_loding_endTime - model_loding_startTime)
        print("\n\n\n")


        self.setup_verify_connection()        

        self.rabbit_thread = threading.Thread(target=self.start_rabbitmq_consumer)
        self.rabbit_thread.start()
        
        node_end = time.time()
        print(f"Node startup time: {node_end - node_start} seconds")
        print("in classify.py")


    # function to be called if the connection to the rabbitMQ got lost
    def setup_verify_connection(self): 
        try:
            if hasattr(self, 'connection2'):
                self.connection2.close()
        except Exception as e:
            self.get_logger().warn(f"Failed to close RabbitMQ connection cleanly: {e}")

        
        self.connection2 = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel_angles = self.connection2.channel()
        self.channel_angles.queue_declare(queue='verify')



    # function to publish to verify queue ( the result of the verification phase )
    def send(self, data):
            
            print("\n\n")
            
            data = str(data)

            try:
                self.channel_angles.basic_publish(exchange='', routing_key='verify', body=data.encode())
                print("Published message to serial communication node: ", data)
            except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed, pika.exceptions.StreamLostError) as e:
                print(f"Connection to RabbitMQ lost when trying to publish: {e}. Attempting to reconnect...")
                self.setup_verify_connection()
                self.channel_angles.basic_publish(exchange='', routing_key='verify', body=data.encode())
                print("Published message to verify after reconnection: ", data)
            
            verify = False 
            verifiedLabel = None
        



    def start_rabbitmq_consumer(self):
        channel = connection.channel()
        channel.queue_declare(queue='mixed_data')        

        # deserializing the received data
        def deserialize_data(body):
            
            data = json.loads(body)
            
            image_base64 = data['frame']
            image_bytes = base64.b64decode(image_base64)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
            return frame, data['frameLabels'], data['coordinates'], data['bbox']
        


        def callback(ch, method, properties, body):

            global callbackStart, callbackStart2

            print("\n\n\n\n")

            callbackStart = datetime.now()
            callbackStart2 = time.time()


            global i, verify, verifiedLabel

            frame, labels, coordinates, bbox = deserialize_data(body)


            fileName = "/home/sdp19/sdp_ws/src/classification/classification/image" + str(i) + ".jpg"
            fileName2 = "/home/sdp19/Desktop/image.jpg"

            cv2.imwrite(fileName, frame)
            cv2.imwrite(fileName2, frame)
            
            
            # checking if the received labels are for the verification phase or not
            if (len(labels) > 1):
                if (labels[-2] == "2"):
                    verify = True 
                    verifiedLabel = labels[-1]

                    labels.pop(-2)
                    labels.pop(-1)
                    
                    
                    if (len(bbox) > 0):
                        #if ( bbox[0] < 90 and bbox[1] < 150 and bbox[2] > 250 and bbox[3] > 300 ) : 
                        bbox[0] = 70
                        bbox[1] = 100
                        bbox[2] = 270
                        bbox[3] = 350
                   

                    
                else:
                    verify = False 
            else: 
                verify = False

            #print("labels = ", labels)

            frame_copy = frame.copy()

            if (len(labels) > 0):
                lab = 0 
                for k in range(0, len(bbox), 4):
                    x1, y1, x2, y2 = bbox[k], bbox[k+1], bbox[k+2], bbox[k+3]
                    cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame_copy, labels[lab], (x1 + 10, y2 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255, thickness=1)
                    lab = lab + 1


            
            fileName3 = "/home/sdp19/Desktop/objectdetection.jpg"
            objDetectionPath = "/home/sdp19/sdp_ws/src/classification/classification/objDetIm" + str(i) + ".jpg"
            cv2.imwrite(fileName3, frame_copy)
            cv2.imwrite(objDetectionPath, frame_copy)

            i = i + 1


            self.crop_images(labels, coordinates, bbox, frame)
      

            
    


        channel.basic_consume(queue='mixed_data', on_message_callback=callback, auto_ack=True)
        channel.start_consuming()
        
        
    # function to crop the images
    def crop_images(self, labels, coordinates, bbox, frame):
        
        frame2 = frame.copy()
        color = (255, 0, 0)
       
        
        cropped_images = []
        m = 0


        for i in range(0, len(bbox), 4):
            x1, y1, x2, y2 = bbox[i], bbox[i+1], bbox[i+2], bbox[i+3]
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            if (x1 > 10):
                x1 = x1 - 10
            
            if (y1 > 10):
                y1 = y1 - 10
                
            if (x2 < 406):
                x2 = x2 + 10
                
            if (y2 < 406):
                y2 = y2 + 10
            
            cropped_image = frame2[y1:y2, x1:x2]


            # resizing the image for the classification model
            resized_image = cv2.resize(cropped_image, (224, 224)).astype(np.float32)
            
            cropped_images.append(resized_image)
            
            fileName90 = "/home/sdp19/sdp_ws/src/classification/classification/RI" + str(m) + ".jpg" 
            cv2.imwrite(fileName90, cropped_image)


            fileName4 = "/home/sdp19/Desktop/Classification.jpg"
            cv2.imwrite(fileName4, cropped_image)
            
            m = m + 1
        
        fileName3 = "/home/sdp19/Desktop/Classification.jpg"
        cv2.imwrite(fileName3, frame)

        #cv2.imshow("Object Detection", frame)
        
        new_labels = []
        new_bbox = []
        new_coordinates = []
        new_cropped_images = []
        
        i = 0
        b = 0
        c = 0 
        
        for item in labels:
            if (item == 'apple' or item == 'orange' or item == "Ripe Apple" or item == "Ripe Orange" or item == "Rotten Apple" or item == "Rotten Orange"):
                new_labels.append(item)
                new_bbox.append(bbox[i])
                new_bbox.append(bbox[i+1])
                new_bbox.append(bbox[i+2])
                new_bbox.append(bbox[i+3])
                
                new_coordinates.append(coordinates[b])
                new_coordinates.append(coordinates[b+1])
                new_coordinates.append(coordinates[b+2])
                
                new_cropped_images.append(cropped_images[c])
                
            i = i + 4
            b = b + 3
            c = c + 1
        
        cropImagesEnd = time.time()

        preprocessing_time = cropImagesEnd - callbackStart2

        print("\n\n")
        print(f"Frame Preprocessing Time [5 fruits]: {preprocessing_time:.3f} seconds")

        self.classification_callback(new_labels, new_coordinates, new_cropped_images, new_bbox, frame2)
        
    
        
    def classification_callback(self, new_labels, new_coordinates, cropped_images, new_bbox, frame2):
        
        classified_labels = []

        
        # classifying the cropped images
        for i in range(len(cropped_images)):
            start_time = time.time()
            
            input = cropped_images[i]

            fileN = '/home/sdp19/Desktop/ToModel' + str(i) + '.jpg'
            cv2.imwrite(fileN, input)


            jpeg_bytes = input / 255.0

            jpeg_bytes = np.expand_dims(jpeg_bytes, axis = 0)

            result = self.model(jpeg_bytes)

            predictionID = np.argmax(result[0])

            predictedLabel = self.dataset_labels[predictionID]

            classified_labels.append(predictedLabel)

            end_time = time.time()

            classification_time = end_time - start_time
            print(f"Classification time for image {i}: {classification_time} seconds")


        #print("before filter: ")      
        print("classified_labels = ", classified_labels)
        
        d = 0 

        frame_copy = frame2.copy()
        lab = 0 
        for k in range(0, len(new_bbox), 4):
            x1, y1, x2, y2 = new_bbox[k], new_bbox[k+1], new_bbox[k+2], new_bbox[k+3]
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_copy, classified_labels[lab], (x1 + 10, y2 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255, thickness=1)
            lab = lab + 1


        #cv2.rectangle(frame_copy, (90, 150), (250, 300), (0, 255, 0), 2)

        fileName5 = "/home/sdp19/Desktop/classification.jpg"
        cv2.imwrite(fileName5, frame_copy)

        classificationResult = "/home/sdp19/sdp_ws/src/classification/classification/ClassResult.jpg"
        cv2.imwrite(classificationResult, frame_copy)


        print("verify = ", verify)

        # Verifying the initial classification
        if(verify and len(classified_labels) > 0):
            print("Current Label = ", verifiedLabel)
            print("classified Label = ", classified_labels[0])
            print("\n")

            if (verifiedLabel):

                verifiedLabel2 = str(verifiedLabel)

                print("Result of Verification !!!!")
                if (classified_labels[0] == "Ripe Apple") : 
                    if (verifiedLabel2 == "Rotten Apple"):
                        print("it is Rotten Apple ! not Ripe Apple")
                        my_thread = threading.Thread(target=self.send, args=(verifiedLabel2,))
                        my_thread.start()

                    elif (verifiedLabel2 == "Ripe Apple"):
                        print("it is Ripe Apple")
                        my_thread = threading.Thread(target=self.send, args=(verifiedLabel2,))
                        my_thread.start()

                    else:
                        message = "It is " + str(classified_labels[0]) + " ! not Ripe Apple"
                        print(message)
                        my_thread = threading.Thread(target=self.send, args=(classified_labels[0],))
                        my_thread.start()


                elif (classified_labels[0] == "Ripe Orange"):
                    if (verifiedLabel2 == "Rotten Orange"):
                        print("it is Rotten Orange ! not Ripe Orange")
                        my_thread = threading.Thread(target=self.send, args=(verifiedLabel2,))
                        my_thread.start()

                    elif (verifiedLabel2 == "Ripe Orange"):
                        print("it is Ripe Orange")
                        my_thread = threading.Thread(target=self.send, args=(verifiedLabel2,))
                        my_thread.start()


                    else:
                        message = "It is " + str(classified_labels[0]) + " ! not Ripe Orange"
                        print(message)
                        my_thread = threading.Thread(target=self.send, args=(classified_labels[0],))
                        my_thread.start()
                        

                elif (classified_labels[0] == "Rotten Orange"):
                        message = "It is " + str(classified_labels[0]) + " !"
                        print(message)
                        my_thread = threading.Thread(target=self.send, args=(classified_labels[0],))
                        my_thread.start()

                elif (classified_labels[0] == "Rotten Apple"):
                        message = "It is " + str(classified_labels[0]) + " !"
                        print(message)
                        my_thread = threading.Thread(target=self.send, args=(classified_labels[0],))
                        my_thread.start()

                elif (classified_labels[0] == "UnRipe"):
                        message = "It is " + str(verifiedLabel2) + " !"
                        print(message)
                        my_thread = threading.Thread(target=self.send, args=(verifiedLabel2,))
                        my_thread.start()
            
            
            else: 
                print("No fruit to be verified !")
                my_thread = threading.Thread(target=self.send, args=("no",))
                my_thread.start()


        elif (len(classified_labels) == 0):
            print("No fruit to be verified !")
            my_thread = threading.Thread(target=self.send, args=("no",))
            my_thread.start()


        elif (verify == False):
            self.filter(classified_labels, new_coordinates)

    

    def filter(self, classified_labels, coordinates):
        # keeping only the ripe and rotten fruits
        global callbackEnd, callbackStart, callbackEnd2, callbackStart2

        new_classified_labels = []
        new_coordinates = []
        m = 0
        pointList = []
        
        point_msg = PointDictionary()
        
        for i in range(len(classified_labels)):
            if (classified_labels[i] == 'Ripe Apple' or classified_labels[i] == 'Ripe Orange' or classified_labels[i] == 'Rotten Orange' or classified_labels[i] == 'Rotten Apple'):
                new_classified_labels.append(classified_labels[i])
                new_coordinates.append(coordinates[m])
                new_coordinates.append(coordinates[m+1])
                new_coordinates.append(coordinates[m+2])
        
            
                point = Point(x = coordinates[m] , y = coordinates[m+1], z = coordinates[m+2])
                pointList.append(point)
                
            m = m + 3
                
        
        
        point_msg.keys = new_classified_labels
        point_msg.values = pointList
        
    

        c = 0 
        for num in range(0, len(new_coordinates), 3):
            print(new_classified_labels[c], end='')
            print(" :   ", end = '')
            print(new_coordinates[num:num+3])
            c = c + 1 


        callbackEnd = datetime.now()
        callbackEnd2 = time.time()

        classification_time2 = callbackEnd2 - callbackStart2

        print("Classification node response time is: ", callbackEnd - callbackStart)
        print(f"Classification time: {classification_time2} seconds")

        # publishing the results
        self.publisher_.publish(point_msg)

        classificaitonEnd = time.time()

        latency = classificaitonEnd - callbackStart2
        print(f"Latency: {latency:.3f} seconds")
        print("published to transform node")
        print("\n\n\n\n\n\n")
    
                
                
def main(args=None):
    rclpy.init(args=args)

    classify_frame = classify_im()

    rclpy.spin(classify_frame)

    classify_frame.destroy_node()
    rclpy.shutdown()
    

if __name__ == '__main__':
    main()
