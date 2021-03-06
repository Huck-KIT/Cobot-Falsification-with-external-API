import os
import random
from collections import namedtuple, deque
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

import b0RemoteApi

now = datetime.now()
current_time = now.strftime("%H:%M:%S")


# User settings
random.seed(13)
num_episodes = 200
max_steps = 12
filepathForResults = os.getcwd()+"/resultsAQ/"+current_time


if not os.path.exists(filepathForResults):
    os.makedirs(filepathForResults)
print("Results will be saved to: "+filepathForResults)


Action = namedtuple('action', ['name'])
t = Action("t")  # transition between stations
r_P = Action("rP")  # reach for parts
r_H = Action("rH")  # reach in housing
r_C = Action("rC")  # reach in cover
p_B = Action("pB")  # press button
m_C = Action("mC")  # mount cover
i_A = Action("iA")  # initialize new assembly
actionSpace = [t, r_P, r_H, r_C, p_B, m_C, i_A]
nominalAssembly = [t, r_P, t, r_H, p_B, r_C, m_C]


def actionIndecesToString(actionSequence):
    return [actionSpace[i].name for i in actionSequence]


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
    elif not (state[1] and not state[8]) and action == 5:
        print('mC not feasible atm')
        return False
    else:
        return True


class QAgent(object):

    def __init__(self, gamma=0.9, A=100, B=1000, batch_size=25):
        self.gamma = gamma
        self.A = A
        self.B = B
        self.step = 0
        self.batch_size = batch_size
        self.memory = ReplayMemory(10000)

        # Initialize Q-function
        self.weights = dict()
        self.target_weights = dict()
        for a in range(len(actionSpace)):
            self.weights[a] = np.zeros(9)
            self.target_weights[a] = np.zeros(9)

    def policy(self, state):
        # Pick action
        eps = pow(0.75, int(self.step / (10*max_steps)) + 1) # Controls the exploration
        if random.random() < eps:
            a = random.randint(0, len(actionSpace) - 1)
            max_q = np.asscalar(np.dot(state, self.weights[a]))
        else:
            max_q = -np.inf
            a = None
            for action, w in self.weights.items():
                q_a = np.asscalar(np.dot(state, w))
                if q_a > max_q:
                    max_q = q_a
                    a = action
        return a, max_q

    def update(self, state, action, reward, next_state, done):
        self.step += 1
        self.memory.push(state, action, reward, next_state, done)
        if len(self.memory) < self.batch_size:
            return
        for t in self.memory.sample(self.batch_size):
            q = np.asscalar(np.dot(t.state, self.weights[t.action]))
            if t.done:
                max_next_q = 0
            else:
                max_next_q = -np.inf
                for w in self.target_weights.values():
                    q_a = np.asscalar(np.dot(t.next_state, w))
                    if q_a > max_next_q:
                        max_next_q = q_a
            alpha = self.A / (self.B + self.step)
            self.weights[t.action] += alpha * (t.reward + self.gamma * max_next_q - q) * t.state
        for a in range(len(actionSpace)):
            self.target_weights[a] = 0.9 * self.target_weights[a] + 0.1 * self.weights[a]


Transition = namedtuple('Transition', ['state', 'action', 'reward', 'next_state', 'done'])


class ReplayMemory(object):
    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


def learn(args=None):
    Q = QAgent()
    performance = []
    fig, ax = plt.subplots()
    ax.grid(True)
    ax.set_title('Approx. Q-learning over Episodes of {} steps'.format(max_steps))
    ax.set_xlabel('Episode')
    ax.set_ylabel('Total Reward')

    for l in range(num_episodes):
        # Reset for episode
        s = reset()

        rewards = []
        actions = []
        assemblySeq = nominalAssembly.copy()
        completedSeq = 0
        m = 0
        while True:
            # Pick action
            a, max_q = Q.policy(s)

            # Step
            if isFeasible(a, s):
                next_s, r, done = step(actionSpace[a])
            else:
                next_s, r, done = s, 0, False
                Q.update(s, a, r, next_s, done)
                continue
            print("Action:", actionSpace[a].name, "Q-value:", max_q)

            rewards.append(r)
            # Tracking progress on assembly
            if actionSpace[a].name == 'iA':
                assemblySeq = nominalAssembly.copy()
            elif len(assemblySeq) > 0 and actionSpace[a] == assemblySeq[0]:
                assemblySeq.pop(0)
                if len(assemblySeq) == 0:
                    print('---------- Assembly Sequence Completed ----------')
                    completedSeq += 1
                else:
                    print('{} actions left to do in {} steps'.format(len(assemblySeq), max_steps-m-1))

            # Update
            Q.update(s, a, r, next_s, done)

            if done or m == max_steps - 1:
                break

            actions.append(a)

            # Increment
            s = next_s
            m += 1

        performance.append(sum(rewards))

        with open(filepathForResults + '/risks.csv', 'a') as f:
            np.savetxt(f, X=[rewards], delimiter=",")
        with open(filepathForResults + '/actionSequences.txt', 'a') as filehandle:
            filehandle.writelines("%s\n" % actionIndecesToString(acts) for acts in [actions])

        ax.plot(l, sum(rewards), 'b.')
        if completedSeq > 0:
            ax.text(l, sum(rewards), completedSeq)
        fig.tight_layout()
        fig.show()

    return Q


def step(action):
    actionIsSet = False
    actionIsDone = False
    maxRisk = 0
    if action.name == "iA":
        return reset(), maxRisk, True

    motionParametersMin = [-0.2, 0.8, 1]
    motionParametersMax = [0.2, 1.2, 1.5]
    motionParametersNominal = [0, 1, 1]
    # sample random continuous motion parameters
    motionParameters = list()
    for k in range(3):
        param = motionParametersMin[k] + (motionParametersMax[k] - motionParametersMin[k]) * random.random()
        motionParameters.append(param)
    # action loop (1 execution = 1 single action in the simulation)
    while not actionIsDone:
        if not actionIsSet:
            actionIsSet, _ = client.simxCallScriptFunction("setAction@Bill", "sim.scripttype_childscript",
                                                           action.name, client.simxServiceCall())
            client.simxCallScriptFunction("setMotionParameters@Bill", "sim.scripttype_childscript",
                                          motionParameters,
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
    return _augment_state(new_state), min(maxRisk, 5.0), workflowIsDone


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

        learn()
