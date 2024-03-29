#!/usr/bin/env python2
from cmath import sqrt
import numpy as np
import rospy
import time
from std_msgs.msg import String, Float64
from sensor_msgs.msg import *
from mavros_msgs.srv import *
from mavros_msgs.msg import *
from geometry_msgs.msg import *
import math
from time import sleep
from tf.transformations import euler_from_quaternion
# from wp_params import WP_Parameters
ARM_RAD=1
DEADBAND_WIDTH = 0.2
#Variables
d_s = 10 #start distance
d_p = 20 #pilon distance
d = 2 #drone width
v_d = 20 #max velocity

x_init = -8.66
y_init = 5

class stateMoniter:
    def __init__(self):
        self.state = State()
        # Instantiate a setpoints message
        
    def stateCb(self, msg):
        # Callback function for topic /mavros/state
        self.state = msg

class wpMissionCnt:

    def __init__(self):
        self.wp =Waypoint()
        
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
        self.home = []
        self.battery_coeff = 0.11

        return self.wp

class FLIGHT_CONTROLLER:

    def __init__(self):
        self.pt = Point()
        self.orient = Quaternion()
        self.angles = Point()
        self.gps = Point()
        stateMt = stateMoniter()
        self.reached_index=0 
        self.transformation_matrix = np.array([[0, -1, 0], [1,0,0], [0,0,1]])
        self.wps11 = [0]*3
        self.wps22 = [0]*2
        self.wp_g = [0]*2
        #NODE
        rospy.init_node('iris_drone', anonymous = True)

        #SUBSCRIBERS
        self.get_pose_subscriber = rospy.Subscriber('/mavros/local_position/pose', PoseStamped, self.get_pose)
        # self.get_linear_vel=rospy.Subscriber('/mavros/local_position/velocity_local', TwistStamped, self.get_vel,)
        # self.get_imu_data=rospy.Subscriber('/mavros/imu/data',Imu,self.get_euler_angles)
        self.get_gps_location = rospy.Subscriber('/mavros/global_position/global', NavSatFix, self.get_gps)
        self.state_subsciber = rospy.Subscriber('/mavros/state',State, stateMt.stateCb)
        rospy.Subscriber("/mavros/local_position/local",PoseStamped, self.get_yaw)
        self.wpReached = rospy.Subscriber("/mavros/mission/reached", WaypointReached, self.wpreach)
        rospy.Subscriber('/mavros/battery', BatteryState, self.get_battery_status)
        

        #PUBLISHERS
        self.publish_pose = rospy.Publisher('/mavros/setpoint_position/local', PoseStamped,queue_size=10)
        self.publish_attitude_thrust=rospy.Publisher('/mavros/setpoint_raw/attitude', AttitudeTarget,queue_size=0)

        #SERVICES
        self.arm_service = rospy.ServiceProxy('/mavros/cmd/arming', CommandBool)
        self.takeoff_service = rospy.ServiceProxy('/mavros/cmd/takeoff', CommandTOL)
        self.land_service = rospy.ServiceProxy('/mavros/cmd/land', CommandTOL)
        self.flight_mode_service = rospy.ServiceProxy('/mavros/set_mode', SetMode)
        self.waypoint_push = rospy.ServiceProxy('/mavros/mission/push', WaypointPush)
        self.waypoint_curr = rospy.ServiceProxy('/mavros/mission/set_current', WaypointSetCurrent)
        self.waypoint_clear = rospy.ServiceProxy('/mavros/mission/clear', WaypointClear)
        self.waypoint_pull = rospy.ServiceProxy('/mavros/mission/pull', WaypointPull)
        self.waypoint_set_current = rospy.ServiceProxy('/mavros/mission/set_current', WaypointSetCurrent)

        rospy.loginfo('INIT')

        self.pt.x = 2
        self.pt.y = 2
        self.pt.z = 2

    #MODE SETUP

    def toggle_arm(self, arm_bool):
        rospy.wait_for_service('/mavros/cmd/arming')
        try:
            self.arm_service(arm_bool)
        
        except rospy.ServiceException as e:
            rospy.loginfo("Service call failed: " %e)


    def land(self, l_alt):

        # self.gps_subscriber

        # l_lat = self.gps_lat
        # l_long = self.gps_long

        rospy.wait_for_service('/mavros/cmd/land')
        try:
            self.land_service(0.0, 0.0, 0, 0, l_alt)
            rospy.loginfo("LANDING")

        except rospy.ServiceException as e:
            rospy.loginfo("Service call failed: " %e)


    def land(self, l_alt):

        # self.gps_subscriber

        # l_lat = self.gps_lat
        # l_long = self.gps_long

        rospy.wait_for_service('/mavros/cmd/land')
        try:
            self.land_service(0.0, 0.0, 0, 0, l_alt)
            rospy.loginfo("LANDING")

        except rospy.ServiceException as e:
            rospy.loginfo("Service call failed: " %e)


    def set_mode(self,md):

        rospy.wait_for_service('/mavros/set_mode')
        try:
            self.flight_mode_service(0, md)
            rospy.loginfo("Mode changed")
                
        except rospy.ServiceException as e:
            rospy.loginfo("Mode could not be set: " %e)


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



    def set_Guided_mode(self):
        
        rate=rospy.Rate(20)
        #print('OFF')
        PS = PoseStamped()

        PS.pose.position.x = 0
        PS.pose.position.y = 0
        PS.pose.position.z = 0
        
        for i in range(10):
            self.publish_pose.publish(PS)
            
            rate.sleep()
        print('done')
        self.set_mode("GUIDED")

    def set_Altitude_Hold_mode(self):

        rate=rospy.Rate(20)
        #print('OFF')
        PS = PoseStamped()

        PS.pose.position.x = 0
        PS.pose.position.y = 0
        PS.pose.position.z = 0
        
        for i in range(10):
            self.publish_pose.publish(PS)
            
            rate.sleep()
        print('done')
        self.set_mode("ALT_HOLD")	

    #CALLBACKS

    def get_gps(self, data):
        self.gps.x = data.latitude
        self.gps.y = data.longitude
        self.gps.z = data.altitude


    def get_pose(self, location_data):
        self.pt.x = location_data.pose.position.x
        self.pt.y = location_data.pose.position.y
        self.pt.z = location_data.pose.position.z

        # orientation in space  
        self.orient.x = location_data.pose.orientation.x
        self.orient.y = location_data.pose.orientation.y
        self.orient.z = location_data.pose.orientation.z
        self.orient.w = location_data.pose.orientation.w

    def within_rad(self):
        if (((self.pt.x)**2 + (self.pt.y)**2 + (self.pt.z)**2) < (ARM_RAD)**2):
            return True
        print((self.pt.x)**2 + (self.pt.y)**2 + (self.pt.z)**2)
        return False

    def wpreach(self, data):
        self.reached_index = data.wp_seq

    def get_battery_status(self, data):
        self.bat_percentage = data.percentage
        self.curr = data.current
        self.volt = data.voltage


