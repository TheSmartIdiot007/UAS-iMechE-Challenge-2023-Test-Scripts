#!/bin/bash
cd ~/ardupilot/ArduCopter/ && sim_vehicle.py -v ArduCopter -f gazebo-iris --console
# gnome-terminal --tab
# gnome-terminal --tab -e cd ~/ && gazebo --verbose worlds/iris_arducopter_runway.world
# gnome-terminal --tab -e cd ~/ardupilot/ArduCopter/ && sim_vehicle.py -v ArduCopter -f gazebo-iris --console --tab -e cd ~/ && gazebo --verbose worlds/iris_arducopter_runway.world