from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='classification',
            executable='classifyIm',  # replace with your actual node executable name
            name='classification_node'
        ),
        Node(
            package='transform',
            executable='point',  # replace with your actual node executable name
            name='transform_node'
        ),
        Node(
            package='motion_control',
            executable='cal_ik',  # replace with your actual node executable name
            name='motion_control_node'
        ),
        Node(
            package='communication',
            executable='serialcom',  # replace with your actual node executable name
            name='communication_node'
        ),
    ])

