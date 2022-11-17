from decouple import config
from .obstacle_search import ObstacleSearch
from .obstacle2_solution import Obstacle2Solution
from .search import Search


class Obstacle2Search(ObstacleSearch):
    MUTATIONS_LIST = config("SEARCH_OBST_MUTATIONS", default="r,x,y")

    def __init__(
        self,
        seed: Obstacle2Solution,
        eval_runs: int = 1,
        path=Search.WEBDAV_DIR,
        id=Search.SEARCH_FLD_NAME,
    ) -> None:
        super().__init__(
            seed,
            None,
            eval_runs,
            path,
            id,
        )

    # def search_mutation(self, budget: int = 5):

    #     # if self.seed.obstacle.to_box().equals(self.seed.fix_obstacle.to_box()):
    #     #     self.best.fitness = Solution.INVALID_SOL_FITNESS
    #     return super().search_mutation(budget)
