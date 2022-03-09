import b0RemoteApi
import sys
import os
import itertools
import random
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

global actionSpace

actionSpace = ["t","rP","rH","rC","mC","pB"]

filepathForResults = os.getcwd()+"/resultsRandomSearch/"
if not os.path.exists(filepathForResults):
    os.makedirs(filepathForResults)
print("Results will be saved to: "+filepathForResults)

def checkPreconditions(action,stateVector):
    """ this function evaluates the action preconditions from Table II in the paper."""

    s_area =    stateVector[0]
    s_parts =   stateVector[1]
    s_robot =   stateVector[2]
    s_gear =    stateVector[3]
    s_rH =      stateVector[4]
    s_rC =      stateVector[5]
    s_cover =   stateVector[6]

    if action == "t":
        return True
    elif action == "rP":
        return not stateVector[0] # not s_area
    elif action == "rH":
        return s_area and s_parts and (not s_cover) and (not s_gear)
    elif action == "rC":
        return s_area and s_parts and (not s_cover)
    elif action == "mC":
        return s_area and s_parts and (not s_cover)
    elif action == "pB":
        return s_area
    else:
        raise Exception("Error in function 'checkPreconditions': argument is not a valid action")

def getFeasibleActions(stateVector):
    feasibleActions = list()
    for action in actionSpace:
        if checkPreconditions(action,stateVector):
            feasibleActions.append(action)
    return feasibleActions

def getMaxRiskValues(risksFromAllEpisodes):
    maxRiskList = list()
    for riskSequence in risksFromAllEpisodes:
        maxRiskList.append(max(riskSequence))
    return maxRiskList

with b0RemoteApi.RemoteApiClient('b0RemoteApi_V-REP-addOn','b0RemoteApiAddOn') as client:  #This line defines the client, which provides all functions of the remote API
    # the function list can be found here: https://www.coppeliarobotics.com/helpFiles/en/b0RemoteApi-functionList.htm

    actionIsSet = False
    N_STEPS_EPISODE = 9 #length of nominal sequence + 2
    N_STEPS_TOTAL = 100*N_STEPS_EPISODE

    # initialize simulation
    client.simxSynchronous(True)
    client.simxStartSimulation(client.simxServiceCall()) #use client to start the simulation
    client.simxSynchronousTrigger()

    stepCounterTotal = 0
    stepCounterEpisode = 0
    risksFromAllEpisodes = list() # list of risk values over the whole search
    actionsFromAllEpisodes = list() # list of action sequences from all episodes

    motionParametersMin     = [-0.2,0.8,1]
    motionParametersMax     = [0.2,1.2,1.5]
    motionParametersNominal = [0,1,1]

    # main loop (1 execution = 1 search episode)
    while (stepCounterTotal <= N_STEPS_TOTAL):

        # initialize new episode
        print("-------------- new episode --------------")

        risksFromThisEpisode = list()
        actionsFromThisEpisode = list()
        stepCounterEpisode = 0
        client.simxCallScriptFunction("resetMaxRisk@RiskMetricCalculator","sim.scripttype_childscript",1,client.simxServiceCall())
        client.simxCallScriptFunction("reset@Bill","sim.scripttype_childscript",1,client.simxServiceCall())

        # action loop (1 execution = 1 single action in the simulation)
        while (stepCounterEpisode <= N_STEPS_EPISODE):

            # check if human model is cucrently performaing an action
            _,isRunning = client.simxCallScriptFunction("isHumanModelActive@Bill","sim.scripttype_childscript",1,client.simxServiceCall())

            if isRunning:
                # step simulation forward
                client.simxSynchronousTrigger()
            else:
                if not (stepCounterEpisode == 0):
                    print("action "+str(stepCounterEpisode))
                    # retrieve maximum risk value from previous action
                    _,risk = client.simxCallScriptFunction("getMaxRisk@RiskMetricCalculator","sim.scripttype_childscript",1,client.simxServiceCall())
                    client.simxCallScriptFunction("resetMaxRisk@RiskMetricCalculator","sim.scripttype_childscript",1,client.simxServiceCall())
                    risksFromThisEpisode.append(risk)
                    print("risk from this action: "+str(risk))

                # retrieve current state
                currentState = None
                while currentState == None:
                    # try to get current state and retry if it fails (sometimes multiple timesteps are needed until simulator returns valid result)
                    try:
                        currentState = client.simxCallScriptFunction("getStateVector@StateVariablesTracker","sim.scripttype_childscript",None,client.simxServiceCall())
                        client.simxSynchronousTrigger()
                    except:
                        pass
                success = currentState.pop(0)
                if success:
                    pass
                    #print("current state:")
                    #print(currentState)
                else:
                    raise Exception("Error: Retrieve state variables failed.")

                # sample next action (randomly)
                action = random.choice(getFeasibleActions(currentState))
                actionsFromThisEpisode.append(action)
                client.simxCallScriptFunction("setAction@Bill","sim.scripttype_childscript",action,client.simxServiceCall())
                print("new action:"+action)

                # set continuous motion parameters (randomly)
                motionParameters = list()
                for k in range(3):
                    print(k)
                    param = motionParametersMin[k]+ (motionParametersMax[k]-motionParametersMin[k]) * random.random()
                    motionParameters.append(param)
                    #assert motionParameters.append(motionParametersMin[k])# + (motionParametersMax[k]-motionParametersMin[k]) * random.random())
                print("selected motion parameters:")
                print(motionParameters)
                client.simxCallScriptFunction("setMotionParameters@Bill","sim.scripttype_childscript",motionParameters,client.simxServiceCall()) # TODO: check that parameters are within limits

                stepCounterEpisode += 1
                stepCounterTotal += 1
        if (not stepCounterTotal == 0): # don't do this in the first epside, since there are no risk values available
            risksFromAllEpisodes.append(risksFromThisEpisode)
            actionsFromAllEpisodes.append(actionsFromThisEpisode)
        print(risksFromAllEpisodes)

    # save results as np file
    maxRiskList     = getMaxRiskValues(risksFromAllEpisodes)
    results_risk    = np.asarray(risksFromAllEpisodes)
    results_actions = np.asarray(actionsFromAllEpisodes)
    np.save(filepathForResults + "/risks.npy", results_risk)
    np.save(filepathForResults + "/actions.npy", results_actions)
    #resultRisk = np.asarray(actionsFromAllEpisodes)

    plt.plot(maxRiskList,"*")
    plt.ylabel('Max risk of episode')
    plt.xlabel('Episodes')
    plt.grid(True)
    plt.show()
    #plt.save(filepathForResults+str(datetime.now())+".png")
