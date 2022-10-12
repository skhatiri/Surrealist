from decouple import config
import random
from aerialist.px4.trajectory import Trajectory
from .obstacle_solution import ObstacleMutationParams, ObstacleSolution
from .search import Search


class ObstacleSearch(Search):
    DELTA = config("SEARCH_OBST_DELTA", default=1, cast=float)
    DELTA_R = config("SEARCH_OBST_DELTA_R", default=20, cast=float)
    MIN_DELTA = config("SEARCH_OBST_MIN_DELTA", default=0.05, cast=float)
    MIN_DELTA_R = config("SEARCH_OBST_MIN_DELTA_R", default=1, cast=float)
    MAX_STALL = config("SEARCH_OBST_MAX_STALL", default=4, cast=int)
    MAX_SAME = config("SEARCH_OBST_MAX_SAME", default=5, cast=int)
    MUTATIONS_LIST = config("SEARCH_OBST_MUTATIONS", default="r,x,y,sx,sy,sz")
    MUTATIONS = [op.strip() for op in MUTATIONS_LIST.split(",")]
    MIN_ROUNDS = config("SEARCH_OBST_MIN_ROUNDS", default=4, cast=int)

    def __init__(
        self,
        seed: ObstacleSolution,
        goal: Trajectory,
        eval_runs: int = 1,
        path=Search.WEBDAV_DIR,
        id=Search.SEARCH_FLD_NAME,
    ) -> None:
        super().__init__(
            seed,
            goal,
            eval_runs,
            ObstacleMutationParams,
            path,
            id,
        )
        # Trajectory.DISTANCE_METHOD = "frechet"

    def search_mutation(self, budget: int = 100):
        improved = True
        delta_factor = 1
        rounds = self.MIN_ROUNDS
        while improved:
            improved = False
            opr_budget = budget // (len(self.MUTATIONS) * max(1, rounds))
            for mut_opr in self.MUTATIONS:
                if mut_opr == "r":
                    delta = self.DELTA_R * delta_factor
                    min_delta = self.MIN_DELTA_R
                else:
                    delta = self.DELTA * delta_factor
                    min_delta = self.MIN_DELTA
                mutation_init = lambda delta: ObstacleMutationParams(mut_opr, delta)
                sol, evals = self.greedy_search(
                    mutation_init,
                    self.best,
                    opr_budget,
                    delta,
                    0,
                    self.MAX_STALL,
                    self.MAX_SAME,
                    min_delta,
                )
                budget -= evals
                if sol is not None:
                    self.best = sol
                    improved = True

            rounds -= 1
            delta_factor /= 2

    def get_mutation_random(self):
        next = ObstacleMutationParams()
        rand = random.randint(0, 3)
        delta = random.uniform(-5, 5)
        scale = random.uniform(0.75, 1.25)
        if rand == 0:
            next.delta_x = delta
        elif rand == 1:
            next.delta_y = delta
        elif rand == 2:
            next.scale_l = scale
        elif rand == 3:
            next.scale_w = scale
        elif rand == 4:
            next.scale_h = scale

        return next

    def get_mutation_around(cls, last_mutation: ObstacleMutationParams):
        pass

    def get_mutation_invert(cls, last_mutation: ObstacleMutationParams):
        next = ObstacleMutationParams()
        next.delta_x = -last_mutation.delta_x
        next.delta_y = -last_mutation.delta_y
        next.scale_l = 2 - last_mutation.scale_l
        next.scale_w = 2 - last_mutation.scale_w
        next.scale_h = 2 - last_mutation.scale_h
        next.inverted = True
        return next
