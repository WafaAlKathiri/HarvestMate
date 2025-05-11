# HarvestMate

Robotics and Artificial intelligence are becoming substantial tools in shaping the future of agriculture and addressing its challenges. Empowering small-scale agriculture, this project tackles the inefficiency and wastage in fruit harvesting for small-scale growers. They lack expertise, time, and rely on manual methods, resulting in suboptimal harvests, significant agricultural waste, and huge profit loss. Existing solutions designed for large farms are costly and inaccessible to smaller growers. HarvestMate bridges the gap between manual methods and large-scale solutions by providing accessible technology that is user-friendly and costeffective. The project integrates a robotic arm with machine learning models that detect and classify fruit ripeness using colored images. A camera captures fruit data, and the deep learning models determine the fruit type and its ripeness. The robotic arm picks and sorts fruits into designated areas for ripe and rotten fruits. The project’s performance measures include increased fruit yield, reduced post-harvest losses, and improved profitability for small-scale growers, contributing to a more sustainable and efficient agricultural sector. 

# Hardware Design 

The images below presents the hardware setup of the project : 

![Hardware Desgin](imagesREADME/hw.png)

# Software flowcharts 




At the start, the pipeline and nodes are initialized and the RGB and depth frames of the camera are aligned. After that, when the camera is activated, it will start capturing frames, which will be processed for initial enhancement using the OpenCV library. These refined frames will then be passed to the YOLO V7 object detection algorithm, which will identify whether the objects in the frames are apples or oranges. The identified objects will be sent to the DepthAI library to compute the X, Y, Z coordinates. Following this, images of the fruits with calculated coordinates will be sent to the classification model that utilizes TensorFlow and Keras libraries to classify them as ripe, rotten, or unripe and save them in a list. The list is then filtered to keep the coordinates of ripe and rotten fruits only. Subsequently, coordinate transformation will be applied using ROS 2 to find all coordinates relative to the base of the robotic arm. Each coordinate will then be passed to a function to check if it is reachable or not. Once reachability of all points has been determined, inverse kinematics will be computed for all coordinates using the IKPY library, and the resulting data will be transmitted to the Arduino microcontroller via serial communication using the pySerial library for further processing and utilization.  

