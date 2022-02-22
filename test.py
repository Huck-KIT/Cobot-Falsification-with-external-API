import b0RemoteApi
import sys
import itertools
import random
from FiniteStateMachine import State, Transition, Automaton
from Workflows import Workflow1, Workflow1Mod

################################# USER SETTINGS ################################
# User settings
CONTROL_MANUAL = True # Set "True" to execute simulation step-by-step manually
N_ITERATIONS = 10 # number of simulation runs
USE_RANDOM_ACTIONS = False # True =  actions are sampled randomly from the action space. False = A default action sequence will be used
ACTION_SEQUENCE_LENGTH = 8 # is only relevant for random actions

################################# LOAD FSM ###################################
#workflow = Workflow1()      # scenario 1, original workflow
workflow = Workflow1Mod()   # scenario 1, modified workflow

workflowModel = workflow.workflowModel #Automaton(states, actionSpace, trans, [])
states = workflow.states
trans = workflow.transitions
actionSpace = workflow.actionSpace
workflowModel.setVerbosity(False)

# Define default action sequence (this sequence will be used if USE_RANDOM_ACTIONS == False)
""" For Workflow1 and Workflow1Mod, the actions are encoded as follows:
0: t    # transition between stations
1: r_P  # reach for parts
2: r_H  # reach in housing
3: r_C  # reach in cover
4: p_B  # press button
5: m_C  # mount cover
"""
defaultActionSequenceIndices = [0, 1, 0, 2, 5, 4, 3, 5] #[t,r_P,t,r_H,p_B,r_C,m_C]
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

                print("------")
                print("Current state: " + states[workflowModel.currentStateIndex].name)
                _, feasibleActionIndices = workflowModel.getFeasibleActions()
                print("feasible actions: ")
                for index in feasibleActionIndices:
                    print(actionSpace[index].name)
                print("------")

                if USE_RANDOM_ACTIONS:
                    nextAction = actionSpace[random.randint(0,len(actionSpace)-1)]
                else:
                    nextAction = defaultActionSequence[actionSequenceIndex]
                actionIsSet,_ = client.simxCallScriptFunction("setAction@Bill","sim.scripttype_childscript",nextAction.name,client.simxServiceCall())
                client.simxCallScriptFunction("setMotionParameters@Bill","sim.scripttype_childscript",[0,1,1],client.simxServiceCall()) # TODO: check that parameters are within limits
                if actionIsSet:
                    actionSequenceIndex += 1
                    print("New action was set: " + nextAction.name)
                    actionHistory.append(nextAction)
                    isAccepted = workflowModel.setInputSequence(actionHistory)
                    _, nextStateIndex = workflowModel.getNextTransition(trans[workflowModel.currentStateIndex],nextAction)
                    workflowModel.currentStateIndex = nextStateIndex
                    if isAccepted:
                        print("Action is feasible")
                    else:
                        print("Warning! Action " + nextAction.name + " is not feasible in the current state! Workflow has been terminated")
                        workflowIsDone = True
                        actionSequenceIndex = 0
                        actionIsSet = False
                        client.simxCallScriptFunction("reset@Bill","sim.scripttype_childscript",1,client.simxServiceCall())
                    if CONTROL_MANUAL:
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

    client.simxStopSimulation()
