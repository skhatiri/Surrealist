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
        # if self.fix_obstacle.to_box().equals(self.obstacle.to_box()):
        #     super().__init__(None, mission_file, [fix_obstacle])
        # else:
        #     super().__init__(None, mission_file, [fix_obstacle, obstacle])

    # def get_fitness(self, trajectory: Trajectory, goal: Trajectory):
    #     sum_dist = trajectory.distance_to_obstacles(self.test.simulation.obstacles)
    #     return sum_dist
    #     # return -(sum_dist + 2 * self.get_min_distance(trajectory))

    def process_simulations(
        self,
        results: List[DroneTestResult],
        goal: Trajectory,
    ):
        logger.info(f"{len(results)} evalations completed")
        self.trajectories = [r.record for r in results]
        self.average_trajectory = Trajectory.average(self.trajectories)
        self.dtws_to_ave = [
            self.average_trajectory.distance(r) for r in self.trajectories
        ]
        self.fitnesses = self.dtws_to_ave
        self.ave_dtw = mean(self.dtws_to_ave)
        dtw_term = self.ave_dtw - self.DETERMINISTIC_MAX_DTW
        if dtw_term < 0:
            dtw_term = 0

        self.obstacle_distance = self.average_trajectory.distance_to_obstacles(
            self.test.simulation.obstacles
        )
        obstacle_term = self.obstacle_distance

        self.trajectory_change = self
        self.fitness = dtw_term - obstacle_term
        self.result = self.average_trajectory

        self.min_distances = [
            r.distance_to_obstacles(self.test.simulation.obstacles)
            for r in self.trajectories
        ]
        max_ind = self.fitnesses.index(max(self.fitnesses))
        self.experiment = results[max_ind]
        self.min_distance = obstacle_term


class Obstacle3MutationParams(Obstacle2MutationParams):
    def __init__(
        self,
        border=None,
        delta=0,
    ) -> None:
        super().__init__(border, delta)

    def log_str(self, sol: Obstacle3Solution):
        return f'{round(sol.ave_dtw,3)},{round(sol.obstacle_distance,3)},{self.border},{self.delta},{sol.obstacle.position.x},{sol.obstacle.position.y},{sol.obstacle.size.x},{sol.obstacle.size.y},{sol.obstacle.size.z},{sol.obstacle.angle},"{str([round(fit,1) for fit in sol.min_distances])}"'

    @classmethod
    def log_header(cls):
        return "ave dtw,obst. dist.,border, delta, x, y, l, w, h, r,[min dist.s],"
