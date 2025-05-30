from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments = ['--x', '0.07', '--y', '0.395', '--z', '0.33', '--yaw', '1.57079632679', '--pitch', '0', '--roll', '0', '--frame-id', 'world', '--child-frame-id', 'robotic_arm']
        ),
        
        
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments = ['--x', '0', '--y', '0', '--z', '0.515', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'world', '--child-frame-id', 'camera_RGB']
        ),
        
        
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments = ['--x', '0', '--y', '0', '--z', '0', '--yaw', '0', '--pitch', '0', '--roll', '-1.57079632679', '--frame-id', 'camera_RGB', '--child-frame-id', 'camera_optical']
        ),
        
    ])
