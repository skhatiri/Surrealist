from decouple import config
import random
from aerialist.px4.trajectory import Trajectory
from .obstacle_solution import ObstacleMutationParams, ObstacleSolution
from .search import Search
import math
import random


class ObstacleSearch(Search):
    DELTA = config("SEARCH_OBST_DELTA", default=1, cast=float)
    DELTA_R = config("SEARCH_OBST_DELTA_R", default=20, cast=float)
    MIN_DELTA = config("SEARCH_OBST_MIN_DELTA", default=0.05, cast=float)
    MIN_DELTA_R = config("SEARCH_OBST_MIN_DELTA_R", default=1, cast=float)
    MAX_STALL = config("SEARCH_OBST_MAX_STALL", default=4, cast=int)
    MAX_SAME = config("SEARCH_OBST_MAX_SAME", default=5, cast=int)
    MUTATIONS_LIST = config("SEARCH_OBST_MUTATIONS", default="r,x,y,sx,sy,sz")
    RANDOM_ORDER = config("SEARCH_RANDOM_ORDER", default=False, cast=bool)
    RANDOM_ORDER_1ST = config("SEARCH_RANDOM_ORDER_1ST", default=True, cast=bool)
    MUTATIONS = [op.strip() for op in MUTATIONS_LIST.split(",")]
    MIN_ROUNDS = config("SEARCH_OBST_MIN_ROUNDS", default=4, cast=int)
    MAX_STEPS = config("SEARCH_OBST_MAX_STEPS", default=1000, cast=int)

    def __init__(
        self,
        seed: ObstacleSolution,
        eval_runs: int = 1,
        path=Search.WEBDAV_DIR,
        id=Search.SEARCH_FLD_NAME,
    ) -> None:
        super().__init__(
            seed,
            eval_runs,
            path,
            id,
        )

    def search_mutation(self, budget: int = 100):
        improved = True
        delta_factor = 1
        rounds = self.MIN_ROUNDS
        max_steps = self.MAX_STEPS
        while improved:
            improved = False
            opr_budget = budget // (len(self.MUTATIONS) * max(1, rounds))
            if self.RANDOM_ORDER:
                if rounds != self.MIN_ROUNDS or self.RANDOM_ORDER_1ST:
                    random.shuffle(self.MUTATIONS)
            for mut_opr in self.MUTATIONS:
                if mut_opr == "r":
                    delta = self.DELTA_R * delta_factor
                    min_delta = self.MIN_DELTA_R
                else:
                    delta = self.DELTA * delta_factor
                    min_delta = self.MIN_DELTA
                mutation_init = lambda delta: self.mutation_type(mut_opr, delta)
                sol, evals = self.greedy_search(
                    mutation_init,
                    self.best,
                    opr_budget,
                    delta,
                    0,
                    self.MAX_STALL,
                    self.MAX_SAME,
                    min_delta,
                    max_steps,
                )
                budget -= evals
                if sol is not None:
                    self.best = sol
                    improved = True

            rounds -= 1
            max_steps *= 2
            delta_factor /= math.sqrt(2)
