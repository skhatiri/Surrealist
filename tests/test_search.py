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
from flight2sim.search.obstacle_search import ObstacleSearch
from flight2sim.search.obstacle_solution import ObstacleMutationParams, ObstacleSolution
from flight2sim.search.search import Search
from flight2sim.search.solution import MutationParams, Solution


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
            commands_file="flight2sim/resources/logs/t0.ulg",
        )
        seed = DroneTest(
            drone_config,
            simulation_config,
            test_config,
        )
        seed_sol = Solution(seed)

        goal = AssertionConfig(
            log_file="flight2sim/resources/logs/t0.ulg",
            variable=AssertionConfig.TRAJECTORY,
        ).expectation

        Search.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/tests/"
        searcher = Search(seed_sol, goal, 3, MutationParams)
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
            obstacles=[10, 10, 0, 15, 20, 20],
        )
        drone_config = DroneConfig(
            port=DroneConfig.ROS_PORT,
            params_file="flight2sim/resources/logs/params_avoidance.csv",
            mission_file="flight2sim/resources/logs/auto1.plan",
        )
        test_config = TestConfig(
            commands_file="flight2sim/resources/logs/auto_commands.csv",
        )
        seed = DroneTest(
            drone_config,
            simulation_config,
            test_config,
        )
        goal = AssertionConfig(
            log_file="flight2sim/resources/logs/auto1.ulg",
            variable=AssertionConfig.TRAJECTORY,
        ).expectation
        Search.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/tests/"

        seed_sol = ObstacleSolution(seed)
        searcher = ObstacleSearch(seed_sol, goal, 3)
        searcher.search(10)
        logger.info(searcher.best.fitness)
        return searcher.best.fitness
