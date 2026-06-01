from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Declare the launch argument
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    
    use_pose_model_arg = DeclareLaunchArgument(
        'use_pose_model',
        default_value='false',
        description='Use pose model weights if true, otherwise use det weights'
    )
    
    use_nano_arg = DeclareLaunchArgument(
        'use_nano',
        default_value='true',
        description='Use Nano (.engine) weights if true, otherwise use .pt'
    )
    
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_pose_model = LaunchConfiguration('use_pose_model')
    use_nano = LaunchConfiguration('use_nano')

    # Define the path to the YAML parameter file
    dynamic_detector_param_path = os.path.join(
        get_package_share_directory('onboard_detector'),
        'cfg',
        'dynamic_detector_param.yaml'
    )

    yolo_detector_param_path = os.path.join(
        get_package_share_directory('onboard_detector'),
        'cfg',
        'yolo_detector_param.yaml'
    )

    # Create the node with the parameter file
    dynamic_detector_node = Node(
        package='onboard_detector',
        executable='dynamic_detector_node',
        name='dynamic_detector_node',
        output='screen',
        parameters=[dynamic_detector_param_path, {'use_sim_time': use_sim_time}]
    )

    # Create the yolo node
    yolo_detector_node = Node(
        package='onboard_detector',
        executable='yolo_detector_node.py',  
        name='yolo_detector_node',      
        output='screen',
        parameters=[yolo_detector_param_path, {
            'use_sim_time': use_sim_time, 
            'use_pose_model': use_pose_model,
            'use_nano': use_nano
        }]
    )

    return LaunchDescription([
        use_sim_time_arg,
        use_pose_model_arg,
        use_nano_arg,
        dynamic_detector_node,
        yolo_detector_node
    ])