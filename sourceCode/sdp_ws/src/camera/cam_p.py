# program to initiate the process
# it asks cam3.py to capture a frame

import pika


connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()


channel.queue_declare(queue='another_queue')

data = "start"
channel.basic_publish(exchange='', routing_key='another_queue', body=data.encode())

print("sent another_queue")
connection.close()