# this function rotates the coordinates considering the spawn point and direction as the origin
    def rotate(self, point):
        angle = self.angles.z - math.pi/2
        px, py = point[0], point[1]
        nx =  math.cos(angle) * px  - math.sin(angle) * py 
        ny =  math.sin(angle) * px  + math.cos(angle) * py 
        return [nx, ny, point[2]]
        
    def get_eulers(self,q):
        eulers = euler_from_quaternion(q)
        return eulers[2]

    def get_yaw(self, data):
        q = []
        q.append(data.pose.pose.orientation.x)
        q.append(data.pose.pose.orientation.y)
        q.append(data.pose.pose.orientation.z)
        q.append(data.pose.pose.orientation.w)
        angle  = self.get_eulers(q)
        self.angles.x = 0.0
        self.angles.y = 0.0
        self.angles.z = angle
        print(angle)

        
# this function corrects the frame offset converting the ardupilot frame (x-right, y-front) to 
# gazebo local frame (x-front, y-left)
    def corrected_pose(self, current_pos):
        current_pos = np.array(current_pos)
        new_pos = np.matmul(self.transformation_matrix,current_pos)
        return list(new_pos)


    #PUBLISHERS
    def gotopose(self,x,y,z):
        rate = rospy.Rate(20)
        sp = PoseStamped()
        given_position = np.array([x,y,z])
        x = given_position[0]
        y = given_position[1]
        z = given_position[2]
        sp.pose.position.x = x
        sp.pose.position.y = y
        sp.pose.position.z = z

        ix = self.orient.x
        iy = self.orient.y
        iz = self.orient.z
        iw = self.orient.w

        sp.pose.orientation.x = ix
        sp.pose.orientation.y = iy
        sp.pose.orientation.z = iz
        sp.pose.orientation.w = iw


        dist = np.sqrt(((self.pt.x-x)**2) + ((self.pt.y-y)**2) + ((self.pt.z-z)**2))
        while(dist > DEADBAND_WIDTH):
            self.publish_pose.publish(sp)
            dist = np.sqrt(((self.pt.x-x)**2) + ((self.pt.y-y)**2) + ((self.pt.z-z)**2))
            rate.sleep()
        print('Reached')



    # helper functions for xy to latlon conversions
    def mdeglon(self, lat0):
        lat0rad = math.radians(lat0)
        return (111415.13 * math.cos(lat0rad)- 94.55 * math.cos(3.0*lat0rad)- 0.12 * math.cos(5.0*lat0rad) )

    def mdeglat(self, lat0):
        lat0rad = math.radians(lat0)
        return (111132.09 - 566.05 * math.cos(2.0*lat0rad)+ 1.20 * math.cos(4.0*lat0rad)- 0.002 * math.cos(6.0*lat0rad) )

    # xy to latlon conversions

    def xy2latlon(self, local, origin):
        lon = local[0]/self.mdeglon(origin[0]) + origin[1]
        lat = local[1]/self.mdeglat(origin[1]) + origin[0]
        alt = local[2] + origin[2]
        gl = np.array([lat, lon, alt])
        return gl

    def latlon2xy(self, coordinates, origin):
        x = (coordinates[1]- origin[1]) + self.mdeglon(origin[0])
        y = (coordinates[0] - origin[0]) + self.mdeglat(origin[0])
        return x,y
    
    def Lets_Begin(self):
        print("Lets Start")
        n = int(input("No. of Points:"))


    def Mission_1(self):
            # wayp_16_l = wpMissionCnt()
            
            # defining the origin as the gps coordinates of the spawn point
            origin = [self.gps.x, self.gps.y, 0]
            self.home = origin
            
            wp0 = [0, 0, 5]
            wp1 = [0, 40, 1]
            # wp2 = [-25, 50, 5]
            # wp3 = [25, 50, 5]
            # wp4 = [25, 0, 5]
            # wp5 = [0, 0, 5]
            # extracting latitude and longitude from given x,y,z coordinates 
            # wp_g = [0]*6
            self.wp_g[0] = self.xy2latlon(wp0, origin)
            self.wp_g[1] = self.xy2latlon(wp1, origin)
            # self.wp_g[2] = self.xy2latlon(wp2,origin)
            # self.wp_g[3] = self.xy2latlon(wp3,origin)
            # self.wp_g[4] = self.xy2latlon(wp4,origin)
            # self.wp_g[5] = self.xy2latlon(wp5,origin)

            for i in range(len(self.wps11)):
                self.wps11[i]=wpMissionCnt()

            for j in range(1, len(self.wps11)):
                self.wps11[j].frame = 3
                self.wps11[j].command = 16
                self.wps11[j].is_current = False
                self.wps11[j].autocontinue = True
                self.wps11[j].param1 = 0.0
                self.wps11[j].param2 = 0.0
                self.wps11[j].param3 = 0.0
                self.wps11[j].param4 = float('nan')
                self.wps11[j].x_lat = self.wp_g[j-1][0]
                self.wps11[j].y_long = self.wp_g[j-1][1]
                self.wps11[j].z_alt = self.wp_g[j-1][2]

            self.wps11[0] = self.wps11[1]
            self.wps11[-1].command = 21

            wps = self.wps11
            return wps
    

    def Mission_2(self):
        # go to home mission
        
        self.wps22[1].frame = 3
        self.wps22[1].command = 16
        self.wps22[1].is_current = False
        self.wps22[1].autocontinue = True
        self.wps22[1].param1 = 0.0
        self.wps22[1].param2 = 0.0
        self.wps22[1].param3 = 0.0
        self.wps22[1].param4 = float('nan')
        self.wps22[1].x_lat = self.home[0]
        self.wps22[1].y_long = self.home[1]
        self.wps22[1].z_alt = self.home[2]
        
        self.wps22[0] = self.wps22[1]
        self.wps22[-1].command = 21
        wps = self.wps22
        return wps


    # def home_distance(self):
    #     Present_loc = [self.gps.x, self.gps.y, self.gps.z]
    #     distance = np.linalg.norm(Present_loc - self.home)
    #     return distance

    def Decision_Making(self):
        # Present_loc = [self.gps.x, self.gps.y, self.gps.z]
        # distance = np.linalg.norm(Present_loc - self.home)
        battery_req = 31
        while(self.bat_percentage > battery_req):
            print(self.bat_percentage)
        self.set_mode("AUTO")
        # n_prev=mav.reached_index
        self.wpClear()
        print("Time to Land")
        self.wpClear()	
        self.set_mode("GUIDED")
        self.waypoint_push(self.Mission_2())
        self.set_mode("AUTO")
        self.toggle_arm(0)

