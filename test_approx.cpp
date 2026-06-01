#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/compressed_image.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <message_filters/subscriber.h>
#include <message_filters/synchronizer.h>
#include <message_filters/sync_policies/approximate_time.h>

void test() {
    typedef message_filters::sync_policies::ApproximateTime<sensor_msgs::msg::CompressedImage, nav_msgs::msg::Odometry> depthOdomSync;
    auto depthOdomSync_ = std::make_shared<message_filters::Synchronizer<depthOdomSync>>(depthOdomSync(100));
    depthOdomSync_->setMaxIntervalDuration(rclcpp::Duration::from_seconds(2.0));
}
