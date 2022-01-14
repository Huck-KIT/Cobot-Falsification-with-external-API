# Collaborative Robot Workflow in CoppeliaSim with Python API
## Introduction
This example shows a simulation of collaborative robot workflow in CoppeliaSim. The human model in the workflow can be controlled through an external Python interface.

## Example Workflow

<img src="https://user-images.githubusercontent.com/56551323/139922675-bec8337b-556d-4d55-a843-07871c5d8177.gif" alt="drawing" width="500"/>

In this workflow, the human worker transitions to a shelf, grabs some parts, returns to the robot, reaches into the workpiece housing, and then presses a button to activate the robot. The robot puts a gearwheen into the housing. Meanwhile, the human reaches into the workpiece cover and then mounts the cover onto the housing. To simulate the effects of human error, the human model can change the order of worksteps (within some boundaries, since the resulting sequences still must be feasible). To caputure the variability of human motion, the human model can also vary its position at the table (laterally, +/- 20cm), its hand velocity (+/- 20%), and the upper body angle when reaching for the workpieces (+/- 25%). As mentioned above, the goal is to find combinations of action sequences and motion parameters that result in a critical collision. 

_Note: As you may notice from the sometimes awkward human motions, we use a simplified human model in this case. This example is not about achieving an extremely detailed simulation of human motion, it is about the general idea of searching for hazardous behaviors!_

## Prerequisites
This example was developed using Ubuntu 18.04 and CoppeliaSim 4.2). To run this example, you need:
- CoppeliaSim 4.2.0 or newer (available [here](https://www.coppeliarobotics.com/downloads))
- The Lua Library "String Distance" (Install from [here](http://www.ccpa.puc-rio.br/software/stringdistance/) and place the resulting library file 'stringdistance.so' in the CoppeliaSim installation folder)
- Python 3 

## Run the Example
To run the example, proceed as follows:
- Open the CoppeliaSim model and enable the B0-remote API (if you don't know how to do this, an explanation can be found [here](https://www.coppeliarobotics.com/helpFiles/en/b0RemoteApiOverview.htm).
- Run the script test.py from your console. This will trigger the human model in the simulation to perform an action sequence (currently, the actions are either hard-coded, or randomly selected, as no search algorithm is used at the moment).
- Depending on how wether you set CONTROL_MANUAL in test.py on True or False, you can either trigger each action manually, or run the whole action sequence at once.
Note that during the simulation, a risk metric is evaluated. The risk metric is based on factors such as human-robot distance, velocity, estimated collision forces, and more. After each action, the maximum risk value at the current timestep is displayed in the console (for details on the defition of the risk metric, see Section IV-C [this paper](https://ieeexplore.ieee.org/document/9645356).

In this example, the worker can perform the following actions: Transition between stations (t), reach for parts from the shelf (rP), reach into the workpiece housing (rH), reach into the workpiece cover (rC), press the button to activate the robot (pB), and mount the cover (mC). You can modify the action sequence by changing the variable defaultActionSequence in line 50 of test.py. Alternatively, the action sequences can also be generated randomly by setting USE_RANDOM_ACTIONS = True.

Note that there are certain constraints on the action sequences that are possible. The following finite state machine (FSM) shows which action sequences of the human worker are feasible:

<img src="https://user-images.githubusercontent.com/56551323/139909669-5295cd09-7c8b-432c-a03f-5b898078db2e.png" alt="drawing" width="800"/>

An action sequence is feasible if it is accepted by the FSM. For instance, the sequence (t,rP,t,rH,pB,rC,mC) (shown in the video clip above) is feasible, whereas the sequence (t,rP,rH,pB,rC,mC,t) is infeasible. If an infeasible action is selected, the FSM will recognize this, print an error to the console, and terminate the action sequence.
You can also create a .txt file of all feasible action sequences by running the script generateActionSequence.py".

