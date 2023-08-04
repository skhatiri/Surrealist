from decouple import config
from .obstacle_search import ObstacleSearch
from .obstacle2_solution import Obstacle2Solution
from .search import Search


class Obstacle2Search(ObstacleSearch):
    MUTATIONS_LIST = config("SEARCH_OBST_MUTATIONS", default="x,y")

    def __init__(
        self,
        seed: Obstacle2Solution,
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
