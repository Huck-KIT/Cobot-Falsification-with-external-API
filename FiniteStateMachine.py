class State:
  def __init__(self, name, isAcceptedFinalState, isTerminal, truthTable):
    self.name = name
    self.isAcceptedFinalState = isAcceptedFinalState # to be accepted, a sequence must end in an accepted final state
    self.isTerminal = isTerminal # in a terminal state, the sequence ends immediately (while being accepted)
    self.truthTable = truthTable

class Transition:
  def __init__(self, name, isAutomatic, duration, isTriggeredExternally, setsExternalTrigger):
    self.isAutomatic = isAutomatic
    self.name = name
    self.duration = duration
    self.isTriggeredExternally = isTriggeredExternally
    self.setsExternalTrigger = setsExternalTrigger
    self.triggerActive = False
    self.isActive = False

class Automaton:
    def __init__(self, states, transitions, truthTableNames):
        self.states = states
        self.numberOfStates = len(states)
        self.transitions = transitions
        self.currentStateIndex = 0
        self.currentInputIndex = 0
        self.clockLocal = 0 # is reset for each transition
        self.clockGlobal = 0 # runs all the time without reset
        self.nextStateIndex = 0
        self.inTransition = False
        self.inputSequence = list()
        self.isVerbose = False
        self.isRunning = False
        self.stateLog = list()
        self.truthTableNames = truthTableNames
        # check dimensions and print warning if they don't fit!
        if len(self.transitions) != self.numberOfStates:
            print("Error! Number of rows in transition matrix is not same as number of states!")
        else:
            for i in range(len(self.transitions)):
                if len(self.transitions[i]) != self.numberOfStates:
                    print("Error! Length of transition matrix "+str(i)+"-th row is not same as number of states!")

    def reset(self):
        self.currentStateIndex = 0
        self.currentInputIndex = 0
        self.clockLocal = 0 # is reset for each transition
        self.clockGlobal = 0 # runs all the time without reset
        self.nextStateIndex = 0
        self.inTransition = False
        self.inputSequence = list()
        self.isVerbose = False
        self.isRunning = False
        self.stateLog = list()

    def setInputSequence(self,inputSequence):
        if self.isVerbose:
            print("check acceptance...")
        if self.checkAcceptance(inputSequence):
            self.inputSequence = inputSequence
            return True
        else:
            return False

    def checkAcceptance(self,inputSequence):
        currentStateIndexLocal = 0 # initial state
        currentInputIndexLocal = 0 # first input symbol
        if self.isVerbose:
            print("input length: "+str(len(inputSequence)))
        while currentInputIndexLocal < len(inputSequence) or self.hasAutomaticTransition(currentStateIndexLocal):
            transitionAccepted = False
            if currentInputIndexLocal < len(inputSequence):
                nextTransition, nextStateIndex = self.getNextTransition(self.transitions[currentStateIndexLocal],inputSequence[currentInputIndexLocal])
            else:
                # in case input sequence has ended, but there are still automatic transitions --> set inputTransition to 'None' to avoid list index being out of range.
                nextTransition, nextStateIndex = self.getNextTransition(self.transitions[currentStateIndexLocal],None)
            if not nextTransition == False:
                currentStateIndexLocal = nextStateIndex
                transitionAccepted = True
                if nextTransition.isAutomatic and self.isVerbose:
                    print("automatic transition leads to state '"+str(self.states[currentStateIndexLocal].name)+"'")
                elif self.isVerbose:
                    print("'"+inputSequence[currentInputIndexLocal].name+"' leads to state '"+str(self.states[currentStateIndexLocal].name)+"'")
                if not nextTransition.isAutomatic:
                    currentInputIndexLocal += 1
            else:
                transitionAccepted = False
                if self.isVerbose and not self.states[currentStateIndexLocal].isTerminal:
                    print("No feasible transition found in state '"+str(self.states[currentStateIndexLocal].name)+"'. ")
                    print("Input is '"+str(inputSequence[currentInputIndexLocal].name)+"', but this transition is not possible in the current state.")
                break
        if self.states[currentStateIndexLocal].isTerminal or (transitionAccepted and self.states[currentStateIndexLocal].isAcceptedFinalState):
            return True
        else:
            return False

    def hasAutomaticTransition(self,stateIndex):
        for transition in range(len(self.transitions[stateIndex])):
            if not (self.transitions[stateIndex][transition] == False or isinstance(self.transitions[stateIndex][transition],list)):
                if self.transitions[stateIndex][transition].isAutomatic:
                    return True
        return False

    def setVerbosity(self, isVerbose):
        self.isVerbose = isVerbose

    def getNextTransition(self, transitionList, inputTransition):
        # returns next transition and index of resulting state if a transition is possible and 'False' if not.
        # if multiple transitions are possible, the one with the shortest duration wins.
        acceptedTransition = False
        nextStateIndex = None
        for i in range(len(transitionList)):
            if not transitionList[i] == False:
                if isinstance(transitionList[i],list):# in case of list of transitions e.g. [r_H,r_C,p_B] in transition table in generateActionSequence.py
                    for j in range(len(transitionList[i])):
                        if transitionList[i][j].isAutomatic or transitionList[i][j] == inputTransition:#transitions are accepted if they are automatic or if the correspond with the current input transition
                            acceptedTransition = transitionList[i][j]
                            nextStateIndex = i
                elif transitionList[i].isAutomatic or transitionList[i] == inputTransition: # in case of single transition
                    acceptedTransition = transitionList[i]
                    nextStateIndex = i
        return acceptedTransition, nextStateIndex

    def iterate(self,timestep,externalTriggerInput):
        externalTriggerOutput = False

        ######################### print and log current state #########################
        if self.isVerbose:
            print("----------------------------")
            print("time: "+str(self.clockGlobal))
            print("current state: '"+self.states[self.currentStateIndex].name+"")
            print("clock local: "+str(self.clockLocal))
        self.stateLog.append(self.states[self.currentStateIndex])
        ###################### get initial transition: #########################
        if not self.isRunning: #
            self.currentTransition, self.nextStateIndex = self.getNextTransition(self.transitions[self.currentStateIndex],self.inputSequence[self.currentInputIndex])
            self.isRunning = True
        if not self.currentTransition==False:
            if self.currentTransition.isTriggeredExternally and externalTriggerInput:
                self.currentTransition.triggerActive = True
                if self.isVerbose:
                    print("External input has triggered transition")
        if self.isVerbose and not self.currentTransition == False:
            print("In transition '"+self.currentTransition.name+"'")

        ########## update state and transition after a certain duration ########
        if not self.currentTransition == False:
            if self.clockLocal >= self.currentTransition.duration:
                if self.isVerbose:
                    print("clock local exceeded duration")
                if self.currentTransition.setsExternalTrigger:
                    externalTriggerOutput = True
                self.currentTransition.triggerActive = False # reset activation
                if not self.currentTransition.isAutomatic:
                    self.currentInputIndex+=1 # increment only if an input action was performed, not in case of an automatic transition!
                self.currentStateIndex = self.nextStateIndex
                self.inTransition = False
                if self.isVerbose:
                    print("Transition completed!")
                    print("New state: '"+str(self.states[self.currentStateIndex].name)+"'")
                if self.currentInputIndex < len(self.inputSequence):
                    self.currentTransition, self.nextStateIndex = self.getNextTransition(self.transitions[self.currentStateIndex],self.inputSequence[self.currentInputIndex])
                else:
                    self.currentTransition, self.nextStateIndex = self.getNextTransition(self.transitions[self.currentStateIndex],None)
                #self.inTransition = True
                if self.isVerbose:
                    print("reset local clock")
                self.clockLocal = 0 #reset clock for new transition
                if self.isVerbose and not self.currentTransition == False:
                    print("New transition '"+self.currentTransition.name+"'")

        ############################ update clocks #############################
        #Note: In case of externally triggered transition, the local clock only strats to run after the transition has been triggered.
        if not self.currentTransition == False:
            if self.currentTransition.isTriggeredExternally and not self.currentTransition.triggerActive:
                pass
            else:
                self.clockLocal+=timestep
        self.clockGlobal+=timestep

        ##### check if end of sequence or terminal state have been reached #####
        if (self.currentInputIndex < len(self.inputSequence) or self.hasAutomaticTransition(self.currentStateIndex)) and not self.states[self.currentStateIndex].isTerminal:
            isActive = True
        else:
            isActive = False
        return isActive,externalTriggerOutput

    def printLog(self):
        truthTable = list()
        for i in range(len(self.stateLog)):
            truthTable.append(self.stateLog[i].truthTable)
        outputLine = "step \t"
        for i in range(len(self.truthTableNames)):
            outputLine += str(self.truthTableNames[i]) + "\t"
        outputLine += "state description"
        print("\n")
        print(outputLine)
        print("---------------------------------------------------------------")
        for i in range(len(truthTable)):
            outputLine = str(i)+"\t"
            for j in range(len(truthTable[i])):
                outputLine += str(truthTable[i][j]) + "\t"
            outputLine += self.stateLog[i].name
            print(outputLine)
        print("\n")




    def getTruthTable(self):
        # returns a list of truth tables (one table for for each timestep)
        truthTable = list()
        # truthTable.append(self.stateLog[0].truthTable)
        for i in range(len(self.stateLog)):
            truthTable.append(self.stateLog[i].truthTable)
        return truthTable
