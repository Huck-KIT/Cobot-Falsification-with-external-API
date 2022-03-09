import random
from collections import namedtuple

import matplotlib.pyplot as plt
import numpy as np

import b0RemoteApi

# User settings
random.seed(8)
TUNE = False

Action = namedtuple('action', ['name'])
t = Action("t")  # transition between stations
r_P = Action("rP")  # reach for parts
r_H = Action("rH")  # reach in housing
r_C = Action("rC")  # reach in cover
p_B = Action("pB")  # press button
m_C = Action("mC")  # mount cover
i_A = Action("i_A") # initialize new assembly
actionSpace = [t, r_P, r_H, r_C, p_B, m_C, i_A]


def isFeasible(action, state):
    # actionSpace = [t, r_P, r_H, r_C, p_B, m_C, i_A]
    # stateVector = [intercept, areaA, areaB, parts, robot, gear, rh, rc, cover]
    #                0          1      2      3      4      5     6   7   8
    if not state[2] == 1 and action == 1:
        print('rP not feasible atm')
        return False
    elif not (state[1] and not state[7] and not state[8]) and action == 2:
        print('rH not feasible atm')
        return False
    elif not (state[1] and not state[8]) and action == 3:
        print('rC not feasible atm')
        return False
    elif not (state[1]) and action == 4:
        print('pB not feasible atm')
        return False
    elif not (state[1] and state[3] and not state[8]) and action == 5:
        print('mC not feasible atm')
        return False
    else:
        return True


def learn(args=None):
    num_episodes = 20
    max_steps = 100

    A, B = 500, 1000
    gamma = 0.9

    performance = []

    # Initialize Q-function
    weights = dict()
    for a in range(len(actionSpace)):
        weights[a] = np.zeros(9)

    for l in range(num_episodes):
        # Reset for episode
        x = reset()

        rewards = []

        for m in range(max_steps):
            # Pick action
            if random.random() < pow(0.5, l/2):
                a = random.randint(0, len(actionSpace) - 1)
                max_q = np.asscalar(np.dot(x, weights[a]))
            else:
                max_q = - np.inf
                a = None
                for action, w in weights.items():
                    q_a = np.asscalar(np.dot(x, w))
                    if q_a > max_q:
                        max_q = q_a
                        a = action

            # Step
            if isFeasible(a, x):
                next_x, r, done = step(actionSpace[a])
            else:
                next_x, r, done = x, 0, False
            print("Action:", actionSpace[a].name, "Q-value:", max_q)

            rewards.append(r)

            # Update
            if done:
                max_next_q = 0
            else:
                max_next_q = - np.inf
                for w in weights.values():
                    q_a = np.asscalar(np.dot(next_x, w))
                    if q_a > max_next_q:
                        max_next_q = q_a
            alpha = A / (B + l * m + m)
            weights[a] += alpha * (r + gamma * max_next_q - max_q) * x

            if done:
                break

            # Increment
            x = next_x

        performance.append(sum(rewards))

        plt.plot(performance, 'b.')
        plt.title('Approx. Q-learning over Episodes of {} steps'.format(max_steps))
        plt.xlabel('Episode')
        plt.ylabel('Total Reward')
        plt.show()

    return True


def step(action):
    actionIsSet = False
    actionIsDone = False
    maxRisk = 0
    if action.name == "i_A":
        return reset(), maxRisk, False
    # action loop (1 execution = 1 single action in the simulation)
    while not actionIsDone:
        if not actionIsSet:
            actionIsSet, _ = client.simxCallScriptFunction("setAction@Bill", "sim.scripttype_childscript",
                                                           action.name, client.simxServiceCall())
            client.simxCallScriptFunction("setMotionParameters@Bill", "sim.scripttype_childscript",
                                          [0, 1, 1],
                                          client.simxServiceCall())  # TODO: check that parameters are within limits
            client.simxSynchronousTrigger()
        else:
            _, isRunning = client.simxCallScriptFunction("isHumanModelActive@Bill",
                                                         "sim.scripttype_childscript", 1,
                                                         client.simxServiceCall())
            if not isRunning:
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
    # workflowIsDone = True if action.name == "m_C" else False
    workflowIsDone = False
    new_state = client.simxCallScriptFunction("getStateVector@StateVariablesTracker", "sim.scripttype_childscript",
                                              None, client.simxServiceCall())
    return _augment_state(new_state), maxRisk, workflowIsDone


def _augment_state(state):
    augmented = [1.0]
    for s in state[1:]:
        if s:
            augmented.append(1.0)
        else:
            augmented.append(0.0)
    if not state[1]:
        augmented.insert(2, 1.0)
    else:
        augmented.insert(2, 0.0)
    return np.array(augmented)


def reset():
    client.simxCallScriptFunction("reset@Bill", "sim.scripttype_childscript", 1, client.simxServiceCall())
    print("--------- Reset and start new Assembly ---------")
    new_state = client.simxCallScriptFunction("getStateVector@StateVariablesTracker", "sim.scripttype_childscript",
                                              None, client.simxServiceCall())
    return _augment_state(new_state)


def close():
    client.simxStopSimulation(client.simxServiceCall())


if __name__ == "__main__":
    # This line defines the client, which provides all functions of the remote API
    # the function list can be found here: https://www.coppeliarobotics.com/helpFiles/en/b0RemoteApi-functionList.htm
    with b0RemoteApi.RemoteApiClient('b0RemoteApi_V-REP-addOn',
                                     'b0RemoteApiAddOn') as client:

        # initialize simulation
        client.simxSynchronous(True)
        client.simxStartSimulation(client.simxServiceCall())
        step(actionSpace[0])

        if TUNE:
            print('Tune not implemented')
        else:
            learn()
