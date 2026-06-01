/*
	FILE: detector_node.cpp
	--------------------------
	Run detector node
*/
#include <rclcpp/rclcpp.hpp>
#include <onboard_detector/dynamicDetector.h>

int main(int argc, char* argv[]){
    rclcpp::init(argc, argv);
    rclcpp::NodeOptions options;
    std::shared_ptr<onboardDetector::dynamicDetector> detector = std::make_shared<onboardDetector::dynamicDetector>(options);
    rclcpp::spin(detector);
    rclcpp::shutdown();
    return 0;
}