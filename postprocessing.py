import os
import re
import statistics

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pyxdameraulevenshtein import damerau_levenshtein_distance


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
        riskValues = pd.read_csv(filepath+"/risks.csv", delimiter=',', names=list(range(10)))
    else:
        print('Error: No Risk data found!')

    # open file with saved action sequences and read the content in a list
    actionSequences = []
    with open(filepath + '/actionSequences.txt', 'r') as filehandle:
        filecontents = filehandle.readlines()
        for line in filecontents:
            current_line = line[:-1]
            current_line = re.findall('[a-zA-Z]+', current_line) #current_line.split("'")
            # current_line = current_line.split(",")
            # print(current_line)
            actionSequences.append(current_line)

    return riskValues,actionSequences

def remainingStepsToCompletion(actionSequence):
    print("check reamining steps for sequence: ")
    print(actionSequence)
    nominalAssembly = ["t", "rP", "t", "rH", "pB", "rC", "mC"]
    for action in actionSequence:
        if len(nominalAssembly) > 0 and action == nominalAssembly[0]:
            nominalAssembly.pop(0)
    print(str(len(nominalAssembly))+" steps remain!")
    return(len(nominalAssembly))

    if actionSpace[a].name == 'iA':
        assemblySeq = nominalAssembly.copy()
    elif len(assemblySeq) > 0 and actionSpace[a] == assemblySeq[0]:
        assemblySeq.pop(0)
        if len(assemblySeq) == 0:
            print('---------- Assembly Sequence Completed ----------')
            completedSeq += 1
        else:
            print('{} actions left to do in {} steps'.format(len(assemblySeq), max_steps-m-1))

def evaluateSequences(actionSequences,maximumRiskValues,riskThreshold):
    actionSequencesAboveThreshold = list()
    normalizedCollisionForces = list()
    distancesFromNominalSequence = list()
    for i in range(len(actionSequences)):
        if maximumRiskValues[i] > riskThreshold and maximumRiskValues[i] < 5: # <5 because there seems to be a bug that occasionally yields values >>5. This is not realistic in the simulation and likely a bug, so we remove that.
            if not actionSequences[i] in actionSequencesAboveThreshold:
                actionSequencesAboveThreshold.append(actionSequences[i])
                normalizedCollisionForces.append(maximumRiskValues[i]-1)
                # distancesFromNominalSequence.append(getDistanceFromNominal(actionSequences[i]))
                distancesFromNominalSequence.append(remainingStepsToCompletion(actionSequences[i]))
    return actionSequencesAboveThreshold,normalizedCollisionForces,distancesFromNominalSequence

################################################################################
filepathQ = os.getcwd()+"/resultsLQ"#/13:49:26"
filepathR = os.getcwd()+"/resultsRandomSearch"#/16:14:58"
filepathLangrangian = os.getcwd()+"/results_lagrangian"

riskValuesQ,actionSequencesQ    = readData(filepathQ)
riskValuesR,actionSequencesR    = readData(filepathR)
riskValuesLagangrian            = readData(filepathLangrangian)

print("N: "+str(len(actionSequencesQ)))
# for a fair comparison, use from the random sampling dataset only as many episodes as the Q-learning has
riskValuesR = riskValuesR[0:len(actionSequencesQ)]
actionSequencesR = actionSequencesR[0:len(actionSequencesQ)]

riskThreshold = 1 # action sequences with risk above this threshold contain a collision

maximumRiskValuesQ = riskValuesQ.max(axis=1)
maximumRiskValuesR = riskValuesR.max(axis=1)

print(maximumRiskValuesQ)
print(maximumRiskValuesR)

#calculate max, mean, and stdDev of risk values
if len(maximumRiskValuesQ) != len(actionSequencesQ):
     print("Error: number of action sequences and risk vectors are not same!")
else:
    actionSequencesAboveThresholdQ,riskValuesAboveThresholdQ,distancesFromNominalSequenceQ = evaluateSequences(actionSequencesQ,maximumRiskValuesQ,riskThreshold)
    actionSequencesAboveThresholdR,riskValuesAboveThresholdR,distancesFromNominalSequenceR = evaluateSequences(actionSequencesR,maximumRiskValuesR,riskThreshold)

    # Print report to console
    print("---------- Results Random Sampling: -----------")
    print("Highest risk value discovered: "+str(max(maximumRiskValuesR)))
    print("Collisions found: "+str(len(riskValuesAboveThresholdR)))
    print("Action sequences leading to collision: ")
    print(actionSequencesAboveThresholdR)

    print("------------- Results Q-learning: -------------")
    print("Highest risk value discovered: "+str(max(maximumRiskValuesQ)))
    print("Collisions found: "+str(len(riskValuesAboveThresholdQ)))
    print("Action sequences leading to collision: ")
    print(actionSequencesAboveThresholdQ)

    # create scatterplot of risk- and distance values
    # plt.grid(True)
    # plt.scatter(distancesFromNominalSequenceR,riskValuesAboveThresholdR,color="Red",label="Q-learning")
    # plt.scatter(distancesFromNominalSequenceQ,riskValuesAboveThresholdQ,color="Green",label="Q-learning")
    # plt.title("Risk vs. Distance from Nominal Behavior")
    # plt.xlim(left=0)
    # plt.ylim(bottom=0)
    # plt.xlabel("Distance from Nominal Behavior")
    # plt.ylabel("F_collision/F_max")
    # plt.show()

    d = {'maxRisk':riskValuesAboveThresholdQ,'distance':distancesFromNominalSequenceQ,'method':'Qlearning'}
    dataQ = pd.DataFrame(data=d)

    d = {'maxRisk':riskValuesAboveThresholdR,'distance':distancesFromNominalSequenceR,'method':'Random'}
    dataR = pd.DataFrame(data=d)

    d = [dataQ,dataR]
    dataComplete = pd.concat(d)

    print(dataQ)

    fig, ax = plt.subplots()
    # ax =  sns.stripplot(x="distance", y="maxRisk", hue="method",data=dataComplete, palette="Set2", size=20, marker="D", edgecolor="gray", alpha=.25)    # sns.kdeplot(data=dataQ, x="distance", y="maxRisk", ax=ax)
    levels = 4
    sns.kdeplot(x="distance", y="maxRisk",data=dataQ, ax=ax, color="Blue", label="Q-Learning",levels=levels)
    sns.kdeplot(x="distance", y="maxRisk",data=dataR, ax=ax, color="Red", label="Random Sampling",levels=levels)
    sns.scatterplot(x="distance", y="maxRisk",data=dataQ, ax=ax, color="Blue")
    sns.scatterplot(x="distance", y="maxRisk",data=dataR, ax=ax, color="Red")

    # sns.swarmplot(data=dataComplete, x="distance", y="maxRisk", hue="method", dodge = False, ax=ax)
    # g = sns.jointplot(data=dataComplete, x="distance", y="maxRisk", hue="method", kind = 'scatter')

    plt.grid(True)
    plt.show()
