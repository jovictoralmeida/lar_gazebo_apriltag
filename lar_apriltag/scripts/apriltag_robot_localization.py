#!/usr/bin/env python3
"""Estima a pose do robo no mundo a partir da AprilTag vista pela camera fixa.

  T_world_base = T_world_tag(detectada) * Rz(correcao) * inv(T_base_apriltag_link)

Publica (namespace do no, ex.: /apriltag_robot_localization/):
  pose                 geometry_msgs/PoseStamped   pose estimada no frame world
  estimate             lar_apriltag/RobotPoseError x, y, z, yaw estimados + ground truth + erros
  path                 nav_msgs/Path               trajetoria estimada (frame world)
  path_ground_truth    nav_msgs/Path               trajetoria real (/gazebo/model_states)
Erro = estimado - ground truth; yaw em radianos, erro de yaw normalizado em [-pi, pi].
"""
import math
import numpy as np
import rospy
import tf2_ros
from tf import transformations as tft
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from gazebo_msgs.msg import ModelStates
from lar_apriltag.msg import RobotPoseError

NAN = float("nan")


def to_matrix(ts):
    t, q = ts.transform.translation, ts.transform.rotation
    m = tft.quaternion_matrix([q.x, q.y, q.z, q.w])
    m[:3, 3] = [t.x, t.y, t.z]
    return m


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class Localizer:
    def __init__(self):
        gp = rospy.get_param
        self.world = gp("~world_frame", "world")
        self.tag = gp("~tag_frame", "tag_detected")
        self.base = gp("~robot_frame", "base_link")
        self.mount = gp("~mount_frame", "apriltag_link")
        self.yaw_corr = float(gp("~tag_yaw_correction", 0.0))
        self.timeout = float(gp("~detection_timeout", 0.5))
        self.min_dist = float(gp("~path_min_distance", 0.02))      # m
        self.min_yaw = math.radians(float(gp("~path_min_yaw_deg", 2.0)))
        self.max_points = int(gp("~path_max_points", 5000))
        self.model_name = gp("~model_name", "husky")
        self.warned_name = False

        self.buf = tf2_ros.Buffer(cache_time=rospy.Duration(10.0))
        self.listener = tf2_ros.TransformListener(self.buf)

        self.pub_pose = rospy.Publisher("~pose", PoseStamped, queue_size=10)
        self.pub_est = rospy.Publisher("~estimate", RobotPoseError, queue_size=10)
        self.pub_path = rospy.Publisher("~path", Path, queue_size=1, latch=True)
        self.pub_gt_path = rospy.Publisher("~path_ground_truth", Path, queue_size=1, latch=True)

        self.path = Path()
        self.path.header.frame_id = self.world
        self.gt_path = Path()
        self.gt_path.header.frame_id = self.world
        self.last_added = None   # (x, y, yaw) do ultimo ponto da trajetoria

        self.gt = None           # (x, y, z, yaw, Pose)
        rospy.Subscriber("/gazebo/model_states", ModelStates, self.gt_cb, queue_size=1)
        rospy.Timer(rospy.Duration(1.0 / float(gp("~rate", 30.0))), self.step)

    def gt_cb(self, msg):
        if self.model_name not in msg.name:
            if not self.warned_name:
                rospy.logwarn("Modelo '%s' nao encontrado em /gazebo/model_states. Modelos: %s "
                              "(use _model_name:=<nome>)", self.model_name, list(msg.name))
                self.warned_name = True
            return
        pose = msg.pose[msg.name.index(self.model_name)]
        p, q = pose.position, pose.orientation
        yaw = tft.euler_from_quaternion([q.x, q.y, q.z, q.w])[2]
        self.gt = (p.x, p.y, p.z, yaw, pose)

    def _append_path(self, stamp, est_pose):
        ps = PoseStamped()
        ps.header.stamp, ps.header.frame_id = stamp, self.world
        ps.pose = est_pose
        self.path.poses.append(ps)
        del self.path.poses[:-self.max_points]
        self.path.header.stamp = stamp
        self.pub_path.publish(self.path)

        if self.gt is not None:
            gs = PoseStamped()
            gs.header.stamp, gs.header.frame_id = stamp, self.world
            gs.pose = self.gt[4]
            self.gt_path.poses.append(gs)
            del self.gt_path.poses[:-self.max_points]
            self.gt_path.header.stamp = stamp
            self.pub_gt_path.publish(self.gt_path)

    def step(self, _):
        try:
            t_wt = self.buf.lookup_transform(self.world, self.tag, rospy.Time(0))
            t_bm = self.buf.lookup_transform(self.base, self.mount, rospy.Time(0))
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException):
            return

        age = (rospy.Time.now() - t_wt.header.stamp).to_sec()
        if age > self.timeout:
            rospy.logwarn_throttle(2.0, "Tag nao detectada ha %.1f s", age)
            return

        rz = tft.rotation_matrix(self.yaw_corr, (0, 0, 1))
        t_wb = to_matrix(t_wt).dot(rz).dot(np.linalg.inv(to_matrix(t_bm)))
        q = tft.quaternion_from_matrix(t_wb)
        x, y, z = t_wb[0, 3], t_wb[1, 3], t_wb[2, 3]
        yaw = tft.euler_from_quaternion(q)[2]
        stamp = t_wt.header.stamp

        # pose estimada
        msg = PoseStamped()
        msg.header.stamp, msg.header.frame_id = stamp, self.world
        msg.pose.position.x, msg.pose.position.y, msg.pose.position.z = x, y, z
        (msg.pose.orientation.x, msg.pose.orientation.y,
         msg.pose.orientation.z, msg.pose.orientation.w) = q
        self.pub_pose.publish(msg)

        # estimativa + erro
        est = RobotPoseError()
        est.header.stamp, est.header.frame_id = stamp, self.world
        est.x, est.y, est.z, est.yaw = x, y, z, yaw
        if self.gt is not None:
            gx, gy, gz, gyaw = self.gt[:4]
            est.has_ground_truth = True
            est.gt_x, est.gt_y, est.gt_z, est.gt_yaw = gx, gy, gz, gyaw
            est.error_x, est.error_y, est.error_z = x - gx, y - gy, z - gz
            est.error_yaw = wrap(yaw - gyaw)
            est.error_position = math.hypot(x - gx, y - gy)
            rospy.loginfo_throttle(
                1.0, "est=(%.3f, %.3f, %.3f, %.1f deg)  erro: pos_xy=%.3f m  z=%.3f m  yaw=%.1f deg",
                x, y, z, math.degrees(yaw), est.error_position, est.error_z,
                math.degrees(est.error_yaw))
        else:
            est.has_ground_truth = False
            (est.gt_x, est.gt_y, est.gt_z, est.gt_yaw, est.error_x, est.error_y,
             est.error_z, est.error_yaw, est.error_position) = [NAN] * 9
            rospy.loginfo_throttle(1.0, "est=(%.3f, %.3f, %.3f, %.1f deg)  (sem ground truth)",
                                   x, y, z, math.degrees(yaw))
        self.pub_est.publish(est)

        # trajetoria (so adiciona ponto se o robo se moveu)
        moved = (self.last_added is None or
                 math.hypot(x - self.last_added[0], y - self.last_added[1]) >= self.min_dist or
                 abs(wrap(yaw - self.last_added[2])) >= self.min_yaw)
        if moved:
            self.last_added = (x, y, yaw)
            self._append_path(stamp, msg.pose)


if __name__ == "__main__":
    rospy.init_node("apriltag_robot_localization")
    Localizer()
    rospy.spin()
