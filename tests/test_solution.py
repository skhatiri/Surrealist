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
from aerialist.px4.plot import Plot
from surrealist.search.solution import Solution
from surrealist.search.obstacle_solution import ObstacleSolution
from surrealist.search.obstacle2_solution import Obstacle2Solution


class TestSolution(unittest.TestCase):
    def setUp(self) -> None:
        os.makedirs("logs/", exist_ok=True)
        logging.basicConfig(
            level=logging.DEBUG,
            filename="logs/root.txt",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return super().setUp()

    def test_solution(self):
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
        Solution.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/tests/"
        Plot.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/tests/"
        sol = Solution(seed)
        iter = 200
        sol.evaluate(
            runs=3,
            iteration=iter,
        )
        logger.info(sol.fitness)
        sol.plot(iter)
        return sol.fitness

    def test_obstacle_solution(self):
        simulation_config = SimulationConfig(
            headless=True,
            simulator=SimulationConfig.ROS,
            obstacles=[10, 10, 0, 15, 20, 20],
        )
        drone_config = DroneConfig(
            port=DroneConfig.ROS_PORT,
            params_file="experiments/params_avoidance.csv",
            mission_file="experiments/auto1.plan",
        )
        test_config = TestConfig(
            commands_file="experiments/auto_commands.csv",
        )
        assertion_config = AssertionConfig(
            log_file="experiments/auto1.ulg",
            variable=AssertionConfig.TRAJECTORY,
        )
        seed = DroneTest(drone_config, simulation_config, test_config, assertion_config)
        Solution.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/tests/"
        Plot.WEBDAV_DIR = "https://filer.cloudlab.zhaw.ch/remote.php/webdav/tests/"
        sol = ObstacleSolution(seed)
        iter = 271
        sol.evaluate(
            runs=3,
            iteration=iter,
        )
        logger.info(sol.fitness)
        sol.plot(iter)
        return sol.fitness