if __name__ == '__main__':

    mav = FLIGHT_CONTROLLER()
    stateMt = stateMoniter()

    #Set time checkpoint for 800 seconds
    warn_time = time.time()+500

    rate= rospy.Rate(20.0)
    time.sleep(3)
    print(mav.within_rad())
    if (True):		
        # defining waypoints
        # 16 -> NAVIGATE
        # 21 -> LAND
        # 22 -> TAKEOFF
        print(mav.reached_index, ' 0')
        mav.set_mode('STABILIZE')
        mav.toggle_arm(1)
        time.sleep(3)
        mav.set_Guided_mode()
        mav.takeoff(5)
        time.sleep(2)
        # mav.set_Guided_mode()
        # time.sleep(2)
        

        #Mission 1 : Navigate to PRP via waypoints
        mav.wpPush(mav.Mission_1())
        mav.set_mode("AUTO")
        mav.toggle_arm(0)
        while(True):
            if (mav.reached_index ==1):
                with open('readme.txt', 'w') as f:
                    f.write(mav.voltage)
                break
        
        while(True):
            if (mav.reached_index ==2):
                with open('readme1.txt', 'w') as f:
                    f.write(mav.voltage)
                break

                
        

        



        # while(True):
        #     x = [mav.curr, mav.volt, mav.bat_percentage]
        #     print(x)
        # print(mav.wp_g[1]-mav.wp_g[0])

        # mav.Decision_Making()
    
