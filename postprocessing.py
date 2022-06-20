import os
import re
import statistics

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pyxdameraulevenshtein import damerau_levenshtein_distance
import csv

def getDistanceFromNominal(actionSequence):
    # to use the damerau levenshtein distance, action sequence is converted into a single string
    actionSequenceAsString = ""
    for action in actionSequence:
        if action == "pB":
            actionSequenceAsString += "b"
        elif action == "t":
            actionSequenceAsString += "t"
        elif action == "rP":
            actionSequenceAsString += "p"
        elif action == "rC":
            actionSequenceAsString += "c"
        elif action == "rH":
            actionSequenceAsString += "h"
        elif action == "mC":
            actionSequenceAsString += "m"
        elif action == "iA":
            actionSequenceAsString += "i"
    return damerau_levenshtein_distance(actionSequenceAsString,"tpthbcmi")



def readData(filepath):
    # load file with risk values
    if os.path.exists(filepath+"/risks.npy"):
        riskValuesAsNp = np.load(filepath+"/risks.npy")
        riskValues = pd.DataFrame(riskValuesAsNp)
    elif os.path.exists(filepath+"/risks.csv"):
        #riskValues = np.loadtxt(filepath+"/risks.csv", delimiter=',')
        riskValues = pd.read_csv(filepath+"/risks.csv", delimiter=',', names=list(range(12)))
    else:
        print('Error: No Risk data found!')

    # open file with saved action sequences and read the content in a list
    actionSequences = []
    if os.path.exists(filepath+"/actionSequences.txt"):
        with open(filepath + '/actionSequences.txt', 'r') as filehandle:
            filecontents = filehandle.readlines()
            for line in filecontents:
                current_line = line[:-1]
                current_line = re.findall('[a-zA-Z]+', current_line) #current_line.split("'")
                # current_line = current_line.split(",")
                # print(current_line)
                actionSequences.append(current_line)
    elif os.path.exists(filepath+"/actionSequences.csv"):
        #riskValues = np.loadtxt(filepath+"/risks.csv", delimiter=',')
        # reader_oi = pd.read_csv(filepath+"/actionSequences.csv", delimiter=',', names=list(range(10)))
        with open(filepath+"/actionSequences.csv", newline='') as csvfile:
            reader_obj = csv.reader(csvfile, delimiter=' ', quotechar='|')
            for row in reader_obj:
                actionSequences.append(row)
    else:
        print('Error: No action data found!')

    return riskValues,actionSequences

def remainingStepsToCompletion(actionSequence):
    # print("check reamining steps for sequence: ")
    # print(actionSequence)
    nominalAssembly = ["t", "rP", "t", "rH", "pB", "rC", "mC"]
    for action in actionSequence:
        if len(nominalAssembly) > 0 and action == nominalAssembly[0]:
            nominalAssembly.pop(0)
    # print(str(len(nominalAssembly))+" steps remain!")
    return(len(nominalAssembly))

    if actionSpace[a].name == 'iA':
        assemblySeq = nominalAssembly.copy()
    elif len(assemblySeq) > 0 and actionSpace[a] == assemblySeq[0]:
        assemblySeq.pop(0)
        if len(assemblySeq) == 0:
            # print('---------- Assembly Sequence Completed ----------')
            completedSeq += 1
        else:
            # print('{} actions left to do in {} steps'.format(len(assemblySeq), max_steps-m-1))
            pass

def remainingStepsToCompletionLagrangian(actionSequence):
    # print("check reamining steps for sequence: ")
    # print(actionSequence)
    nominalAssembly = ["t", "rP", "t", "rH", "pB", "rC", "mC"]
    actionSequenceAsList = actionSequence[0].split(sep=",")
    for action in actionSequenceAsList:
        # print("action")
        # print(action)
        if len(nominalAssembly) > 0 and action == nominalAssembly[0]:
            nominalAssembly.pop(0)
    # print(str(len(nominalAssembly))+" steps remain!")

    return(len(nominalAssembly))

    if actionSpace[a].name == 'iA':
        assemblySeq = nominalAssembly.copy()
    elif len(assemblySeq) > 0 and actionSpace[a] == assemblySeq[0]:
        assemblySeq.pop(0)
        if len(assemblySeq) == 0:
            # print('---------- Assembly Sequence Completed ----------')
            completedSeq += 1
        else:
            # print('{} actions left to do in {} steps'.format(len(assemblySeq), max_steps-m-1))
            pass

