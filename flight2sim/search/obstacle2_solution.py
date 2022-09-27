from __future__ import annotations
import logging
from typing import List
import copy
from aerialist.px4.drone_test import DroneTest, DroneTestResult
from aerialist.px4.obstacle import Obstacle
from aerialist.px4.trajectory import Trajectory
from .solution import Solution, MutationParams

logger = logging.getLogger(__name__)


class Obstacle2Solution(Solution):
    def __init__(self, test: DroneTest) -> None:
        super().__init__(test)
        self.fix_obstacle = test.simulation.obstacles[0]
        self.obstacle = test.simulation.obstacles[1]
        # if self.fix_obstacle.to_box().equals(self.obstacle.to_box()):
        #     super().__init__(None, mission_file, [fix_obstacle])
        # else:
        #     super().__init__(None, mission_file, [fix_obstacle, obstacle])

    def get_fitness(self, trajectory: Trajectory, goal: Trajectory):
        sum_dist = trajectory.distance_to_obstacles(self.obstacles)
        return -(sum_dist + 2 * self.get_min_distance(trajectory))

    def process_simulations(self, results: List[DroneTestResult], goal: Trajectory):
        logger.info(f"{len(results)} evalations completed")
        self.trajectories: List[Trajectory] = []
        self.fitnesses: List[float] = []
        self.min_distances: List[float] = []

        self.experiment = results[0]
        self.trajectory = self.experiment.record
        self.fitness = self.get_fitness(self.trajectory, goal)
        self.min_distance = self.get_min_distance(self.trajectory)
        for r in results:
            self.trajectories.append(r.record)
            fitness = self.get_fitness(r.record, goal)
            self.fitnesses.append(fitness)
            self.min_distances.append(self.get_min_distance(r.record))
            if fitness > self.fitness:
                self.trajectory = r.record
                self.fitness = fitness
                self.experiment = r
                self.min_distance = self.get_min_distance(r.record)

    def get_min_distance(self, trajectory: Trajectory):
        return min(
            trajectory.distance_to_obstacles([self.obstacle]),
            trajectory.distance_to_obstacles([self.fix_obstacle]),
        )

    def mutate(self, param: Obstacle2MutationParams) -> Obstacle2Solution:
        mutant = self
        mutant = mutant.move_border(param.border, param.delta)
        return mutant

    def move_border(self, border, delta):
        mutant_test = copy.deepcopy(self.test)
        if border == "x1":
            mutant_test.simulation.obstacles[1].p1.x += delta
        if border == "y1":
            mutant_test.simulation.obstacles[1].p1.y += delta
        if border == "x2":
            mutant_test.simulation.obstacles[1].p2.x += delta
        if border == "y2":
            mutant_test.simulation.obstacles[1].p2.y += delta
        if border == "x":
            mutant_test.simulation.obstacles[1].p1.x += delta
            mutant_test.simulation.obstacles[1].p2.x += delta
        if border == "y":
            mutant_test.simulation.obstacles[1].p1.y += delta
            mutant_test.simulation.obstacles[1].p2.y += delta

        if mutant_test.simulation.obstacles[1].intersects(self.fix_obstacle):
            # mutation is invalid (intersects with other obstacle)
            mutant = copy.deepcopy(self)
            mutant.obstacle = mutant_test.simulation.obstacles[1]
            mutant.fitness = -9999
        else:
            mutant = type(self)(mutant_test)

        return mutant


class Obstacle2MutationParams(MutationParams):
    def __init__(
        self,
        border=None,
        delta=0,
    ) -> None:
        super().__init__()
        self.border = border
        self.delta = delta

    def log_str(self, sol: Obstacle2Solution):
        return f'{round(sol.min_distance,3)},{self.border},{self.delta},{sol.obstacle.p1.x},{sol.obstacle.p1.y},{sol.obstacle.p2.x},{sol.obstacle.p2.y},"{str([round(fit,1) for fit in sol.min_distances])}",'

    @classmethod
    def log_header(cls):
        return "min dist.,border, delta, x1, y1, x2, y2,[min dist.s],"
