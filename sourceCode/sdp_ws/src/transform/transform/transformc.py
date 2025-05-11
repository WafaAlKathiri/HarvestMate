from tf2_ros import Buffer, TransformListener
from custom_msgs.msg import PointDictionary
from geometry_msgs.msg import PointStamped
from geometry_msgs.msg import Point
from rclpy.node import Node
import tf2_geometry_msgs  
import threading
import pika
import json
import rclpy
import time

startTransform = time.time()
def load_reachability_matrices(files_info):
    matrices = {}
    for file_range, file_name in files_info.items():
        with open(file_name, 'r') as file:
            matrices[file_range] = json.load(file)
    return matrices


# specifying the reachability matrices paths
files_info = {
    (0.0, 13.5): "/home/sdp19/sdp_ws/src/transform/transform/reachability_matrix1.json",
    (14.0, 26.5): "/home/sdp19/sdp_ws/src/transform/transform/reachability_matrix2.json",
    (27.0, 30.0): "/home/sdp19/sdp_ws/src/transform/transform/reachability_matrix3.json"
}


# loading the reachability matrices
loaded_matrices = load_reachability_matrices(files_info)

found2 = False

# Creating a pointTransformer node
class PointTransformer(Node):
    def __init__(self):
        super().__init__('point_transformer')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)


        # creating a variable to publish to the coordinate_topic
        self.publisher_ = self.create_publisher(PointDictionary, 'coordinate_topic', 10)

        # creating a variable that will subscribe to the classificationResult topic
        self.subscription = self.create_subscription(PointDictionary, 'classificationResult', self.transform_callback, 10)
        self.subscription  # prevent unused variable warning

        EndTransform = time.time()


        print(f"Node startup time: {EndTransform - startTransform} seconds")
        print("In transform.py")
        print("\n\n\n")
        
        
    def transform_callback(self, msg):
        totalS = time.time()
        
        print("points in the camera frame: ")
        for key, value in zip(msg.keys, msg.values):
            print(f"{key}: (x={value.x}, y={value.y}, z={value.z})")



        pointsList = []
        point_msg = PointDictionary()
        point_to_search = []
        labels = []
        
        for i in range(len(msg.keys)):
            eachS = time.time()
            point_camera_frame = PointStamped()
            point_camera_frame.header.frame_id = "camera_optical"
            point_camera_frame.header.stamp = self.get_clock().now().to_msg()
            

            point_camera_frame.point.x = msg.values[i].x
            point_camera_frame.point.y = msg.values[i].y
            point_camera_frame.point.z = msg.values[i].z

            try:
                # Transform the point to the robotic_arm frame
                transform = self.tf_buffer.lookup_transform("robotic_arm",point_camera_frame.header.frame_id,rclpy.time.Time())

                point_robotic_arm_frame = tf2_geometry_msgs.do_transform_point(point_camera_frame, transform)

                point_to_search.append(point_robotic_arm_frame.point.x * 100)
                point_to_search.append(point_robotic_arm_frame.point.y * 100)
                point_to_search.append(point_robotic_arm_frame.point.z * 100)

                eachE2 = time.time()

                found, search_time = self.search_reachable_point(point_to_search, loaded_matrices)
                reachable_time2 = eachE2 - eachS

                print(f"Response time for the reachability check {i}: {reachable_time2} seconds")

                # checking if the point is reachable
                if (found):
                    print("Is Reachable")
                    labels.append(msg.keys[i])
                    point2 = Point(x=point_robotic_arm_frame.point.x , y=point_robotic_arm_frame.point.y, z=point_robotic_arm_frame.point.z)
                    pointsList.append(point2)

                else:
                    print("Isn't reachable")


            except Exception as e:
                self.get_logger().error(f"Failed to transform point: {str(e)}")

            

            eachE = time.time()
            reachable_time = eachE - eachS
            print(f"Response time for the Transform node for point {i}: {reachable_time} seconds")



            point_to_search = []

            print("\n\n") 

        point_msg.values = pointsList
        point_msg.keys = labels
            


        totalE = time.time()
        self.publisher_.publish(point_msg)
        totalE = time.time()
        print("latency is: ", totalE - totalS)
        print("\n")


        print("published to the motion_control node")
        print("points in the robotic arm frame: ")
        
        
        print("\n\n\n\n")
    

    def round_to_nearest_half(self, number):
        """Round a number to the nearest half."""
        return round(number * 2) / 2




    def search_reachable_point(self, point, matrices):
        start_time = time.time()
        """
        Search for a rounded point in the reachability matrices stored across multiple JSON files.

        Parameters:
            point (list): The (x, y, z) point to search for.
            files_info (dict): Information about which ranges are covered by which files.

        Returns:
            found (bool): Whether the point is in any matrix.
            elapsed_time (float): Time taken to perform the search, in seconds.
        """


        # Round the point coordinates to the nearest 0.5
        rounded_point = [self.round_to_nearest_half(coordinate) for coordinate in point]
        print("rounded point = ", rounded_point)

        # Determine which file to search based on the x-value
        for file_range, reach_mat in matrices.items():
            if file_range[0] <= rounded_point[0] <= file_range[1]:
                break
        else:
            print(f"No file covers the x-value {rounded_point[0]}")
            return False, 0
        

        # Search for the rounded point in the matrix
        found = rounded_point in reach_mat

        # Calculate the elapsed time
        elapsed_time = time.time() - start_time

        return found, elapsed_time
    
               

def main():
    rclpy.init()
    node = PointTransformer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()