def evaluateSequences(actionSequences,maximumRiskValues,riskThreshold):
    actionSequencesAboveThreshold = list()
    normalizedCollisionForces = list()
    distancesFromNominalSequence = list()
    action_counter=0
    for i in range(len(actionSequences)):
        action_counter += len(actionSequences[i])
        if maximumRiskValues[[i][0]] > riskThreshold and maximumRiskValues[[i][0]] < 5.0 and action_counter < 10000: # <5 because there seems to be a bug that occasionally yields values >>5. This is not realistic in the simulation and likely a bug, so we remove that.
            if not actionSequences[i] in actionSequencesAboveThreshold:
                actionSequencesAboveThreshold.append(actionSequences[i])
                normalizedCollisionForces.append(maximumRiskValues[i]-1)
                # distancesFromNominalSequence.append(getDistanceFromNominal(actionSequences[i]))
                distancesFromNominalSequence.append(remainingStepsToCompletion(actionSequences[i]))
    print("numer of actions: "+str(action_counter))
    return actionSequencesAboveThreshold,normalizedCollisionForces,distancesFromNominalSequence

def evaluateSequencesLagrangian(actionSequences,maximumRiskValues,riskThreshold):
    actionSequencesAboveThreshold = list()
    normalizedCollisionForces = list()
    distancesFromNominalSequence = list()
    action_counter = 0
    for i in range(len(actionSequences)-1):
        actionSequenceAsList = actionSequences[i][0].split(sep=",")
        action_counter += len(actionSequenceAsList)
        if maximumRiskValues[[i][0]] > riskThreshold and maximumRiskValues[[i][0]] < 5.0 and action_counter < 10000: # <5 because there seems to be a bug that occasionally yields values >>5. This is not realistic in the simulation and likely a bug, so we remove that.
            if not actionSequences[i] in actionSequencesAboveThreshold:
                actionSequencesAboveThreshold.append(actionSequences[i])
                normalizedCollisionForces.append(maximumRiskValues[i]-1)
                # distancesFromNominalSequence.append(getDistanceFromNominal(actionSequences[i]))
                distancesFromNominalSequence.append(remainingStepsToCompletionLagrangian(actionSequences[i]))
            else:
                print("seq already found!")
    print("numer of actions (lagragnian): "+str(action_counter))
    return actionSequencesAboveThreshold,normalizedCollisionForces,distancesFromNominalSequence


################################################################################
filepathQ = os.getcwd()+"/resultsLQ"#/13:49:26"
filepathR = os.getcwd()+"/resultsRandomSearch/16:14:58"
filepathLangrangian = os.getcwd()+"/06.20_094640_case_tryout"

filesQ = [x[0] for x in os.walk(filepathQ)]
filesQ.pop(0)

dir_counter = 0
for dir in filesQ:
     if dir_counter == 0:
          riskValuesQ,actionSequencesQ    = readData(dir)
          dir_counter +=1
     else:
          riskValuesQ_temp,actionSequencesQ_temp    = readData(dir)
          riskValuesQ = pd.concat([riskValuesQ,riskValuesQ_temp],ignore_index=True)
          actionSequencesQ = actionSequencesQ+actionSequencesQ_temp

filesR = [x[0] for x in os.walk(filepathR)]
filesR.pop(0)

riskValuesR,actionSequencesR = readData(filepathR)

# dir_counter = 0
# for dir in filesR:
#     if dir_counter == 0:
#          riskValuesR,actionSequencesR    = readData(dir)
#          dir_counter +=1
#     else:
#          riskValuesR_temp,actionSequencesR_temp    = readData(dir)
#          riskValuesR = pd.concat([riskValuesR,riskValuesR_temp],ignore_index=True)
#          actionSequencesR = actionSequencesR+actionSequencesR_temp
     # print(actionSequencesR)

# print(riskValuesQ)
# print(len(actionSequencesQ))
#
# print(riskValuesR)
# print(len(actionSequencesR))

riskValuesLagangrian,actionSequencesLagrangian = readData(filepathLangrangian)


#for a fair comparison, use from the random sampling dataset only as many episodes as the Q-learning has
# riskValuesR = riskValuesR[0:len(actionSequencesQ)]
# actionSequencesR = actionSequencesR[0:len(actionSequencesQ)]

riskThreshold = 1 # action sequences with risk above this threshold contain a collision

maximumRiskValuesQ = riskValuesQ.max(axis=1)
maximumRiskValuesR = riskValuesR.max(axis=1)
maximumRiskValuesLagrangian = riskValuesLagangrian.max(axis=1)
# print("risks random")
# print(riskValuesR)
#
# print("max risks random")
# print(maximumRiskValuesR)
#
# print("risks:")
# print(riskValuesLagangrian)
print("max risks len:")
print(len(maximumRiskValuesLagrangian))
# print(maximumRiskValuesR)

