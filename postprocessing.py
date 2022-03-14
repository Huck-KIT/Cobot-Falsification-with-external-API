import numpy as np
import matplotlib.pyplot as plt
import os
import re
import statistics
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
        print("calculate distance for: "+actionSequenceAsString)
        print(damerau_levenshtein_distance(actionSequenceAsString,"tpthbcm"))
    return damerau_levenshtein_distance(actionSequenceAsString,"tpthbcm")


riskThreshold = 1 # action sequences with risk above this threshold contain a collision
filepath = os.getcwd()+"/resultsRandomSearch/16:14:58"

# load file with risk values
riskValues = np.load(filepath+"/risks.npy")
actionSequences = []

# open file with saved action sequences and read the content in a list
with open(filepath + '/actionSequences.txt', 'r') as filehandle:
    filecontents = filehandle.readlines()
    for line in filecontents:
        current_line = line[:-1]
        current_line = re.findall('[a-zA-Z]+', current_line) #current_line.split("'")
        print(current_line)
        actionSequences.append(current_line)

#calculate max, mean, and stdDev of risk values
if len(riskValues) != len(actionSequences):
    print("Error: number of action sequences and risk vectors are not same!")
else:
    # calculate max, mean, and std of risk values
    maximumRisksPerEpisode = list()
    avgRisksPerEpisode = list()
    stdDevRisksPerEpisode = list()
    for riskSequence in riskValues:
        maximumRisksPerEpisode.append(max(riskSequence))

    # Get those action sequences with a risk value above threshold
    actionSequencesAboveThreshold = list()
    riskValuesAboveThreshold = list()
    distancesFromNominalSequence = list()
    for i in range(len(actionSequences)):
        tempSequence = list()
        if max(riskValues[i]) > riskThreshold and max(riskValues[i]) < 5: # <5 because there seems to be a bug that occasionally yields values >>5. This is not realistic in the simulation and likely a bug, so we remove that.
            for j in range(len(actionSequences[i])):
                tempSequence.append(actionSequences[i][j])
                if riskValues[i][j] > riskThreshold:
                    break
            # append sequence only if not already existing (to make sure not action sequences are counted double)
            if not tempSequence in actionSequencesAboveThreshold:
                actionSequencesAboveThreshold.append(tempSequence)
                riskValuesAboveThreshold.append(max(riskValues[i]))
                distancesFromNominalSequence.append(getDistanceFromNominal(tempSequence))

    # Print report to console
    print("Highest risk value discovered: "+str(max(maximumRisksPerEpisode)))
    print("Mean of highest risk values per episode:"+str(statistics.mean(maximumRisksPerEpisode)))
    print("Std Dev of highest risk values per episode:"+str(statistics.stdev(maximumRisksPerEpisode)))
    print("Collisions found: "+str(len(riskValuesAboveThreshold)))
    print("------------- action sequences leading to collision: -------------")
    print(actionSequencesAboveThreshold)
    print(riskValuesAboveThreshold)

    # create scatterplot of risk- and distance values
    plt.grid(True)
    plt.scatter(distancesFromNominalSequence,riskValuesAboveThreshold)
    plt.title("Risk vs. Distance from Nominal Behavior")
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.xlabel("Distance from Nominal Behavior")
    plt.ylabel("Risk Metric")
    plt.show()
