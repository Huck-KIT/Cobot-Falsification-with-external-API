import random

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from skopt import gp_minimize

import b0RemoteApi
from FiniteStateMachine import State, Transition, Automaton
from Workflows import Workflow1, Workflow1Mod

################################# USER SETTINGS ################################
# User settings
USE_RANDOM_ACTIONS = False  # True =  actions are sampled randomly from the action space. False = A default action sequence will be used
USE_MAX_REWARDS = True # False = reward is obtained in each step of the episode. False = Max. reward is tracked during episode and returned at the end of episode


############################# LOAD WORKFLOW MODEL ##############################

#workflow = Workflow1()      # scenario 1, original workflow
workflow = Workflow1Mod()   # scenario 1, modified workflow

workflowModel = workflow.workflowModel #Automaton(states, actionSpace, trans, [])
states = workflow.states
trans = workflow.transitions
actionSpace = workflow.actionSpace
workflowModel.setVerbosity(False)

ITERATION = 0

############################ CONTROL SIMULATION ################################
with b0RemoteApi.RemoteApiClient('b0RemoteApi_V-REP-addOn',
                                 'b0RemoteApiAddOn') as client:  # This line defines the client, which provides all functions of the remote API
    # the function list can be found here: https://www.coppeliarobotics.com/helpFiles/en/b0RemoteApi-functionList.htm
    def learn(args=None):
        epsilon = 0.1
        gamma = 0.9
        A = 200
        B = 400
        if args:
            print(args)
            epsilon = args[0]
            gamma = args[1]
            A = args[2]
            B = args[3]

        # initialize simulation
        client.simxSynchronous(True)
        client.simxStartSimulation(client.simxServiceCall())  # use client to start the simulation
        actionHistory = list()
        paramsMin = [-0.2, 0.8, 1]
        paramsMax = []

        def step(action):
            actionIsSet = False
            actionIsDone = False
            workflowIsDone = False
            maxRisk = 0

            # action loop (1 execution = 1 single action in the simulation)
            while (not actionIsDone):
                if (not actionIsSet):
                    actionIsSet, _ = client.simxCallScriptFunction("setAction@Bill", "sim.scripttype_childscript",
                                                                   action.name, client.simxServiceCall())
                    client.simxCallScriptFunction("setMotionParameters@Bill", "sim.scripttype_childscript",
                                                  [0, 1, 1],
                                                  client.simxServiceCall())  # TODO: check that parameters are within limits
                    if actionIsSet:
                        print("New action was set: " + action.name)
                        actionHistory.append(action)
                        isAccepted = workflowModel.setInputSequence(actionHistory)
                        if not isAccepted:
                            print(
                                "Warning! Action " + action.name + " is not feasible in the current state! Workflow has been terminated")
                            workflowIsDone = True
                            actionSequenceIndex = 0
                            actionIsSet = False
                            actionIsDone = True
                            client.simxCallScriptFunction("reset@Bill", "sim.scripttype_childscript", 1,
                                                          client.simxServiceCall())
                        else:
                            workflowModel.currentTransition, workflowModel.nextStateIndex = workflowModel.getNextTransition(
                                workflowModel.transitions[workflowModel.currentStateIndex],
                                workflowModel.inputSequence[-1])
                            workflowModel.currentStateIndex = workflowModel.nextStateIndex
                    client.simxSynchronousTrigger()
                else:
                    _, isRunning = client.simxCallScriptFunction("isHumanModelActive@Bill",
                                                                 "sim.scripttype_childscript", 1,
                                                                 client.simxServiceCall())
                    if (not isRunning):
                        _, maxRisk = client.simxCallScriptFunction("getMaxRisk@RiskMetricCalculator",
                                                                   "sim.scripttype_childscript", 1,
                                                                   client.simxServiceCall())
                        client.simxCallScriptFunction("resetMaxRisk@RiskMetricCalculator",
                                                      "sim.scripttype_childscript",
                                                      1,
                                                      client.simxServiceCall())
                        actionIsSet = False
                        actionIsDone = True
                    else:
                        client.simxSynchronousTrigger()

            return workflowModel.currentStateIndex, maxRisk, workflowIsDone

        def reset():
            client.simxCallScriptFunction("reset@Bill", "sim.scripttype_childscript", 1, client.simxServiceCall())
            print("--------- Reset and start new Episode ---------")
            workflowModel.reset()
            actionHistory = list()
            return workflowModel.currentStateIndex, actionHistory

        def close():
            client.simxStopSimulation()

        def setup_plotting():
            w = 6
            h = 6
            fig = plt.figure(figsize=(6, 9))
            gs = GridSpec(4, 3, figure=fig)

            ax = fig.add_subplot(gs[1:, :])
            ax.set_aspect(w / h)
            ax.set_title('Q-Tabel')
            # ax.set_xlim(-.5, w + .5)
            # ax.set_ylim(-.5, h + .5)
            q_tabel = ax

            ax = fig.add_subplot(gs[0, :])
            ax.grid(True)
            ax.set_xlabel('Episode')
            ax.xaxis.set_label_position('top')
            ax.xaxis.tick_top()
            ax.set_ylabel('Total Reward')
            # ax.set_ylim(-2, 8)
            scatter_plot = ax

            return fig, q_tabel, scatter_plot

        def initialize_Q(states, actions):
            """
            Initializes the Q-table as a dictionary of dictionaries.

            A particular Q-value can be retrieved by calling Q[x][a].
            All actions and their associated values in a state x can
            be retrieved through Q[x].
            Q-values are initialized to a small random value to encourage
            exploration and to facilitate learning.

            :param states: iterable set of states
            :param actions: iterable set of actions
            """
            return {x: {a: random.random() * 1.0 for a in actions} for x in states}

        def argmax_Q(Q, state):
            """Computes the argmax of Q in a particular state."""
            max_q = float("-inf")
            argmax_q = None
            for a, q in Q[state].items():
                if q > max_q:
                    max_q = q
                    argmax_q = a
            return argmax_q

        def choose_epsilon_greedily(Q, x, epsilon):
            """
            Chooses random action with probability epsilon, else argmax_a(Q(*|x))

            :param Q: Q-table as dict of dicts
            :param x: state
            :param epsilon: float
            """
            _, feasibleActionIndices = workflowModel.getFeasibleActions()
            # print("------")
            # print("current state: "+states[workflowModel.currentStateIndex].name)
            # print("feasible actions: ")
            # for index in feasibleActionIndices:
            #     print(actionSpace[index].name)
            # print("------")
            if random.random() < epsilon:
                #return random.choice(list(Q[x].keys # sample from whole action actionSpace
                return random.choice(feasibleActionIndices) # sample only from subset of action space that is actually feasible
            action = argmax_Q(Q, x)
            return action

        num_episodes = 75
        max_steps = 8
        Q = initialize_Q([i for i in range(len(states))], [j for j in range(len(actionSpace))])
        performance = []
        fig, q_tabel, scatter_plot = setup_plotting()
        for l in range(num_episodes):
            # Reset for episode
            x, actionHistory = reset()
            done = False
            rewards = 0
            r_max = 0

            for m in range(max_steps):
                # Pick action
                a = choose_epsilon_greedily(Q, x, epsilon)
                next_x, r, done = step(actionSpace[a])

                """
                # hack by tom: track maximum reward during episode and only return it at the end of episode (all steps inbetween give 0)
                if USE_MAX_REWARDS:
                    # track maximum of the rewards occuring during the episode
                    if r > r_max:
                        r_max = r
                if done or m == max_steps-1:
                    # return the maximum at the end of episode
                    r = r_max
                    r_max = 0
                else:
                    # no intermediate rewards (i.e., during episode) is given.
                    r = 0
                """

                print("collected reward in this step: " + str(r))

                # Update Q-Table
                alpha = A / (B + l)
                max_next_Q = max(Q[next_x].values())
                Q[x][a] = (1 - alpha) * Q[x][a] + alpha * (r + gamma * max_next_Q)

                # Increment
                x = next_x
                rewards += r
                if done:
                    # Set the Q-values of the terminal state to 0
                    Q[next_x][a] = 0
                    break

            performance.append(rewards)
            scatter_plot.plot(l, rewards, 'b.')
            if (l + 1) % 25 == 0:
                print('c')
                q_tabel.clear()
                q_tabel.imshow(
                    [[Q[state][action] for state in range(len(states))] for action in range(len(actionSpace))])

                # Show all ticks and label them with the respective list entries
                q_tabel.set_yticks(np.arange(len(actionSpace)))
                q_tabel.set_yticklabels([a.name for a in actionSpace])
                q_tabel.set_xticks(np.arange(len(states)))
                q_tabel.set_xticklabels([s.name for s in states])

                # Rotate the tick labels and set their alignment.
                plt.setp(q_tabel.get_xticklabels(), rotation=65, ha="right",
                         rotation_mode="anchor")

                for i in range(len(states)):
                    for j in range(len(actionSpace)):
                        text = q_tabel.text(i, j, "{0:.2f}".format(Q[i][j]),
                                            ha="center", va="center", color="w")
                q_tabel.set_title('Q-Tabel')
                fig.tight_layout()
                fig.show()
        # close()

        #return - (sum(performance) + 10 * max(performance))
        return max(performance)


    if __name__ == "__main__":
        tune = False
        if tune:
            res = gp_minimize(learn, dimensions=[(0.05, 0.5), (0.3, 0.99), (50, 500), (500, 1000)],
                              x0=[0.1, 0.9, 400, 500], n_calls=50, n_jobs=-1, verbose=True)
            print(res)
        else:
            #learn([0.05, 0.99, 500, 500]) # original
            learn([0.2, 0.99, 500, 500])
