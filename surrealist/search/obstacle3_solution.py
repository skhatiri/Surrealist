from __future__ import annotations
import logging
from statistics import mean
from typing import List
from aerialist.px4.drone_test import DroneTest, DroneTestResult
from aerialist.px4.trajectory import Trajectory

from .obstacle2_solution import Obstacle2MutationParams, Obstacle2Solution

logger = logging.getLogger(__name__)


class Obstacle3Solution(Obstacle2Solution):
    DETERMINISTIC_MAX_DTW = 65

    def __init__(self, test: DroneTest) -> None:
        super().__init__(test)
        self.mutation_type = Obstacle3MutationParams

    def get_fitness(self, trajectory: Trajectory):
        dtw_term = self.ave_dtw - self.DETERMINISTIC_MAX_DTW
        if dtw_term < 0:
            dtw_term = 0

        obstacle_term = trajectory.distance_to_obstacles(self.test.simulation.obstacles)
        self.obstacle_distance = obstacle_term
        return dtw_term - obstacle_term

    def aggregate_simulations(
        self,
        results: List[DroneTestResult],
    ):
        self.trajectories = [r.record for r in results]
        self.average_trajectory = Trajectory.average(self.trajectories)
        self.dtws_to_ave = [
            self.average_trajectory.distance(r) for r in self.trajectories
        ]
        self.fitnesses = self.dtws_to_ave
        self.ave_dtw = mean(self.dtws_to_ave)

        self.min_distances = [self.get_min_distance(r) for r in self.trajectories]
        self.min_distance = self.get_min_distance(self.average_trajectory)

        self.fitness = self.get_fitness(self.average_trajectory)
        self.result = self.average_trajectory
        self.aggregate = DroneTestResult(
            record=self.average_trajectory,
        )
        return self.aggregate


class Obstacle3MutationParams(Obstacle2MutationParams):
    def __init__(
        self,
        border=None,
        delta=0,
    ) -> None:
        super().__init__(border, delta)

    def log_str(self, sol: Obstacle3Solution):
        return f'{round(sol.ave_dtw,3)},{round(sol.obstacle_distance,3)},{self.property},{self.delta},{sol.obstacle.position.x},{sol.obstacle.position.y},{sol.obstacle.size.l},{sol.obstacle.size.w},{sol.obstacle.size.h},{sol.obstacle.position.r},"{str([round(fit,1) for fit in sol.min_distances])}"'

    @classmethod
    def log_header(cls):
        return "ave dtw,obst. dist.,border, delta, x, y, l, w, h, r,[min dist.s],"
