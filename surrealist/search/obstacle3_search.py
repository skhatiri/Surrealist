from decouple import config
from .obstacle2_search import Obstacle2Search
from .obstacle3_solution import Obstacle3Solution
from .search import Search


class Obstacle3Search(Obstacle2Search):
    MUTATIONS_LIST = config("SEARCH_OBST_MUTATIONS", default="x,y")

    def __init__(
        self,
        seed: Obstacle3Solution,
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
