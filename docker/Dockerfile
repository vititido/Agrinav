# syntax=docker/dockerfile:1
#
# Stages:
#   base  ROS 2 Jazzy, Gazebo Harmonic and every rosdep key of the workspace,
#         with the workspace built.
#   dev   base plus lint and test tools.
#
# Behind a TLS-inspecting proxy, pass its CA bundle as a build secret so
# rosdep can reach GitHub:  docker build --secret id=ca_bundle,src=ca.crt ...

ARG ROS_DISTRO=jazzy

FROM osrf/ros:${ROS_DISTRO}-desktop-full AS base
ARG ROS_DISTRO
ENV ROS_DISTRO=${ROS_DISTRO} \
    WS=/ws \
    DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR ${WS}

# Manifests first, so the dependency layer is reused until a package.xml changes.
COPY src/agrinav_description/package.xml src/agrinav_description/
COPY src/agrinav_gazebo/package.xml src/agrinav_gazebo/
COPY src/agrinav_bringup/package.xml src/agrinav_bringup/
RUN --mount=type=secret,id=ca_bundle,required=false \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    if [ -f /run/secrets/ca_bundle ]; then export SSL_CERT_FILE=/run/secrets/ca_bundle; fi \
    && apt-get update \
    && rosdep update --rosdistro "${ROS_DISTRO}" \
    && rosdep install --from-paths src --ignore-src -y --rosdistro "${ROS_DISTRO}"

COPY src src
RUN source "/opt/ros/${ROS_DISTRO}/setup.bash" \
    && colcon build --symlink-install --event-handlers console_direct-

COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]

FROM base AS dev
RUN --mount=type=secret,id=ca_bundle,required=false \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    if [ -f /run/secrets/ca_bundle ]; then export PIP_CERT=/run/secrets/ca_bundle; fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3-venv libxml2-utils \
    && python3 -m venv /opt/devtools \
    && /opt/devtools/bin/pip install --no-cache-dir ruff==0.17.6 pre-commit \
    && ln -s /opt/devtools/bin/ruff /opt/devtools/bin/pre-commit /usr/local/bin/
