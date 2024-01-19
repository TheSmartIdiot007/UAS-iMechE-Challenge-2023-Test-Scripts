#!/usr/bin/env python2
import numpy as np
import rospy
# from std_msgs.msg import String, Float64
# from sensor_msgs.msg import *
from mavros_msgs.srv import *
from mavros_msgs.msg import *
# from geometry_msgs.msg import *



class WP_Parameters:

    def __init__(self):
        self.wp =Waypoint()

        #SERVICES
        # self.arm_service = rospy.ServiceProxy('/mavros/cmd/arming', CommandBool)
        # self.takeoff_service = rospy.ServiceProxy('/mavros/cmd/takeoff', CommandTOL)
        # self.land_service = rospy.ServiceProxy('/mavros/cmd/land', CommandTOL)
        # self.flight_mode_service = rospy.ServiceProxy('/mavros/set_mode', SetMode)
        self.waypoint_push = rospy.ServiceProxy('/mavros/mission/push', WaypointPush)
        self.waypoint_curr = rospy.ServiceProxy('/mavros/mission/set_current', WaypointSetCurrent)
        self.waypoint_clear = rospy.ServiceProxy('/mavros/mission/clear', WaypointClear)
        self.waypoint_pull = rospy.ServiceProxy('/mavros/mission/pull', WaypointPull)
        self.waypoint_set_current = rospy.ServiceProxy('/mavros/mission/set_current', WaypointSetCurrent)
        
    def setWaypoints(self,frame,command,is_current,autocontinue,param1,param2,param3,param4,x_lat,y_long,z_alt):
        self.wp.frame =frame #  FRAME_GLOBAL_REL_ALT = 3 for more visit http://docs.ros.og/api/mavros_msgs/html/msg/Waypoint.html
        self.wp.command = command #VTOL TAKEOFF = 84,NAV_WAYPOINT = 16, TAKE_OFF=22 for checking out other parameters go to https://github.com/mavlink/mavros/blob/master/mavros_msgs/msg/CommandCode.msg'''
        self.wp.is_current= is_current
        self.wp.autocontinue = autocontinue # enable taking and following upcoming waypoints automatically 
        self.wp.param1=param1 # To know more about these params, visit https://mavlink.io/en/messages/common.html#MAV_CMD_NAV_WAYPOINT
        self.wp.param2=param2
        self.wp.param3=param3
        self.wp.param4=param4
        self.wp.x_lat= x_lat 
        self.wp.y_long=y_long
        self.wp.z_alt= z_alt #relative altitude.

        return self.wp
    
    def wpPush(self,wps):
        # Call /mavros/mission/push to push the waypoints
        # and print fail message on failure
        rospy.wait_for_service('/mavros/mission/push')
        try:
            self.waypoint_push(0, wps)
            rospy.loginfo("Waypoint pushed")

        except:
            print ("Service waypoint push call failed")

    def wpClear(self):
        rospy.wait_for_service('mavros/mission/clear')
        try:
            self.waypoint_clear()
            rospy.loginfo("Waypoints cleared")
        except:
            print("Waypoint clear failed")

    def wpList(self):
        rospy.wait_for_service('mavros/mission/pull')
        try:
            self.waypoint_pull()
        except:
            print("Waypoint pull failed")

    def wpReindex(self, index):
        rospy.wait_for_service('mavros/mission/set_current')
        try:
            self.waypoint_set_current(index)
            rospy.loginfo("Index set to 0")
        except:
            print("Index reset failed")
