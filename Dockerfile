# ROS Noetic + Gazebo Classic 11 + lar_gazebo (branch noetic) + apriltag_ros
FROM osrf/ros:noetic-desktop-full

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    ROS_DISTRO=noetic

RUN apt-get update && apt-get install -y --no-install-recommends \
        git ca-certificates build-essential bash-completion imagemagick mesa-utils \
        python3-catkin-tools python3-rosdep python3-numpy \
        ros-noetic-husky-simulator ros-noetic-husky-desktop ros-noetic-husky-viz \
        ros-noetic-hector-slam ros-noetic-teleop-twist-keyboard \
        ros-noetic-realsense2-description \
        ros-noetic-apriltag-ros ros-noetic-rqt-image-view \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws

# 1) lar_gazebo (mesmo procedimento do README: clone -b noetic + rosdep + catkin build)
ARG LAR_GAZEBO_REF=noetic
RUN mkdir -p src && \
    git clone --depth 1 -b ${LAR_GAZEBO_REF} https://github.com/lar-deeufba/lar_gazebo.git src/lar_gazebo

# 2) pacote desta solucao (tag no robo + camera + deteccao + localizacao)
COPY lar_apriltag src/lar_apriltag
RUN chmod +x src/lar_apriltag/scripts/*.py

# 3) textura da AprilTag (tag36h11, id 0) -> material do Gazebo
#    Ampliacao por multiplo inteiro (pixel replication) para manter as celulas nitidas.
RUN git clone --depth 1 https://github.com/AprilRobotics/apriltag-imgs.git /tmp/apriltag-imgs && \
    echo "Tamanho da imagem original: $(identify -format %wx%h /tmp/apriltag-imgs/tag36h11/tag36_11_00000.png)" && \
    mkdir -p /usr/share/gazebo-11/media/materials/textures /usr/share/gazebo-11/media/materials/scripts && \
    convert /tmp/apriltag-imgs/tag36h11/tag36_11_00000.png -scale 10000% \
        /usr/share/gazebo-11/media/materials/textures/lar_tag36_11_00000.png && \
    cp src/lar_apriltag/media/materials/scripts/lar_apriltag.material \
        /usr/share/gazebo-11/media/materials/scripts/ && \
    rm -rf /tmp/apriltag-imgs

# 4) dependencias + build
RUN (rosdep init 2>/dev/null || true) && rosdep update --rosdistro noetic && \
    . /opt/ros/noetic/setup.sh && \
    rosdep install --from-paths src --ignore-src -r -y --rosdistro noetic && \
    catkin init && catkin build

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && echo "source /entrypoint.sh true" >> /root/.bashrc

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
