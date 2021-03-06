import b0RemoteApi
import sys
import itertools
import random
from FiniteStateMachine import State, Transition, Automaton
from Workflows import Workflow1, Workflow1Mod, Workflow2

################################# USER SETTINGS ################################
# User settings
CONTROL_MANUAL = True # Set "True" to execute simulation step-by-step manually
N_ITERATIONS = 10 # number of simulation runs
USE_RANDOM_ACTIONS = False # True =  actions are sampled randomly from the action space. False = A default action sequence will be used
ACTION_SEQUENCE_LENGTH = 10 # is only relevant for random actions

################################# LOAD FSM ###################################
# workflow = Workflow1()      # scenario 1, original workflow
# workflow = Workflow1Mod()   # scenario 1, modified workflow
workflow = Workflow1Mod()      # scenario 2

workflowModel = workflow.workflowModel #Automaton(states, actionSpace, trans, [])
states = workflow.states
trans = workflow.transitions
actionSpace = workflow.actionSpace
workflowModel.setVerbosity(False)

# Define default action sequence (this sequence will be used if USE_RANDOM_ACTIONS == False)

# Action space workflow 1
#0 t = Transition("t", False, 0, False, False)  # transition between stations
#1 r_P = Transition("rP", False, 0, False, False)  # reach for parts
#2 r_H = Transition("rH", False, 0, False, False)  # reach in housing
#3 r_C = Transition("rC", False, 0, False, False)  # reach in cover
#4 p_B = Transition("pB", False, 0, False, False)  # press button
#5 m_C = Transition("mC", False, 0, False, False)  # mount cover


# Action space workflow 2
#0 p   = Transition("p",   False, 0, False, False)  # get part from storage/put it back
#1 f   = Transition("f",   False, 0, False, False)  # feed part to robot/retreive it
#2 b_W = Transition("b_W", False, 0, False, False)  # press button to activate robot (normal)
#3 b_O = Transition("b_O", False, 0, False, False)  # press button to activate robot in safety override mode
#4 w   = Transition("w",   False, 0, False, False)  # wait
#5 i   = Transition("i",   False, 0, False, False)  # inspect

#defaultActionSequenceIndices = [4, 4, 5, 2, 4] #[t,r_P,t,r_H,p_B,r_C,m_C]
defaultActionSequenceIndices = [3,4,4,5,4,3,2,3,4] #[t,r_P,t,r_H,p_B,r_C,m_C]

defaultActionSequence = list()
for index in defaultActionSequenceIndices:
    defaultActionSequence.append(actionSpace[index])

############################ CONTROL SIMULATION ################################

with b0RemoteApi.RemoteApiClient('b0RemoteApi_V-REP-addOn','b0RemoteApiAddOn') as client:  #This line defines the client, which provides all functions of the remote API
    # the function list can be found here: https://www.coppeliarobotics.com/helpFiles/en/b0RemoteApi-functionList.htm
    # initialize simulation
    client.simxSynchronous(True)
    client.simxStartSimulation(client.simxServiceCall()) #use client to start the simulation
    actionSequenceIndex = 0
    actionIsSet = False
    paramsMin = [-0.2,0.8,1]
    paramsMax = []



    # main search loop (1 execution = 1 action sequence in the simulation)
    for i in range(N_ITERATIONS):
        print("Search iteration "+str(i))
        workflowIsDone = False
        actionHistory = list()
        currentStateIndex = workflowModel.currentStateIndex
        # action loop (1 execution = 1 single action in the simulation)
        while (not workflowIsDone):
            if (not actionIsSet):

                # print("------")
                # print("Current state: " + states[workflowModel.currentStateIndex].name)
                # _, feasibleActionIndices = workflowModel.getFeasibleActions()
                # print("feasible actions: ")
                # for index in feasibleActionIndices:
                #     print(actionSpace[index].name)
                # print("------")

                if USE_RANDOM_ACTIONS:
                    nextAction = actionSpace[random.randint(0,len(actionSpace)-1)]
                elif actionSequenceIndex<len(defaultActionSequence):
                    nextAction = defaultActionSequence[actionSequenceIndex]
                else:
                    print("action sequence ended")
                    stateVar = client.simxCallScriptFunction("getStateVector@StateVariablesTracker","sim.scripttype_childscript",1,client.simxServiceCall())
                    print("_____, area, parts, robot, gear,  s_rH,  s_rC,  s_cover")
                    print(stateVar)
                    client.simxStopSimulation()
                    break
                actionIsSet,_ = client.simxCallScriptFunction("setAction@Bill","sim.scripttype_childscript",nextAction.name,client.simxServiceCall())
                #parametersAreSet,_ = client.simxCallScriptFunction("setMotionParameters@Bill","sim.scripttype_childscript",[1.3,-0.05,0,1.2],client.simxServiceCall()) #walking velocity scaling factor, reaching goal offset x, reaching goal offset y, hand velocity scaling factor
                #client.simxCallScriptFunction("setMotionParameters@Bill","sim.scripttype_childscript",[0,1,1],client.simxServiceCall()) # TODO: check that parameters are within limits
                if actionIsSet:
                    actionSequenceIndex += 1
                    print("New action was set: " + nextAction.name)
                    actionHistory.append(nextAction)
                    isAccepted = workflowModel.setInputSequence(actionHistory)
                    # _, nextStateIndex = workflowModel.getNextTransition(trans[workflowModel.currentStateIndex],nextAction)
                    # workflowModel.currentStateIndex = nextStateIndex
                    # if isAccepted:
                    #     print("Action is feasible")
                    # else:
                    #     print("Warning! Action " + nextAction.name + " is not feasible in the current state! Workflow has been terminated")
                    #     workflowIsDone = True
                    #     actionSequenceIndex = 0
                    #     actionIsSet = False
                    #     client.simxCallScriptFunction("reset@Bill","sim.scripttype_childscript",1,client.simxServiceCall())
                    if CONTROL_MANUAL:
                        stateVar = client.simxCallScriptFunction("getStateVector@StateVariablesTracker","sim.scripttype_childscript",1,client.simxServiceCall())
                        print("_____, area, parts, robot, gear,  s_rH,  s_rC,  s_cover")
                        print(stateVar)
                        print("Press enter to continue")
                        input()
                client.simxSynchronousTrigger()
            else:
                _,isRunning = client.simxCallScriptFunction("isHumanModelActive@Bill","sim.scripttype_childscript",1,client.simxServiceCall())
                if (not isRunning):
                    _,maxRisk = client.simxCallScriptFunction("getMaxRisk@RiskMetricCalculator","sim.scripttype_childscript",1,client.simxServiceCall())
                    print("Action done")
                    print("Max risk from this action: "+str(maxRisk))
                    print("-----------------------------")
                    client.simxCallScriptFunction("resetMaxRisk@RiskMetricCalculator","sim.scripttype_childscript",1,client.simxServiceCall())
                    actionIsSet = False
                    if actionSequenceIndex == ACTION_SEQUENCE_LENGTH:
                        workflowIsDone = True
                        actionSequenceIndex = 0
                        actionIsSet = False
                        client.simxCallScriptFunction("reset@Bill","sim.scripttype_childscript",1,client.simxServiceCall())
                        workflowModel.reset()
                        print("workflow is done!")
                else:
                    client.simxSynchronousTrigger()

    # stateVar = client.simxCallScriptFunction("getStateVector@StateVariablesTracker","sim.scripttype_childscript",1,client.simxServiceCall())
    # print(stateVar)
    # client.simxStopSimulation()
