from __future__ import annotations
import logging
from typing import List
import copy
from aerialist.px4.drone_test import DroneTest, DroneTestResult
from aerialist.px4.obstacle import Obstacle
from aerialist.px4.trajectory import Trajectory

from .obstacle_solution import ObstacleMutationParams, ObstacleSolution

logger = logging.getLogger(__name__)


class Obstacle2Solution(ObstacleSolution):
    def __init__(self, test: DroneTest) -> None:
        super().__init__(test)
        self.mutation_type = Obstacle2MutationParams
        self.goal = None

    def get_fitness(self, trajectory: Trajectory):
        sum_dist = trajectory.distance_to_obstacles(self.test.simulation.obstacles)
        return -(sum_dist + 2 * self.get_min_distance(trajectory))

    def aggregate_simulations(self, results: List[DroneTestResult]):
        self.trajectories = [r.record for r in results]
        self.fitnesses = [self.get_fitness(r.record) for r in results]
        max_ind = self.fitnesses.index(max(self.fitnesses))
        self.fitness = self.fitnesses[max_ind]
        self.aggregate = results[max_ind]
        self.result = results[max_ind].record
        self.min_distances = [self.get_min_distance(r.record) for r in results]
        self.min_distance = self.min_distances[max_ind]
        return self.aggregate

    def get_min_distance(self, trajectory: Trajectory):
        return min(
            [
                trajectory.distance_to_obstacles([obs])
                for obs in self.test.simulation.obstacles
            ]
        )

    def check_validity(self):
        for obst in self.test.simulation.obstacles:
            if obst.size.l <= 0 or obst.size.w <= 0 or obst.size.h <= 0:
                return False

        for i in range(len(self.test.simulation.obstacles) - 1):
            for j in range(i + 1, len(self.test.simulation.obstacles)):
                if self.test.simulation.obstacles[i].intersects(
                    self.test.simulation.obstacles[j]
                ):
                    return False

        return True


class Obstacle2MutationParams(ObstacleMutationParams):
    def __init__(
        self,
        border=None,
        delta=0,
    ) -> None:
        super().__init__(border, delta)

    def log_str(self, sol: Obstacle2Solution):
        return f'{round(sol.min_distance,3)},{self.property},{self.delta},{sol.obstacle.position.x},{sol.obstacle.position.y},{sol.obstacle.size.l},{sol.obstacle.size.w},{sol.obstacle.size.h},{sol.obstacle.position.r},"{str([round(fit,1) for fit in sol.min_distances])}"'

    @classmethod
    def log_header(cls):
        return "min dist.,border, delta, x, y, l, w, h, r,[min dist.s],"
