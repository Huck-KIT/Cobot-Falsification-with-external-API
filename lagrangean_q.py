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
TUNE = False
num_episodes = 10
max_steps = 12
batchsize = 3 * max_steps
memorysize = int(1.0 * num_episodes * max_steps)
reset_memory = False
ALPHA = 0.1
DELTA0 = 0.25
action_label_spec = True
filepathForResults = os.getcwd() + "/resultsLQ/" + current_time

if not os.path.exists(filepathForResults):
    os.makedirs(filepathForResults)
print("Results will be saved to: " + filepathForResults)

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
    # stateVector = [intercept, areaA, areaB, parts, robot, gear, rh, rc, cover, reset]
    #                0          1      2      3      4      5     6   7   8
    if not state[2] == 1 and action == 1:
        # print('rP not feasible atm', state)
        return False
    elif not (state[1] and not state[5] and not state[8]) and action == 2:
        # print('rH not feasible atm', state)
        return False
    elif not (state[1] and not state[8]) and action == 3:
        # print('rC not feasible atm', state)
        return False
    elif not (state[1]) and action == 4:
        # print('pB not feasible atm', state)
        return False
    elif not (state[1] and not state[8]) and action == 5:
        # print('mC not feasible atm', state)
        return False
    else:
        return True


do_indices = [0, 2, 4, 7, 9, 11, 13, 15]


class Spec(object):

    def __init__(self, multipliers):
        self.multipliers = multipliers.copy()
        self.C = [[]] * len(multipliers)
        self.current_state = 0
        self.states = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        if action_label_spec:
            # actionSpace = [t, r_P, r_H, r_C, p_B, m_C, i_A]
            #                0  1    2    3    4    5    6
            #          spec_state   label sign multiplier index  next_spec_state
            self.transitions = {0: {0: (+1, 0, 1),
                                    },
                                1: {0: (-1, 1, 0),
                                    1: (+1, 2, 2),
                                    6: (-1, 3, 8)
                                    },
                                2: {0: (+1, 4, 3),
                                    6: (-1, 5, 8)
                                    },
                                3: {0: (-1, 6, 2),
                                    2: (+1, 7, 4),
                                    6: (-1, 8, 8)
                                    },
                                4: {4: (+1, 9, 5),
                                    6: (-1, 10, 8)
                                    },
                                5: {3: (+1, 11, 6),
                                    6: (-1, 12, 8)
                                    },
                                6: {5: (+1, 13, 7),
                                    6: (-1, 14, 8)
                                    },
                                7: {6: (+1, 15, 0)
                                    },
                                }
        else:
            # stateVector = [intercept, areaA, areaB, parts, robot, gear, rh, rc, cover, reset]
            #                0          1      2      3      4      5     6   7   8      9
            #          spec_state   label sign multiplier index  next_spec_state
            self.transitions = {0: {2: (+1, 0, 1),
                                    },
                                1: {1: (-1, 1, 0),
                                    3: (+1, 2, 2),
                                    9: (-1, 3, 8)
                                    },
                                2: {1: (+1, 4, 3),
                                    9: (-1, 5, 8)
                                    },
                                3: {2: (-1, 6, 2),
                                    6: (+1, 7, 4),
                                    9: (-1, 8, 8)
                                    },
                                4: {5: (+1, 9, 5),
                                    9: (-1, 10, 8)
                                    },
                                5: {7: (+1, 11, 6),
                                    9: (-1, 12, 8)
                                    },
                                6: {8: (+1, 13, 7),
                                    9: (-1, 14, 8)
                                    },
                                7: {9: (+1, 15, 0)
                                    },
                                }

    def _encode_state(self, state):
        encoded = np.zeros(len(self.states))
        encoded[state] = 1.0
        return encoded

    def check(self, labels):
        r = 6 if action_label_spec else 9
        if labels[r] and self.transitions[self.current_state].get(r, None):
            c = self.transitions[self.current_state][r][0] * self.multipliers[
                self.transitions[self.current_state][r][1]]
            for i in range(len(self.multipliers)):
                if i == self.transitions[self.current_state][r][1]:
                    self.C[self.transitions[self.current_state][r][1]].append(c)
                else:
                    self.C[i].append(0)
            print('########################### Spec satisfied:', self.current_state, r, c, 0)
            self.current_state = self.transitions[self.current_state][r][2]
            return self._encode_state(self.current_state), c
        for l, t in self.transitions[self.current_state].items():
            if labels[l] == 1.0:
                c = t[0] * self.multipliers[t[1]]
                for i in range(len(self.multipliers)):
                    if i == t[1]:
                        self.C[t[1]].append(c)
                    else:
                        self.C[i].append(0)
                print('########################### Spec satisfied:', self.current_state, l, c, t[2])
                self.current_state = t[2]
                return self._encode_state(self.current_state), c
        return self._encode_state(self.current_state), 0

    def reset(self):
        self.current_state = 0
        self.C = [[]] * len(self.multipliers)
        return self._encode_state(self.current_state)


