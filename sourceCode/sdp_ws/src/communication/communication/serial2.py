import rclpy
from rclpy.node import Node
from custom_msgs.msg import IkResult, PointFiveElements
import pika
import threading
import serial
import time 

nodestart = time.time()

servo_angles = []
labels = []
directions = []

seqNum = 1

currentLabel = None
correctLabel = None

startt = 0.0

serialstart = time.time()
ser = serial.Serial('/dev/ttyACM0', 2000000, timeout = 1)
ser.flush()
serialend = time.time()
duration = serialend - serialstart
print(f"Time taken to establish and flush the serial connection: {duration:.4f} seconds")


# Creating SerialCom node
class SerialCom(Node):

    def __init__(self):
        super().__init__('serial_com')

        # subscribing to the angles topic
        self.subscription = self.create_subscription(IkResult, 'angles', self.serial_callback, 10)
        self.subscription


        # RabbitMQ connection
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='another_queue')
        
        nodeend = time.time()

        print(f"Node startup time: {nodeend - nodestart} seconds")
        print()

        print("Starting serial2.py")
        print("\n\n\n\n")



    # function to reconnect to rubbitMQ if connection got lost
    def reconnect_to_rabbitmq(self):
        print("Attempting to reconnect to RabbitMQ...")
        try:
            self.connection.close()
        except Exception:
            pass  # If the connection is already closed, ignore any exception
        
        # Re-establish the connection and channel
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='another_queue')
        print("Reconnected to RabbitMQ.")


    # publishing to the camera to do the verification phase
    def publish_message(self):
        print("publish to to the camera")
        data = "2" + currentLabel

        try:
            self.channel.basic_publish(exchange='', routing_key='another_queue', body=data.encode())
            print("Published message to the camera: ", data)
        except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed, pika.exceptions.StreamLostError) as e:
            print("Connection to RabbitMQ lost. Attempting to reconnect...")
            self.reconnect_to_rabbitmq()
            # retry the publish after reconnection
            print("Published to cam2.py after reconnecting")
            self.channel.basic_publish(exchange='', routing_key='another_queue', body=data.encode())



    # whenever receives data from iknew.py program
    def serial_callback(self, result):
        print("\n\n\n\n")
        global labels, servo_angles, directions

        labels.clear()
        servo_angles.clear()


        for label, point in zip(result.list_of_strings, result.list_of_points):
            labels.append(label)
            servo_angles.append(point)

        
        directions = result.list_of_directions

        print("Received from the motion_control node: ")

        for label, point in zip(labels, servo_angles):
            print(f"Label: {label}")
            print(f"  M1: {point.element1}")
            print(f"  M2: {point.element2}")
            print(f"  M3: {point.element3}")
            print(f"  M4: {point.element4}")

        print("\n\n")
        self.start_send()


    def start_send(self):
        

        global currentLabel, startt
        startt = time.time()
        
        if servo_angles:
            M1, M2, M3, M4 = servo_angles[0].element1, servo_angles[0].element2, servo_angles[0].element3, servo_angles[0].element4
            if M2 < 15:
                M2 = 15
            if M2 > 165 : 
                M2 = 165
                
            if not (0 <= M1 <= 180 and 0 <= M3 <= 180 and 0 <= M4 <= 180):
                print("wrong angles")
                return
                

            currentLabel = labels[0]

            if (labels[0] == "Rotten Orange"):
                M4 = M4 + 20

            data_to_send = f"1,{directions[0]},{M1},{M2},{M3},{M4}\n".encode('utf-8')
            print("Sending servo motor angles to the arduino ..")

            # sending servo motor angles to the arduino board to pick the fruit
            self.send_to_arduino(data_to_send)
            
            # Checking the number of attempt
            if (seqNum == 1):
                print("first try to pick the fruit")
                print("timer to pick the fruit and do the verification part = 25 sec\n")
                # Doing the verification phase after 20 seconds
                timerP = threading.Timer(20.0, self.publish_message)
                timerP.start()
            if (seqNum == 2):
                print("second try to pick the fruit !")
                print("timer to pick the fruit again and do the verification part = 30\n")
                # Doing the verification phase after 20 seconds
                timerP = threading.Timer(20.0, self.publish_message)
                timerP.start()

        else:
            data = "1"
            print("list is empty, publish to the camera to capture another frame")
            print("\n\n")
            #channel.basic_publish(exchange='', routing_key='another_queue', body=data.encode())



    # function to send to the arduino board utilizing threading
    def send_to_arduino(self, data_to_send):
        global ser
        def send():
            try:
                sendarduino = time.time()
                ser.write(data_to_send)
                sendarduinotimeend = time.time()
                print("Time taken to send to the arudino: ", sendarduinotimeend - sendarduino)

                pass 
            except Exception as e:
                print(f"Failed to send to Arduino with error: {e}")
                print("\n")

        thread = threading.Thread(target=send)
        thread.start()




