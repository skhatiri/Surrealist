import logging
from decouple import config
from aerialist.px4.drone_test import DroneTest

from .obstacle3_search import Obstacle3Search
from .obstacle3_solution import Obstacle3Solution
from .obstacle2_search import Obstacle2Search
from .obstacle2_solution import Obstacle2Solution
from .obstacle_search import ObstacleSearch
from .obstacle_solution import ObstacleSolution
from .search import Search
from .solution import Solution

logger = logging.getLogger(__name__)


class SearchFactory(object):
    MUTATIONS_LIST = config("SEARCH_OBST_MUTATIONS", default="x,y")

    def __init__(
        self,
        seed_test: DroneTest,
        search_method: str,
        budget: int = 50,
        simulations_count: int = 1,
        seeds_count: int = 1,
        path: str = Search.WEBDAV_DIR,
        id: str = Search.SEARCH_FLD_NAME,
    ) -> None:
        if search_method == "obstacle":
            self.seed_type = ObstacleSolution
            self.search_type = ObstacleSearch
        elif search_method == "obstacle2":
            self.seed_type = Obstacle2Solution
            self.search_type = Obstacle2Search
        elif search_method == "obstacle3":
            self.seed_type = Obstacle3Solution
            self.search_type = Obstacle3Search

        if seed_test is not None:
            self.seed = self.seed_type(seed_test)
            if seeds_count == 1:
                self.seed_solutions = [self.seed]
            elif seeds_count > 1:
                logger.info(f"generating {seeds_count} seeds...")
                self.seed_solutions = self.seed.generate_seeds(seeds_count)
        else:
            self.seed = None
            self.seed_solutions = []

        self.seeds_count = seeds_count
        self.simulations_count = simulations_count
        self.budget = budget
        self.path = path
        self.id = id

    def search(self):
        logger.info(f"searching for {len(self.seed_solutions)} seeds...")
        for i in range(len(self.seed_solutions)):
            searcher = self.search_type(
                self.seed_solutions[i], self.simulations_count, self.path, self.id
            )
            searcher.search(self.budget)

    def evaluate(self, test_suite_path: str):
        logger.info(f"loading test suite at {test_suite_path} ...")
        solutions = self.seed_type.load_folder(test_suite_path)
        if solutions is None or len(solutions) == 0:
            logger.error("no tests found to evaluate")
            return
        logger.info(f"evaluating {len(solutions)} tests ...")
        searcher = self.search_type(
            solutions[0], self.simulations_count, self.path, self.id
        )
        searcher.evaluate(solutions)
