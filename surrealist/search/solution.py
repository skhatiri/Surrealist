from __future__ import annotations
from typing import List
from decouple import config
from numpy import percentile
import logging
from aerialist.px4.drone_test import (
    DroneTest,
    DroneTestResult,
    AgentConfig,
)
from aerialist.px4.k8s_agent import K8sAgent
from aerialist.px4.trajectory import Trajectory
from aerialist.entry import execute_test

logger = logging.getLogger(__name__)


class Solution(object):
    DIR = config("RESULTS_DIR", default="results/")
    WEBDAV_DIR = config("WEBDAV_UP_FLD", default=None)
    CHANGE_THRESHOLD = config("SEARCH_CHANGE_THRESHOLD", cast=float, default=0.01)
    INVALID_SOL_FITNESS = -9999

    def __init__(self, test: DroneTest) -> None:
        super().__init__()
        self.test = test
        self.result = None
        self.mutation_type = MutationParams

    def evaluate(
        self,
        runs: int,
        iteration: int,
    ) -> None:
        if hasattr(self, "fitness"):  # solution has been simulated before
            return

        if self.result is not None:  # solution has been simulated before
            self.fitness = self.get_fitness(self.result)
            return

        agent = AgentConfig(
            engine=AgentConfig.K8S,
            count=runs,
            path=self.WEBDAV_DIR,
            id=f"iter{iteration:03d}",
        )
        K8sAgent.WEBDAV_LOCAL_DIR = self.DIR
        test_results = execute_test(
            DroneTest(
                drone=self.test.drone,
                simulation=self.test.simulation,
                test=self.test.test,
                assertion=self.test.assertion,
                agent=agent,
            )
        )
        logger.info(f"{len(test_results)} evalations completed")
        self.aggregate_simulations(test_results)

    def aggregate_simulations(
        self,
        results: List[DroneTestResult],
    ):
        self.trajectories = [r.record for r in results]
        self.fitnesses = [self.get_fitness(r.record) for r in results]

        median_ind = self.fitnesses.index(
            percentile(self.fitnesses, 50, interpolation="nearest")
        )
        self.result = Trajectory.average([r.record for r in results])
        self.fitness = self.get_fitness(self.result)
        self.aggregate = DroneTestResult(
            log_file=results[median_ind].log_file, record=self.result
        )
        return self.aggregate

    def get_fitness(self, trajectory: Trajectory):
        raise NotImplementedError()

    def compare_to(self, other: Solution):
        """compares the fitness of solutions,
        taking into account the fitness distribution in different simulation runs"""
        if self.is_almost_identical(other):
            return 0
        else:
            if self.fitness > other.fitness:
                return 1
            else:
                return -1

    def is_almost_identical(self, other: Solution):
        distance = abs(self.result.distance(other.result))
        return distance < self.CHANGE_THRESHOLD

    def mutate(self, params: MutationParams) -> Solution:
        raise NotImplementedError("This method must be overridden")

    def plot(self, iteration: int):
        Trajectory.plot_multiple(
            self.trajectories,
            self.goal if hasattr(self, "goal") else None,
            distance=-self.fitness,
            obstacles=self.test.simulation.obstacles
            if self.test.simulation is not None
            else None,
            file_prefix=f"iter{iteration:03d}-",
            ave_trajectory=self.result,
        )


class MutationParams(object):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def log_header(cls):
        return ""

    def log_str(self, sol: Solution):
        return ""
