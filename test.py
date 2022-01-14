import b0RemoteApi
import sys
import itertools
import random
from FiniteStateMachine import State, Transition, Automaton

################################# USER SETTINGS ################################
# User settings
CONTROL_MANUAL = True # Set "True" to execute simulation step-by-step manually
N_ITERATIONS = 3 # number of simulation runs
USE_RANDOM_ACTIONS = False # True =  actions are sampled randomly from the action space. False = A default action sequence will be used
ACTION_SEQUENCE_LENGTH = 7 # is only relevant for random actions

################################# CREATE FSM ###################################
# Define states
#               state description                       isAcceptingFinalState   isTerminal  Truth table (optioal; not used here)
s_A1N   = State("worker at area 1, no parts taken",     True,                   False,  [])
s_A2N   = State("worker at area 2, no parts taken",     True,                   False,  [])
s_A1P   = State("worker at area 1, parts taken",        True,                   False,  [])
s_A2P   = State("worker at area 2, parts taken",        True,                   False,  [])
s_A1E   = State("worker at area 1, assembly ended",     True,                   False,  [])
s_A2E   = State("worker at area 2, assembly ended",     True,                   False,  [])
states  = [s_A1N,s_A2N,s_A1P,s_A2P,s_A1E,s_A2E] #first state in list is taken as initial state

# Define Transitions
# NOTE: since we only use the automaton for acceptance checking, we do not use timed transitions or external triggers.
# Therefore, the durations of the transition are set to 0 and the external triggers to False.
#                   name            isAutomatic    duration     isTriggeredExternally   setsExternalTrigger
t       = Transition("t",           False,         0,           False,                  False) # transition between stations
r_P     = Transition("rP",          False,         0,           False,                  False) # reach for parts
r_H     = Transition("rH",          False,         0,           False,                  False) # reach in housing
r_C     = Transition("rC",          False,         0,           False,                  False) # reach in cover
p_B     = Transition("pB",          False,         0,           False,                  False) # press button
m_C     = Transition("mC",          False,         0,           False,                  False) # mount cover
actionSpace = [t,r_P,r_H,r_C,p_B,m_C]

# Define transition matrix (rows: start states, colums: resulting states)
trans    = [[p_B,   t,      False,          False,  False,  False],
            [t,     False,  False,          r_P,    False,  False],
            [False, False,  [r_H,r_C,p_B],  t,      m_C,    False],
            [False, False,  t,              False,  False,  False],
            [False, False,  False,          False,  p_B,    t    ],
            [False, False,  False,          False,  t,      False]]

# Create FSM
workflowModel = Automaton(states,trans,[])
workflowModel.setVerbosity(False)

# Define default action sequence (this sequence will be used if USE_RANDOM_ACTIONS == False)
defaultActionSequence = [t,r_P,t,r_P,p_B,r_C,m_C]

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
        # action loop (1 execution = 1 single action in the simulation)
        while (not workflowIsDone):
            if (not actionIsSet):
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
                        print("workflow is done!")
                else:
                    client.simxSynchronousTrigger()

    client.simxStopSimulation()
