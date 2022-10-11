from decouple import config
import random
from aerialist.px4.trajectory import Trajectory
from .obstacle_solution import ObstacleMutationParams, ObstacleSolution
from .search import Search


class ObstacleSearch(Search):
    DELTA = config("SEARCH_OBST_DELTA", default=1, cast=float)
    MIN_DELTA = config("SEARCH_OBST_MIN_DELTA", default=0.05, cast=float)
    MAX_STALL = config("SEARCH_OBST_MAX_STALL", default=4, cast=int)
    MAX_SAME = config("SEARCH_OBST_MAX_SAME", default=5, cast=int)

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

    def search_mutation(self, budget: int = 5):
        improved = True
        delta = self.DELTA
        border_budget = budget // 7
        while improved:
            improved = False
            for border in [
                "y",
                "x",
                "z1",
                "x1",
                "y1",
                "x2",
                "y2",
            ]:
                mutation_init = lambda delta: ObstacleMutationParams(border, delta)
                sol, evals = self.greedy_search(
                    mutation_init,
                    self.best,
                    border_budget,
                    delta,
                    0,
                    self.MAX_STALL,
                    self.MAX_SAME,
                    self.MIN_DELTA,
                )
                budget -= evals
                if sol is not None:
                    self.best = sol
                    improved = True

            border_budget = budget // 6
            delta /= 2

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
