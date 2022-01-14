import b0RemoteApi
import time
import random
import math
from julia.api import Julia
jl = Julia(compiled_modules=False)
from julia import Base
from julia import AdaptiveStressTesting
from julia import ASTInterfaceTesting

def init_sim(sim):
	print("initialize")

MAXTIME = 25 #sim endtime
RNG_LENGTH = 2
SIGMA = 1.0 #standard deviation of Gaussian
SEED = 1 
	
sim_params = ASTInterfaceTesting.Walk1DParams(1.0, 10.0, 20, False)
sim = ASTInterfaceTesting.Walk1DSim(sim_params, SIGMA)
ast_params = AdaptiveStressTesting.ASTParams(MAXTIME, RNG_LENGTH, SEED, None)
ast = AdaptiveStressTesting.AdaptiveStressTest(ast_params, sim, ASTInterfaceTesting.initialize, ASTInterfaceTesting.update, ASTInterfaceTesting.isterminal)
AdaptiveStressTesting.sample(ast)

init_fun=Base.function(init_sim)

mcts_params_d = MAXTIME
mcts_params_ec = Base.Float64(100)
mcts_params_n = 100
mcts_params_k = 0.5
mcts_params_alpha = 0.85
mcts_params_clear_nodes = True
mcts_params_maxtime_s = Base.floatmax(Base.Float64)
mcts_params_rng_seed = Base.UInt64(SEED)
mcts_params_top_k = Base.UInt64(10)
#mcts_params = AdaptiveStressTesting.DPWParams(mcts_params_d, mcts_params_ec, mcts_params_n, mcts_params_k, mcts_params_alpha, mcts_params_clear_nodes, mcts_params_maxtime_s, mcts_params_rng_seed, mcts_params_top_k)
#result = AdaptiveStressTesting.stress_test(ast, mcts_params)
print("run w/o error!")

