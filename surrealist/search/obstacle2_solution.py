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
        # TODO: handle obstacles overlaps

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

    def mutate(self, param: Obstacle2MutationParams) -> ObstacleSolution:
        mutant_obstacle = self.modify_obstacle(
            self.obstacle, param.property, param.delta
        )
        if (
            mutant_obstacle.size.l <= 0
            or mutant_obstacle.size.w <= 0
            or mutant_obstacle.size.h <= 0
            or mutant_obstacle.intersects(self.test.simulation.obstacles[1])
        ):
            # mutation is invalid (size has negative elements or overlaps with other obstacles)
            mutant = copy.deepcopy(self)
            mutant.obstacle = mutant_obstacle
            mutant.fitness = self.INVALID_SOL_FITNESS
        else:
            mutant_test = copy.deepcopy(self.test)
            mutant_test.simulation.obstacles[0] = Obstacle(
                mutant_obstacle.size, mutant_obstacle.position
            )
            mutant = type(self)(mutant_test)

        return mutant


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
