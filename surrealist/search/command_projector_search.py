import random
import logging
from decouple import config
from aerialist.px4.trajectory import Trajectory
from .command_solution import CommandSolution, CommandProjectionParams
from .search import Search

logger = logging.getLogger(__name__)


class CommandProjectorSearch(Search):
    ALPHA = config("SEARCH_PROJ_ALPHA", default=0.01, cast=float)
    MAX_STALL = config("SEARCH_PROJ_MAX_STALL", default=4, cast=int)
    MAX_SAME = config("SEARCH_PROJ_MAX_SAME", default=5, cast=int)

    def __init__(
        self, seed: CommandSolution, goal: Trajectory, eval_runs: int = 1
    ) -> None:
        super().__init__(seed, goal, eval_runs, CommandProjectionParams)

    def search_mutation(self, budget: int = 5):
        improved = True
        alpha = self.ALPHA
        while improved and budget > 0:
            improved = False
            attr_budget = budget // 4
            for i in [3, 0, 1, 2]:
                mutation_init = lambda p: CommandProjectionParams.dimension_projector(
                    i, p
                )
                sol, evals = self.greedy_search(
                    mutation_init,
                    self.best,
                    attr_budget,
                    alpha,
                    1,
                    self.MAX_STALL,
                    self.MAX_SAME,
                )
                budget -= evals
                if sol is not None:
                    self.best = sol
                    improved = True

    def get_mutation_random(self):
        next = [1] * 4
        projector_ind = random.randint(0, 3)
        next[projector_ind] = random.uniform(1 - self.ALPHA, 1 + self.ALPHA)
        return CommandProjectionParams(projector=tuple(next))

    def get_mutation_around(self, last_mutation: CommandProjectionParams):
        next = [1] * 4
        for i in range(4):
            next[i] = 0.5 + (
                last_mutation.projector[i] / 2
            )  # = 1 - ((1 - prev.projector[i]) / 2)
        return CommandProjectionParams(projector=tuple(next))

    def get_mutation_invert(self, last_mutation: CommandProjectionParams):
        next = [1] * 4
        for i in range(4):
            next[i] = 1.5 - (
                last_mutation.projector[i] / 2
            )  # = 1 + ((1 - prev.projector[i]) / 2)
        return CommandProjectionParams(projector=tuple(next))
