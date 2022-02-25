from FiniteStateMachine import State, Transition, Automaton

""" Here we define the workflows models (state machines) for the different
simulation scnearios"""

""" ----------------- scenario 1 (original workflow) ---------------------------
This is the workflow according to Fig. 1 in our Overleaf notes.
"""

class Workflow1:
    def __init__(self):
        s_A1N = State("worker at area 1, no parts taken", True, False, [])
        s_A2N = State("worker at area 2, no parts taken", True, False, [])
        s_A1P = State("worker at area 1, parts taken", True, False, [])
        s_A2P = State("worker at area 2, parts taken", True, False, [])
        s_A1E = State("worker at area 1, assembly ended", True, False, [])
        s_A2E = State("worker at area 2, assembly ended", True, False, [])
        self.states = [s_A1N, s_A2N, s_A1P, s_A2P, s_A1E, s_A2E]  # first state in list is taken as initial state

        # Define Transitions
        # NOTE: since we only use the automaton for acceptance checking, we do not use timed transitions or external triggers.
        # Therefore, the durations of the transition are set to 0 and the external triggers to False.
        #                   name            isAutomatic    duration     isTriggeredExternally   setsExternalTrigger
        t = Transition("t", False, 0, False, False)  # transition between stations
        r_P = Transition("rP", False, 0, False, False)  # reach for parts
        r_H = Transition("rH", False, 0, False, False)  # reach in housing
        r_C = Transition("rC", False, 0, False, False)  # reach in cover
        p_B = Transition("pB", False, 0, False, False)  # press button
        m_C = Transition("mC", False, 0, False, False)  # mount cover
        self.actionSpace = [t, r_P, r_H, r_C, p_B, m_C]

        # Define transition matrix (rows: start states, colums: resulting states)
        self.transitions =  [[p_B, t, False, False, False, False],
                            [t, False, False, r_P, False, False],
                            [False, False, [r_H, r_C, p_B], t, m_C, False],
                            [False, False, t, False, False, False],
                            [False, False, False, False, p_B, t],
                            [False, False, False, False, t, False]]

        # Create FSM
        self.workflowModel = Automaton(self.states, self.actionSpace, self.transitions, [])


""" ------------------------ scenario 1 (modified) -----------------------------
This is the workflow according to Fig. 5 in our Overleaf notes (in contrast to
workflow 1, we differentiate between states whether the robot is idle/activated).
 """

class Workflow1Mod():
    def __init__(self):
        s_A1N               = State("worker at area 1, no parts taken",                 True, False, [])
        s_A2N               = State("worker at area 2, no parts taken",                 True, False, [])
        s_A1P_robotIdle     = State("worker at area 1, parts taken, robot idle",        True, False, [])
        s_A1P_robotActive   = State("worker at area 1, parts taken, robot activated",   True, False, [])
        s_A2P               = State("worker at area 2, parts taken",                    True, False, [])
        s_E                 = State("assembly sequence ended",                          True, False, [])
        self.states         = [s_A1N, s_A2N, s_A1P_robotIdle, s_A1P_robotActive, s_A2P, s_E]  # first state in list is taken as initial state

        # Define Transitions
        # NOTE: since we only use the automaton for acceptance checking, we do not use timed transitions or external triggers.
        # Therefore, the durations of the transition are set to 0 and the external triggers to False.
        #                   name            isAutomatic    duration     isTriggeredExternally   setsExternalTrigger
        t   = Transition("t",   False, 0, False, False)  # transition between stations
        r_P = Transition("rP",  False, 0, False, False)  # reach for parts
        r_H = Transition("rH",  False, 0, False, False)  # reach in housing
        r_C = Transition("rC",  False, 0, False, False)  # reach in cover
        p_B = Transition("pB",  False, 0, False, False)  # press button
        m_C = Transition("mC",  False, 0, False, False)  # mount cover
        self.actionSpace = [t, r_P, r_H, r_C, p_B, m_C]

        # Define transition matrix (rows: start states, colums: resulting states)
        self.transitions =  [[p_B,  t,      False,         False,           False,  False    ],
                            [t,     False,  False,         False,           r_P,    False    ],
                            [False, False,  [r_H, r_C],    p_B,             t,      m_C      ],
                            [False, False,  False,         [r_H, r_C, p_B], t,      m_C      ],
                            [False, False,  t,             False,           False,  False    ],
                            [False, False,  False,         False,           False,  False]   ]

        # Create FSM
        self.workflowModel = Automaton(self.states, self.actionSpace, self.transitions, [])

""" ---------------------------------- scenario 2 ------------------------------
This is the workflow according to Fig. 7 in our Overleaf notes.
"""

class Workflow2():
    def __init__(self):
        s_SI    = State("Part at storage, robot idle",                      True, False, [])
        s_SW    = State("Part at storage, robot working (normal)",          True, False, [])
        s_SO    = State("Part at stoarge, robot working (safety override)", True, False, [])
        s_HI    = State("Worker has part, robot idle",                      True, False, [])
        s_HW    = State("Worker has part, robot working (normal)",          True, False, [])
        s_HO    = State("Worker has part, robot working (safety override)", True, False, [])
        s_RI    = State("Robot has part, robot idle",                       True, False, [])
        s_RW    = State("Robot has part, robot working (normal)",           True, False, [])
        s_RO    = State("Robot has part, robot working (safety override)",  True, False, [])
        self.states = [s_SI, s_SW, s_SO, s_HI, s_HW, s_HO, s_RI, s_RW, s_RO]  # first state in list is taken as initial state

        # Define Transitions
        # NOTE: since we only use the automaton for acceptance checking, we do not use timed transitions or external triggers.
        # Therefore, the durations of the transition are set to 0 and the external triggers to False.
        #                   name            isAutomatic    duration     isTriggeredExternally   setsExternalTrigger
        p   = Transition("p",   False, 0, False, False)  # get part from storage/put it back
        f   = Transition("f",   False, 0, False, False)  # feed part to robot/retreive it
        b_W = Transition("b_W", False, 0, False, False)  # press button to activate robot (normal)
        b_O = Transition("b_O", False, 0, False, False)  # press button to activate robot in safety override mode
        w   = Transition("w",   False, 0, False, False)  # wait
        i   = Transition("i",   False, 0, False, False)  # inspect
        self.actionSpace = [p, f, b_W, b_O, w, i]

        # Define transition matrix (rows: start states, colums: resulting states)
        #                       s_SI    s_SW    s_WO    s_HI    s_HW    s_HO    s_RI    s_RW    s_RO
        self.transitions =     [[w,     b_W,    b_O,    p,      False,  False,  False,  False,  False],
                                [b_W,   w,      False,  False,  p,      False,  False,  False,  False],
                                [b_O,   False,  w,      False,  False,  p,      False,  False,  False],
                                [p,     False,  False,  w,      False,  False,  f,      False,  False],
                                [False, p,      False,  False,  w,      False,  False,  f,      False],
                                [False, False,  p,      False,  False,  w,      False,  False,  f    ],
                                [False, False,  False,  f,      False,  False,  [w,i],  b_W,    b_O  ],
                                [False, False,  False,  False,  f,      False,  b_W,    [w,i],  False],
                                [False,  False,  False,  False, False,  f,      b_O,    False,  [w,i]]]

        # Create FSM
        self.workflowModel = Automaton(self.states, self.actionSpace, self.transitions, [])
