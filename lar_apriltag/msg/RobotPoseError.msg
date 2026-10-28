# Pose do robo estimada pela AprilTag (frame world) e erro em relacao ao ground truth do Gazebo.
# Erro = estimado - ground truth. Angulos em radianos. Sem ground truth: campos gt_* e error_* = NaN.
std_msgs/Header header
float64 x
float64 y
float64 z
float64 yaw
float64 gt_x
float64 gt_y
float64 gt_z
float64 gt_yaw
float64 error_x
float64 error_y
float64 error_z
float64 error_yaw
float64 error_position   # norma do erro em xy (m)
bool has_ground_truth