#calculate max, mean, and stdDev of risk values
if len(maximumRiskValuesQ) != len(actionSequencesQ):
     print("Error: number of action sequences and risk vectors are not same!")
else:
    actionSequencesAboveThresholdQ,riskValuesAboveThresholdQ,distancesFromNominalSequenceQ = evaluateSequences(actionSequencesQ,maximumRiskValuesQ,riskThreshold)
    actionSequencesAboveThresholdR,riskValuesAboveThresholdR,distancesFromNominalSequenceR = evaluateSequences(actionSequencesR,maximumRiskValuesR,riskThreshold)
    actionSequencesAboveThresholdLagrangian,riskValuesAboveThresholdLagrangian,distancesFromNominalSequenceLagrangian = evaluateSequencesLagrangian(actionSequencesLagrangian,maximumRiskValuesLagrangian,riskThreshold)

# print(riskValuesLagangrian)
# print(riskValuesAboveThresholdLagrangian)

    # Print report to console
    print("---------- Results Random Sampling: -----------")
    print("Highest risk value discovered: "+str(max(riskValuesAboveThresholdR)))
    print("Collisions found: "+str(len(riskValuesAboveThresholdR)))
    # print("Action sequences leading to collision: ")
    # print(actionSequencesAboveThresholdR)
#
    print("------------- Results Q-learning: -------------")
    print("Highest risk value discovered: "+str(max(riskValuesAboveThresholdQ)))
    print("Collisions found: "+str(len(riskValuesAboveThresholdQ)))
    # print("Action sequences leading to collision: ")
    # print(actionSequencesAboveThresholdQ)

    print("------------- Results Lagrangian: -------------")
    print("Highest risk value discovered: "+str(max(riskValuesAboveThresholdLagrangian)))
    print("Collisions found: "+str(len(riskValuesAboveThresholdLagrangian)))

    # print(actionSequencesAboveThresholdR)


    print(len(actionSequencesLagrangian))
# #
    #create scatterplot of risk- and distance values
    # plt.grid(True)
    # plt.scatter(distancesFromNominalSequenceR,riskValuesAboveThresholdR,color="Red",label="Q-learning")
    # plt.scatter(distancesFromNominalSequenceQ,riskValuesAboveThresholdQ,color="Green",label="Q-learning")
    # plt.title("Risk vs. Distance from Nominal Behavior")
    # plt.xlim(left=0)
    # plt.ylim(bottom=0)
    # plt.xlabel("Distance from Nominal Behavior")
    # plt.ylabel("F_collision/F_max")
    # plt.show()
#
    d = {'maxRisk':riskValuesAboveThresholdQ,'distance':distancesFromNominalSequenceQ,'method':'Qlearning'}
    dataQ = pd.DataFrame(data=d)

    d = {'maxRisk':riskValuesAboveThresholdR,'distance':distancesFromNominalSequenceR,'method':'Random'}
    dataR = pd.DataFrame(data=d)

    d = {'maxRisk':riskValuesAboveThresholdLagrangian,'distance':distancesFromNominalSequenceLagrangian,'method':'Lagrangean'}
    dataL = pd.DataFrame(data=d)

    d = [dataQ,dataR,dataL]
    dataComplete = pd.concat(d)
#
#     print(dataQ)
#
    fig, ax = plt.subplots()
    # ax =  sns.stripplot(x="distance", y="maxRisk", hue="method",data=dataComplete, palette="Set2", size=20, marker="D", edgecolor="gray", alpha=.25)    # sns.kdeplot(data=dataQ, x="distance", y="maxRisk", ax=ax)
    levels = 4
    sns.kdeplot(x="distance", y="maxRisk",data=dataQ, ax=ax, color="Blue", label="Q-Learning",levels=levels)
    sns.kdeplot(x="distance", y="maxRisk",data=dataR, ax=ax, color="Red", label="Random Sampling",levels=levels)
    sns.kdeplot(x="distance", y="maxRisk",data=dataL, ax=ax, color="Green", label="Lagrangean",levels=levels)

    sns.scatterplot(x="distance", y="maxRisk",data=dataQ, ax=ax, color="Blue")
    sns.scatterplot(x="distance", y="maxRisk",data=dataR, ax=ax, color="Red")
    sns.scatterplot(x="distance", y="maxRisk",data=dataL, ax=ax, color="Green")

    # sns.swarmplot(data=dataComplete, x="distance", y="maxRisk", hue="method", dodge = False, ax=ax)
    # g = sns.jointplot(data=dataComplete, x="distance", y="maxRisk", hue="method", kind = 'scatter')

    plt.grid(True)
    plt.show()
