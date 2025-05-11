
import numpy as np
import time
import ikpy.chain


# calculating the time needed to check if a point is reachable or not utilizing the inverse and forward kinematics
urdf_path = '/home/sdp19/sdp_ws/src/robot_description/urdf/braccio.urdf'


# Load the chain from the URDF file
chain = ikpy.chain.Chain.from_urdf_file(urdf_path,
                                        active_links_mask=[False, True, True, True, True, True, False])



target_orientation = np.array([0, 0, 1])  # Convert list to NumPy array
target_orientation = target_orientation / np.linalg.norm(target_orientation)

target_position = [17.0, 13.1, 6.2]
# Convert from cm to m
target_position_m = [coordinate * 0.01 for coordinate in target_position]

start_time = time.time()

try:
    joint_angles = chain.inverse_kinematics(target_position=target_position_m,
                                            target_orientation=target_orientation,
                                            orientation_mode="X")
    fk_result = chain.forward_kinematics(joint_angles)
    fk_position = fk_result[:3, 3]

    difference_vector = np.array(fk_position) - np.array(target_position_m)
    difference_norm = np.linalg.norm(difference_vector)

    if difference_norm < 0.01:
        print("Point is reachable : ", target_position )

except Exception as e:
    print(f"Error for target {target_position}: {e}")

# Calculate the elapsed time
elapsed_time = time.time() - start_time

print("Time it took calculate reachability for individual point  : ", elapsed_time)