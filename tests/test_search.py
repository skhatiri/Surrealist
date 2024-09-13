from asyncio.log import logger
import unittest
import os
import logging
from aerialist.px4.drone_test import (
    AssertionConfig,
    DroneConfig,
    DroneTest,
    SimulationConfig,
    TestConfig,
)
from surrealist.search.obstacle_search import ObstacleSearch
from surrealist.search.obstacle_solution import ObstacleMutationParams, ObstacleSolution
from surrealist.search.search import Search
from surrealist.search.solution import MutationParams, Solution


class TestSearch(unittest.TestCase):
    def setUp(self) -> None:
        os.makedirs("logs/", exist_ok=True)
        logging.basicConfig(
            level=logging.DEBUG,
            filename="logs/root.txt",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return super().setUp()

    def test_search(self):
        simulation_config = SimulationConfig(
            headless=True,
            simulator=SimulationConfig.GAZEBO,
        )
        drone_config = DroneConfig(
            port=DroneConfig.SITL_PORT,
            params={},
            mission_file=None,
        )
        test_config = TestConfig(
            commands_file="experiments/t0.ulg",
        )
        assertion_config = AssertionConfig(
            log_file="experiments/t0.ulg",
            variable=AssertionConfig.TRAJECTORY,
        )
        seed = DroneTest(drone_config, simulation_config, test_config, assertion_config)
        seed_sol = Solution(seed)

        Search.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/tests/"
        searcher = Search(seed_sol, 3, MutationParams)
        try:
            searcher.search(1)
        except:
            pass
        logger.info(searcher.best.fitness)
        return searcher.best.fitness

    def test_obstacle_search(self):
        simulation_config = SimulationConfig(
            headless=True,
            simulator=SimulationConfig.ROS,
            obstacles=[3, 3, 10, -7, 2, 0, 30],
        )
        drone_config = DroneConfig(
            port=DroneConfig.ROS_PORT,
            params_file="experiments/rq2-0-params.csv",
            mission_file="experiments/rq2-0.plan",
        )
        test_config = TestConfig(
            commands_file="experiments/auto_commands.csv",
        )
        assertion = AssertionConfig(
            log_file="experiments/rq2-0.ulg",
            variable=AssertionConfig.TRAJECTORY,
        )

        seed = DroneTest(
            drone_config,
            simulation_config,
            test_config,
            assertion,
        )
        goal = assertion.expectation
        Search.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/ICST/"

        seed_sol = ObstacleSolution(seed)
        searcher = ObstacleSearch(seed_sol, goal, 3)
        searcher.search(100)
        logger.info(searcher.best.fitness)
        return searcher.best.fitness
