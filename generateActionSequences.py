import sys
import itertools
from FiniteStateMachine import State, Transition, Automaton

########################### DEFINE STATES ######################################
#               state description                       isAcceptingFinalState   isTerminal  Truth table (optioal; not used here)
s_A1N   = State("worker at area 1, no parts taken",     True,                   False,  [])
s_A2N   = State("worker at area 2, no parts taken",     True,                   False,  [])
s_A1P   = State("worker at area 1, parts taken",        True,                   False,  [])
s_A2P   = State("worker at area 2, parts taken",        True,                   False,  [])
s_A1E   = State("worker at area 1, assembly ended",     True,                   False,  [])
s_A2E   = State("worker at area 2, assembly ended",     True,                   False,  [])
states  = [s_A1N,s_A2N,s_A1P,s_A2P,s_A1E,s_A2E] #first state in list is taken as initial state

########################### DEFINE TRANSITIONS #################################
# NOTE: since we only use the automaton for acceptance checking, we do not use timed transitions or external triggers.
# Therefore, the durations of the transition are set to 0 and the external triggers to False.
#                   name            isAutomatic    duration     isTriggeredExternally   setsExternalTrigger
t       = Transition("t",           False,         0,           False,                  False) # transition between stations
r_P     = Transition("rP",          False,         0,           False,                  False) # reach for parts
r_H     = Transition("rH",          False,         0,           False,                  False) # reach in housing
r_C     = Transition("rC",          False,         0,           False,                  False) # reach in cover
p_B     = Transition("pB",          False,         0,           False,                  False) # press button
m_C     = Transition("mC",          False,         0,           False,                  False) # mount cover

# transition matrix (rows: start states, colums: resulting states)
trans    = [[p_B,   t,      False,          False,  False,  False],
            [t,     False,  False,          r_P,    False,  False],
            [False, False,  [r_H,r_C,p_B],  t,      m_C,    False],
            [False, False,  t,              False,  False,  False],
            [False, False,  False,          False,  p_B,    t    ],
            [False, False,  False,          False,  t,      False]]

# create automaton for worker
workflowModel = Automaton(states,trans,[])
workflowModel.setVerbosity(False)

# create cartesian product of action space for action sequences of length six (A^7)
actionSpace = [t,r_P,r_H,r_C,p_B,m_C]
cartesianProduct = list(itertools.product(actionSpace,actionSpace,actionSpace,actionSpace,actionSpace,actionSpace,actionSpace))
print(str(len(cartesianProduct))+" possible action sequences generated")
#
# testSequence = [t,r_P,t,r_H,p_B,r_C,m_C]
# testAccepted = workflowModel.setInputSequence(testSequence)
# print("test sequence accepted: "+str(testAccepted))

# only add action sequences that are accepted by the automaton
feasibleSequences = []
actionSequenceLog = open("actionSequences.txt","a")
actionSequenceLog.write("{")
for actionSequence in cartesianProduct:
    print("\n------------------------")
    sequenceString = "{"
    for i in range(len(actionSequence)):
        sequenceString += actionSequence[i].name
        if not i == len(actionSequence)-1:
            sequenceString += ","
    sequenceString += "},\n"
    isAccepted = workflowModel.setInputSequence(actionSequence)
    print("Sequence: \t"+sequenceString)
    print("Is feasible: \t"+str(isAccepted))
    if isAccepted:
        feasibleSequences.append(actionSequence)
        actionSequenceLog.write(sequenceString)
actionSequenceLog.write("}")
actionSequenceLog.close()

print("Out of "+str(len(cartesianProduct))+" possible action sequences, "+str(len(feasibleSequences))+" are feasible:")

# for actionSequence in feasibleSequences:
#     print("\n------------------------")
#     sequenceString = "{"
#     for i in range(len(actionSequence)):
#         sequenceString += actionSequence[i].name
#         if not i == len(actionSequence)-1:
#             sequenceString += ","
#     sequenceString += "},"
#     print("Sequence: \t"+sequenceString)
