import json
import time


# calculating the time needed to check if a point is reachable or not utilizing reachability matrix


# Load the JSON files and save their contents into variables
def load_reachability_matrices(files_info):
    matrices = {}
    for file_range, file_name in files_info.items():
        with open(file_name, 'r') as file:
            matrices[file_range] = json.load(file)
    return matrices

files_info = {
    (0.0, 13.5): "/home/sdp19/sdp_ws/src/transform/transform/reachability_matrix1.json",
    (14.0, 26.5): "/home/sdp19/sdp_ws/src/transform/transform/reachability_matrix2.json",
    (27.0, 30.0): "/home/sdp19/sdp_ws/src/transform/transform/reachability_matrix3.json"
}

# Load all matrices
loaded_matrices = load_reachability_matrices(files_info)

def round_to_nearest_half(number):
    """Round a number to the nearest half."""
    return round(number * 2) / 2

def search_reachable_point(point, matrices):
    """
    Search for a rounded point in the preloaded reachability matrices.

    Parameters:
        point (list): The (x, y, z) point to search for.
        matrices (dict): The preloaded reachability matrices, keyed by their x-value ranges.

    Returns:
        found (bool): Whether the point is in any matrix.
        elapsed_time (float): Time taken to perform the search, in seconds.
    """
    # Record the start time (here for search time)
    start_time = time.time()

    # Round the point coordinates to the nearest 0.5
    rounded_point = [round_to_nearest_half(coordinate) for coordinate in point]

    # Determine which matrix to search based on the x-value
    for file_range, reach_mat in matrices.items():
        if file_range[0] <= rounded_point[0] <= file_range[1]:
            break
    else:
        print(f"No matrix covers the x-value {rounded_point[0]}")
        return False, 0

    # Search for the rounded point in the matrix
    found = rounded_point in reach_mat

    # Calculate the elapsed time
    elapsed_time = time.time() - start_time

    return found, elapsed_time

point_to_search = [17.0, 13.1, 6.2]   # Example point

found, search_time = search_reachable_point(point_to_search, loaded_matrices)

if found:
    print(f"Point {point_to_search} (rounded) is reachable. Search time: {search_time:.6f} seconds.")
else:
    print(f"Point {point_to_search} (rounded) is not reachable. Search time: {search_time:.6f} seconds.")