class QAgent(object):

    def __init__(self, gamma=0.9, A=100, B=1000, batch_size=10):
        self.gamma = gamma
        self.A = A
        self.B = B
        self.step = 0
        self.batch_size = batch_size
        self.memory = ReplayMemory(memorysize)

        # Initialize Q-function
        self.weights = dict()
        self.target_weights = dict()
        for a in range(len(actionSpace)):
            self.weights[a] = np.zeros(19)
            self.target_weights[a] = np.zeros(19)

    def policy(self, state):
        # Pick action
        eps = pow(0.5, int(self.step / (2 * max_steps)) + 1)
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
            # alpha = self.A / (self.B + self.step)
            alpha = ALPHA
            self.weights[t.action] += alpha * (t.reward + self.gamma * max_next_q - q) * t.state
        for a in range(len(actionSpace)):
            self.target_weights[a] = 0.9 * self.target_weights[a] + 0.1 * self.weights[a]

    def reset(self):
        self.step = 0
        if reset_memory:
            self.memory = ReplayMemory(memorysize)


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


def learn(args=None, multipliers=None):
    Q = QAgent()
    multipliers = np.ones(16)
    A, B, t = 0.16, 5, 0.501

    # Reporting
    performance = []
    fig, ax = plt.subplots()
    ax.grid(True)
    ax.set_title('Approx. Q-learning over Episodes of {} steps'.format(max_steps))
    ax.set_xlabel('Episode')
    ax.set_ylabel('Total Reward')

    fig2, ax2 = plt.subplots()
    ax2.grid(True)

    offset = 0

    fig3, axs3 = plt.subplots(len(multipliers), figsize=[6.4, 20.0], sharex=True)
    fig3.suptitle('Multipliers')

    def run_episodes(sp, os):
        L = 0
        L_ls = []
        Q.reset()
        trans = []
        for l in range(num_episodes):
            # Reset for episode
            s = reset()
            q = sp.reset()

            rewards = []
            constraints = []
            actions = []
            assemblySeq = nominalAssembly.copy()
            completedSeq = 0
            m = 0
            while True:
                # Pick action
                a, max_q = Q.policy(np.append(s, q))
                # print("Action:", actionSpace[a].name, "Q-value:", max_q)

                # Step
                if isFeasible(a, s):
                    next_s, r, done = step(actionSpace[a])
                    if action_label_spec:
                        a_label = [0] * len(actionSpace)
                        a_label[a] = 1
                        next_q, c = sp.check(a_label)
                    else:
                        next_q, c = sp.check(next_s)
                else:
                    next_s, r, done = s, 0, False
                    next_q, c = q, 0
                    Q.update(np.append(s, q), a, r + c, np.append(next_s, next_q), done)
                    trans.append(s.tolist() + q.tolist() + [a, r, c] + next_s.tolist() + next_q.tolist() + [done])
                    continue

                # done = True if m == max_steps - 1 else False

                actions.append(a)
                rewards.append(r)
                constraints.append(c)
                # Tracking progress on assembly
                if actionSpace[a].name == 'iA':
                    assemblySeq = nominalAssembly.copy()
                elif len(assemblySeq) > 0 and actionSpace[a] == assemblySeq[0]:
                    assemblySeq.pop(0)
                    if len(assemblySeq) == 0:
                        print(
                            '!!!!!!!!!!!!!!!!!!!---------- Assembly Sequence Completed ----------!!!!!!!!!!!!!!!!!!!!')
                        completedSeq += 1
                    else:
                        print('{} actions left to do in {} steps'.format(len(assemblySeq), max_steps - m - 1))

                # Update
                Q.update(np.append(s, q), a, r + c, np.append(next_s, next_q), done)
                trans.append(s.tolist() + q.tolist() + [a, r, c] + next_s.tolist() + next_q.tolist() + [done])

                if done or m == max_steps - 1:
                    break

                # Increment
                s = next_s
                q = next_q
                m += 1

            performance.append(sum(rewards))

            with open(filepathForResults + '/risks.csv', 'a') as f:
                np.savetxt(f, X=[rewards], delimiter=",")
            with open(filepathForResults + '/actionSequences.txt', 'a') as filehandle:
                filehandle.writelines("%s\n" % actionIndecesToString(acts) for acts in [actions])
            print(actionIndecesToString(actions))

            L_l = sum([Q.gamma ** k * r for k, r in enumerate(rewards)])
            for i, m in enumerate(sp.multipliers):
                if i in do_indices:
                    for q, ts in sp.transitions.items():
                        for t in ts.values():
                            if i == t[1]:
                                target_step = q
                    L_l += m * (sum([Q.gamma ** k * c for k, c in enumerate(sp.C[i])]) - np.floor(
                        max_steps / 8) * m * Q.gamma ** target_step)
                else:
                    L_l += m * sum([Q.gamma ** k * c for k, c in enumerate(sp.C[i])])

            L = 0.9 * L + 0.1 * L_l
            L_ls.append(L_l)

            ax.plot(os + l, sum(rewards), 'b.')
            if completedSeq > 0:
                ax.text(os + l, sum(rewards), completedSeq)
            ax.plot(os + l, sum(constraints), 'r*')

        fig.tight_layout()
        fig.show()

        with open('transitions.csv', 'a') as f:
            np.savetxt(f, X=trans, delimiter=",")
        print(L_ls)
        return L

    # Pretrain
    for i in range(1):
        spec = Spec(np.ones(16))
        run_episodes(spec, offset)
        offset += num_episodes

    for k in range(1, 51):
        mu = A / pow(B + k, 0.602)
        h = np.random.choice([-1, 1], len(multipliers)) * DELTA0 / pow(k, t)
        u_minus = np.clip(multipliers - h, 0, 1000)
        spec = Spec(u_minus)
        y_minus = run_episodes(spec, offset)
        offset += num_episodes
        u_plus = np.clip(multipliers + h, 0, 1000)
        spec = Spec(u_plus)
        y_plus = run_episodes(spec, offset)
        offset += num_episodes
        multipliers -= np.clip(mu * (y_plus - y_minus) / (2 * h), -0.5, 0.5)

        # Reporting
        ax2.plot(k, y_plus, 'b.')
        ax2.plot(k, y_minus, 'r*')
        fig2.tight_layout()
        fig2.show()

        for i, m in enumerate(multipliers):
            axs3[i].plot(k, m, 'b.')
            axs3[i].set_ylabel(i)
        fig3.tight_layout()
        fig3.show()

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
    return _augment_state(new_state + [False]), min(maxRisk, 5.0), workflowIsDone


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
    return _augment_state(new_state + [True])


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
