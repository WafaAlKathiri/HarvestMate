import rclpy
from rclpy.node import Node
import ikpy.chain
from custom_msgs.msg import PointDictionary, IkResult, PointFiveElements
import time

motionstart = time.time()

pi = 22.0/7.0


# specifying the URDF file path
urdf_path = '/home/sdp19/sdp_ws/src/robot_description/urdf/braccio.urdf'

# loading the URDF file to create a chain
chain = ikpy.chain.Chain.from_urdf_file(urdf_path, active_links_mask=[False, True, True, True, True, True, False])

modelloadend = time.time()

print("URDF loading time is: ", modelloadend - motionstart)
class cal_ik(Node):

    def __init__(self):
    
        super().__init__('cal_ik')

        # creating a variable to publish to the angles topic
        self.publisher_ = self.create_publisher(IkResult, 'angles', 10)

        # creating a variable to subscribe to the coordinate_topic
        self.subscription = self.create_subscription(PointDictionary, 'coordinate_topic', self.sub_coordinate_callback, 10)
        self.subscription  

        motionend = time.time()


        print(f"Node startup time: {motionend - motionstart} seconds")
        print("starting iknew.py\n\n")


    def sub_coordinate_callback(self, msg):

        startT = time.time()

        result = IkResult()
        result.list_of_points = []
        result.list_of_strings = []
        result.list_of_directions = []

        
        for i in range(len(msg.keys)):
            x = msg.values[i].x
            y = msg.values[i].y
            z = msg.values[i].z

            if (z):
                result.list_of_directions.append("1")
            else:
                result.list_of_directions.append("0")


            key = msg.keys[i]

            print('Received from the transform node: \n%s (x = %f, y = %f, z = %f)' % (key, x, y, z))

            target_orientation = [0, 0, 1] 

            # calculating inverse kinematics for each point to find the servo motor angles
            inversestart = time.time()
            ik = chain.inverse_kinematics(target_position=[x, y, z], target_orientation = target_orientation, orientation_mode = "X")
            inverseend = time.time()
            
            print("inverse kinematics time is: ", inverseend - inversestart)
            
            M1 = round(ik[1] * (180.0/pi))
            M2 = round(ik[2] * (180.0/pi))
            M3 = round(ik[3] * (180.0/pi))
            M4 = round(ik[4] * (180.0/pi))
            


            angle_values = f"M1 = {M1:.2f}\nM2 = {M2:.2f}\nM3 = {M3:.2f}\nM4 = {M4:.2f}"

            servo_angles = PointFiveElements(element1 = M1, element2 = M2, element3 = M3, element4 = M4)
            
            result.list_of_points.append(servo_angles)
            result.list_of_strings.append(key)


        result.list_of_strings = msg.keys

        print("\n\n\n")
        print("Publishing to serial communication node: ")
        for key, point in zip(result.list_of_strings, result.list_of_points):
            print(f"Label: {key}")
            print(f"  M1: {point.element1}")
            print(f"  M2: {point.element2}")
            print(f"  M3: {point.element3}")
            print(f"  M4: {point.element4}")


        # publishing to the serial communication node
        self.publisher_.publish(result)
        endT = time.time()
        print("latency is: ", endT - startT)

        print('\n\n\n')







def main(args=None):
    rclpy.init(args=args)

    calulate_ik = cal_ik()

    rclpy.spin(calulate_ik)

    calulate_ik.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
