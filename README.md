# UAS iMechE 2023 Challenge Scripts

## Trajectory Generation
We used minimum snap trajectory generation to generate a smooth 8 degree polynomial trajectory passing through a sequence of waypoints<br>
<img align="right" src="/results/time_optimal_traj.png" width="40%" height="40%"/><br>
Initially we implemented a [trajectory with fixed time segments](https://github.com/atharva7am/Trajectory_Tracking_AeRoVe/blob/main/min_snap_trajectory_generator/fixed_time_ms.py)<br>

Then we improved it by computing [optimal time segments](https://github.com/atharva7am/Trajectory_Tracking_AeRoVe/blob/main/min_snap_trajectory_generator/min_snap_time_opt.py), where gradient descent is implemented to optimized time for each segment.<br>

We further modified the formulation to incorporate acceleration and velocity constraints to generate [constrained time optimized trajectory](https://github.com/atharva7am/Trajectory_Tracking_AeRoVe/blob/main/min_snap_trajectory_generator/constrained_time_opt.py)<br clear="right"/>
## PID based Controller
We implemented high-level position controller (lateral acceleration as control) and low level attitude controller (angular rates as control)<br>
<img src="/results/pid_tracking_1.jpeg" width="50%" height="50%"/>  <img src="/results/pid_tracking_2.jpeg" width="40%" height="40%"/><br>
