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
from aerialist.px4 import file_helper
from aerialist.entry import execute_test

logger = logging.getLogger(__name__)


class Solution(object):
    DIR = config("RESULTS_DIR", default="results/")
    WEBDAV_DIR = config("WEBDAV_UP_FLD", default=None)
    CHANGE_THRESHOLD = config("SEARCH_CHANGE_THRESHOLD", cast=float, default=0.01)

    def __init__(self, test: DroneTest) -> None:
        super().__init__()
        self.test = test
        self.result = None

    def evaluate(
        self,
        goal: Trajectory | object,
        runs: int,
        iteration: int,
    ) -> None:
        if hasattr(self, "fitness"):  # solution has been simulated before
            return

        if self.result is not None:  # solution has been simulated before
            self.fitness = self.get_fitness(self.result, goal)
            return

        agent = AgentConfig(
            engine=AgentConfig.K8S,
            count=runs,
            path=self.WEBDAV_DIR,
            id=f"iter{iteration:03d}",
        )
        K8sAgent.WEBDAV_LOCAL_DIR = self.DIR
        results = execute_test(
            DroneTest(
                drone=self.test.drone,
                simulation=self.test.simulation,
                test=self.test.test,
                assertion=self.test.assertion,
                agent=agent,
            )
        )

        self.process_simulations(results, goal)

    def process_simulations(
        self,
        results: List[DroneTestResult],
        goal: Trajectory,
    ):
        logger.info(f"{len(results)} evalations completed")
        self.trajectories: List[Trajectory] = []
        self.fitnesses: List[float] = []
        for r in results:
            self.trajectories.append(r.record)
            self.fitnesses.append(self.get_fitness(r.record, goal))

        median_ind = self.fitnesses.index(
            percentile(self.fitnesses, 50, interpolation="nearest")
        )
        self.experiment = results[median_ind]
        self.result = Trajectory.average(self.trajectories)
        self.fitness = self.get_fitness(self.result, goal)

    def get_fitness(
        self,
        trajectory: Trajectory,
        goal: Trajectory,
    ):
        return -goal.distance(trajectory)

    def compare_to(self, other: Solution):
        """compares the fitness of solutions,
        taking into account the fitness distribution in different simulation runs"""
        distance = abs(self.get_fitness(self.result, other.result))
        # relative_change = (self.fitness - other.fitness) / self.fitness
        # if abs(relative_change) < self.CHANGE_THRESHOLD:
        if distance < self.CHANGE_THRESHOLD:
            return 0
        else:
            if self.fitness > other.fitness:
                return 1
            else:
                return -1

        # sim = similarity_test(self.fitnesses, other.fitnesses)
        # if sim == True:
        #     return 0
        # elif sim == False:
        #     if median(self.fitnesses) > median(other.fitnesses):
        #         return 1
        #     else:
        #         return -1
        # else:
        #     logger.warning("non deciesive similairty")
        #     return 0

    def mutate(self, params: MutationParams) -> Solution:
        raise NotImplementedError("This method must be overridden")

    def plot(self, goal, iteration: int):
        Trajectory.plot_multiple(
            self.trajectories,
            goal,
            distance=-self.fitness,
            obstacles=self.test.simulation.obstacles
            if self.test.simulation is not None
            else None,
            file_prefix=f"iter{iteration:03d}-",
            ave_trajectory=self.result,
        )
        # Command.save_csv(self.commands,f'{self.DIR}{datetime.now().strftime("%m-%d %H-%M-%S")}.csv')


class MutationParams(object):
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def log_header(cls):
        return ""

    def log_str(self, sol: Solution):
        return ""
