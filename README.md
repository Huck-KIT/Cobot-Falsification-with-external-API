# Robot-Hazard-Analysis-Simulation
## Introduction
This example shows how simulation of collaborative robot workflows can be used to uncover potential hazards for the human worker. It is motivated by the problem of design-time risk assessment of robot systems. The main research questions that are addressed by this example are:
1. How can we use simulation to identify potential hazards in an early development stage (i.e., before the system is built and commissioned in real life)?
2. How can we identify hazardous worker behaviors that are likely to cause unsafe states wen performed in interaction with the robot system?

## Concept
The general approach is to simulate a collaborative workflow of human and robot and to evaluate a risk metric during the simulation. The risk metric is based on factors such as human-robot distance, velocity, estimated collision forces, and more. Our objective is to expose hazards by finding unsafe states (more specifically, human-robot collisions that exceed a certain force limit). We achieve this by varying the behavior of the human worker in simulation, and recording behaviors where the the risk metric exceeds a certain threshold. We vary the behavior of the human worker both on an action-level (e.g. the human worker can omit an action or switch the order of actions in the workflow) and on a motion-level (e.g., the worker can walks to a slighly different position each time). Since this results in a vast search space of possible behaviors, we use a search algorithm that is guided by the risk metric and tries to find as many high-risk behaviors as possible

_Note to reviewers: At this point, we will link to the paper for more explanation once it is published)_

## Example Workflow

<img src="https://user-images.githubusercontent.com/56551323/139922675-bec8337b-556d-4d55-a843-07871c5d8177.gif" alt="drawing" width="500"/>

In this workflow, the human worker transitions to a shelf, grabs some parts, returns to the robot, reaches into the workpiece housing, and then presses a button to activate the robot. The robot puts a gearwheen into the housing. Meanwhile, the human reaches into the workpiece cover and then mounts the cover onto the housing. To simulate the effects of human error, the human model can change the order of worksteps (within some boundaries, since the resulting sequences still must be feasible). To caputure the variability of human motion, the human model can also vary its position at the table (laterally, +/- 20cm), its hand velocity (+/- 20%), and the upper body angle when reaching for the workpieces (+/- 25%). As mentioned above, the goal is to find combinations of action sequences and motion parameters that result in a critical collision. 

_Note: As you may notice from the sometimes awkward human motions, we use a simplified human model in this case. This example is not about achieving an extremely detailed simulation of human motion, it is about the general idea of searching for hazardous behaviors!_

## Prerequisites
This example was developed using Ubuntu 18.04 and CoppeliaSim 4.2). To run this example, you need:
- CoppeliaSim 4.2.0 or newer (available [here](https://www.coppeliarobotics.com/downloads))
- The Lua Library "String Distance" (Install from [here](http://www.ccpa.puc-rio.br/software/stringdistance/) and place the resulting library file 'stringdistance.so' in the CoppeliaSim installation folder)
- Python 2.7 or newer

## Run the Example
### Preparations
After downloading the repository, you need to set some file paths in CoppeliaSim (using relative paths in CoppeliaSim is somewhat error-prone, so you should set absolute paths). Open the simulation model 'simulation.ttt'. You will see a hierarchy of objects on the left. First, click on the text symbol besides the object "SearchAlgorithm". This will open the script which controls the simulation. The comments in the script will direct you to set the paths to the hazardLog.txt and actionSequences.txt files. Then, click on the script symbol besides of the object "screenshotSensor" and enter the path where you want the simulation to save the screenhots (the simulation will generate screenshots of the scene when critical situations are found).

### Create Action Sequences
In this example, the worker can perform the following actions: Transition between stations (t), reach for parts from the shelf (rP), reach into the workpiece housing (rH), reach into the workpiece cover (rC), press the button to activate the robot (pB), and mount the cover (mC). 
We use a finite state machine (FSM) to model which action sequences of the human worker are feasible:

<img src="https://user-images.githubusercontent.com/56551323/139909669-5295cd09-7c8b-432c-a03f-5b898078db2e.png" alt="drawing" width="800"/>

An action sequence is feasible if it is accepted by the FSM. For instance, the sequence (t,rP,t,rH,pB,rC,mC) (which btw is the nominal workflow as shown in the clip) is feasible, whereas the sequence (t,rP,rH,pB,rC,mC,t) is infeasible.
By running the preprocessings script 'generateActionSequences.py'. This will iterate through all possible action sequences of a certain length (here length=7), extract the feasible sequences, and write them to the file 'actionSequences.txt'.

_Note: When you download this repositry, actionSequences.txt is already filled, so you can omit this step if you want._

### Search for Hazards
You can start the search for hazards simply by pressing the 'play' button in CoppeliaSim. This will prompt a window where you must enter a so-called split factor. Essentially, the split factor decides how the search algorithm distributes the maximum number of simulation runs. For more details on this, see the paper linked above. If you just want to try out the simulation, we recomend you choose an arbitrary factor between 0.4 and 0.6. CoppeliaSim will now simulated the collaborative workflow with action squences and motion parameters of the human worker. During simulation, a graph will show the current level of risk. If the risk metric exceeds a certain threshold (here: threshold=1.7), a log entry and a screenshot of the hazardous situation will be created (assuming you set the correct paths for hazard log and screenshots).# Cobot falsification with external API

