#include <cv_bridge/cv_bridge.h>
#include <sensor_msgs/msg/compressed_image.hpp>

void test(const sensor_msgs::msg::CompressedImage::ConstSharedPtr& img) {
    cv_bridge::CvImagePtr imgPtr = cv_bridge::toCvCopy(img);
    if (imgPtr->encoding == sensor_msgs::image_encodings::TYPE_32FC1) {
    }
}
