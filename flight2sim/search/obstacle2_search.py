from decouple import config
from aerialist.px4.trajectory import Trajectory
from .obstacle2_solution import (
    Obstacle2MutationParams,
    Obstacle2Solution,
)
from .search import Search


class Obstacle2Search(Search):
    DELTA = config("SEARCH_OBST_DELTA", default=18, cast=float)
    MIN_DELTA = config("SEARCH_OBST_MIN_DELTA", default=0.05, cast=float)
    MAX_STALL = config("SEARCH_OBST_MAX_STALL", default=4, cast=int)
    MAX_SAME = config("SEARCH_OBST_MAX_SAME", default=5, cast=int)

    def __init__(
        self, seed: Obstacle2Solution, goal: Trajectory, eval_runs: int = 1
    ) -> None:
        super().__init__(seed, goal, eval_runs, Obstacle2MutationParams)

    def search_mutation(self, budget: int = 5):

        improved = True
        if self.seed.obstacle.to_box().equals(self.seed.fix_obstacle.to_box()):
            self.best.fitness = -9999
        border_budget = budget // 4
        delta = self.DELTA
        while improved:
            improved = False
            for border in [
                "x",
                "y",
            ]:  # "x1", "y1", "x2", "y2"]:

                mutation_init = lambda delta: Obstacle2MutationParams(border, delta)
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

            border_budget = budget // 2
            delta /= 2