# connecting to rabbitMQ
def start_consuming(serial_communication):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel2 = connection.channel()
    channel2.queue_declare(queue='verify')
    channel2.basic_consume(queue='verify', on_message_callback=lambda ch, method, properties, body: callback(ch, method, properties, body, serial_communication), auto_ack=True)
    channel2.start_consuming()


def callback(ch, method, properties, body, serial_communication):
    # After the verification phase
    global seqNum
    
    print("\n\n\n")
    received = body.decode()


    print("received after the verification : ", received)

    correctLable = received
    
    if (received != "no"):
        # Sorting the ripe fruit
        if (correctLable == "Ripe Apple" or correctLable == "Ripe Orange"):
            data_to_send = "2\n".encode('utf-8')
            send_to_arduino2(data_to_send)
            print("sorting the ripe fruit")

        # Sorting the rotten fruit
        elif (correctLable == "Rotten Apple" or correctLable == "Rotten Orange"):
            data_to_send = "3\n".encode('utf-8')
            send_to_arduino2(data_to_send)
            print("sorting the rotten fruit")

        print("\n\n")
        

        correctLable = ""


        labels.pop(0)
        servo_angles.pop(0)
        directions.pop(0)

     
        print("remaining fruits = ", labels)


        print("\n\n\n")
        if(seqNum == 2):
            seqNum = 1


        print("Waiting before picking the next fruit to reach the initial position [time will include placing the fruit in the box as well as going to the initial position]")
        print("\n\n")
        threading.Timer(10, execute_after_delay, args=(serial_communication, )).start() 


           

    # if failed to pick the fruit it will check the attempt number
    else:
        # if second attempt, it will go to the initial position
        if (seqNum == 2):
            labels.pop(0)
            servo_angles.pop(0)
            directions.pop(0)
            seqNum = 1

            data_to_send = "4\n".encode('utf-8')
            send_to_arduino2(data_to_send)
            # wait 
            print("Waiting before picking the next fruit to reach the initial position\n\n")
            threading.Timer(5, execute_after_delay, args=(serial_communication, )).start() 

        # if first attempt it will try again
        else:
            print("second try to pick the fruit")
            seqNum = 2
            data_to_send = "4\n".encode('utf-8')
            send_to_arduino2(data_to_send)
            # wait .....
            print("Waiting before picking the same fruit to reach the initial position\n")
            threading.Timer(5, execute_after_delay, args=(serial_communication, )).start()




def execute_after_delay(serial_communication):

    endt = time.time()
    print("latency for one fruit is: ", endt -  startt)
    
    serial_communication.start_send()


# another function to send data to the arduino board
def send_to_arduino2(data_to_send):
        global ser
        def send():
            try:
                ser.write(data_to_send)
                pass
            except Exception as e:
                print(f"Failed to send to Arduino with error: {e}")

        thread = threading.Thread(target=send)
        thread.start()
        
        



def main(args=None):
    rclpy.init(args=args)


    serial_communication = SerialCom()
    consuming_thread = threading.Thread(target=start_consuming, args=(serial_communication,))
    consuming_thread.start()


    try:
        rclpy.spin(serial_communication)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()
        serial_communication.connection.close()
        ser.close()


if __name__ == '__main__':
    main()
