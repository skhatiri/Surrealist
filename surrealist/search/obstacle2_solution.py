from __future__ import annotations
import logging
from typing import List
import random
import copy
from shapely.geometry import Point
from decouple import config

from aerialist.px4.drone_test import DroneTest, DroneTestResult
from aerialist.px4.obstacle import Obstacle
from aerialist.px4.trajectory import Trajectory

from .obstacle_solution import ObstacleMutationParams, ObstacleSolution

logger = logging.getLogger(__name__)


class Obstacle2Solution(ObstacleSolution):
    MIN_OBSTACLE_GAP = config(
        "SERACH_MIN_OBSTACLE_GAP", default=0.0, cast=float
    )  # meters (disabled by default; 0.75 suggested if enabled)
    MIN_OBSTACLE_THICKNESS = config(
        "SEARCH_MIN_OBSTACLE_THICKNESS", default=0.0, cast=float
    )  # meters (disabled by default; 0.05 suggested if enabled)
    MIN_OBSTACLE_HEIGHT = config(
        "SEARCH_MIN_OBSTACLE_HEIGHT", default=0.0, cast=float
    )  # meters (disabled by default; 5 suggested if enabled)
    MIN_WAYPOINT_GAP = config(
        "SEARCH_MIN_WAYPOINT_GAP", default=0.0, cast=float
    )  # meters (disabled by default; 0.5 suggested if enabled)
    OBSTACLES_CAN_INTERSECT = config(
        "SEARCH_OBSTACLES_CAN_INTERSECT", default=False, cast=bool
    )  # whether obstacles can intersect (disabled by default)

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
        self.gap = self.get_gap()
        return self.aggregate

    def get_min_distance(self, trajectory: Trajectory):
        return min(
            [
                trajectory.distance_to_obstacles([obs])
                for obs in self.test.simulation.obstacles
            ]
        )

    def check_validity(self):
        if not super().check_validity():
            return False

        obst = self.test.simulation.obstacles[0]
        # minimum size of the mutated obstacle
        if obst.shape == obst.BOX:
            if (
                obst.size.l < self.MIN_OBSTACLE_THICKNESS
                or obst.size.w < self.MIN_OBSTACLE_THICKNESS
                or obst.size.h < self.MIN_OBSTACLE_HEIGHT
            ):
                logger.warning(
                    f"invalid solution: obstacle too small ({obst.to_dict()})"
                )
                return False
        if obst.shape == obst.CYLINDER:
            if (
                obst.size.r < (self.MIN_OBSTACLE_THICKNESS / 2)
                or obst.size.h < self.MIN_OBSTACLE_HEIGHT
            ):
                logger.warning(
                    f"invalid solution: obstacle too small ({obst.to_dict()})"
                )
                return False

        # no obstacles interest
        if not self.OBSTACLES_CAN_INTERSECT:
            for i in range(len(self.test.simulation.obstacles) - 1):
                for j in range(i + 1, len(self.test.simulation.obstacles)):
                    if self.test.simulation.obstacles[i].intersects(
                        self.test.simulation.obstacles[j]
                    ):
                        logger.warning(
                            f"invalid solution: obstacles intersect ({obst.to_dict()})"
                        )
                        return False

        # minimum gap between obstacles
        if self.get_gap() < self.MIN_OBSTACLE_GAP:
            logger.warning(
                f"invalid solution: obstacles gap too small ({obst.to_dict()})"
            )
            return False

        # minimum obstacle distance to waypoints (if present)
        if self.test.mission is not None and self.test.mission.waypoints is not None:
            for wp in self.test.mission.waypoints:
                point = Point(wp.x, wp.y)
                # for ob in self.test.simulation.obstacles:
                wp_distance = obst.distance(point)
                if wp_distance < self.MIN_WAYPOINT_GAP:
                    logger.warning(
                        f"invalid solution: obstacle too close to waypoint ({obst.to_dict()})"
                    )
                    return False

        return True

    def get_gap(self):
        gaps = []
        for i in range(1, len(self.test.simulation.obstacles)):
            gaps.append(
                Obstacle.minimum_gap(
                    [
                        self.test.simulation.obstacles[0],
                        self.test.simulation.obstacles[i],
                    ]
                )
            )
        return min(gaps)

    def generate_seeds(self, n: int):
        if n == 1:
            return [self]
        seeds = [self]
        size_range = (-2, 2)
        position_range = (-5, 5)
        rotation_range = (-90, 90)
        while len(seeds) < n:
            new_obstacles = []
            for obs in self.test.simulation.obstacles:
                shape = obs.shape
                size = Obstacle.Size(
                    l=obs.size.l * 2 ** random.uniform(*size_range),
                    w=obs.size.w * 2 ** random.uniform(*size_range),
                    h=obs.size.h,
                    r=obs.size.r * 2 ** random.uniform(*size_range),
                )
                position = Obstacle.Position(
                    x=obs.position.x + random.uniform(*position_range),
                    y=obs.position.y + random.uniform(*position_range),
                    z=obs.position.z,
                    r=obs.position.r + random.uniform(*rotation_range),
                )
                new_obstacles.append(Obstacle(size, position, shape))
            new_test = copy.deepcopy(self.test)
            new_test.simulation.obstacles = new_obstacles
            new_seed = type(self)(new_test)
            if new_seed.check_validity():
                logger.info(f"new valid seed:{new_test.to_dict()}")
                seeds.append(new_seed)
            else:
                logger.info(f"ignoring invalid seed:{new_test.to_dict()}")

        return seeds


class Obstacle2MutationParams(ObstacleMutationParams):
    def __init__(
        self,
        border=None,
        delta=0,
    ) -> None:
        super().__init__(border, delta)

    def log_str(self, sol: Obstacle2Solution):
        return f'{round(sol.min_distance,3)},{self.property},{self.delta},{sol.obstacle.position.x},{sol.obstacle.position.y},{sol.obstacle.size.l},{sol.obstacle.size.w},{sol.obstacle.size.r},{sol.obstacle.size.h},{sol.obstacle.position.r},"{str([round(fit,1) for fit in sol.min_distances])}"'
        # return f'{round(sol.min_distance,3)},{sol.aggregate.status.value},{round(sol.gap,3)},{self.property},{self.delta},{sol.obstacle.position.x},{sol.obstacle.position.y},{sol.obstacle.size.l},{sol.obstacle.size.w},{sol.obstacle.size.r},{sol.obstacle.size.h},{sol.obstacle.position.r},"{str([round(fit,1) for fit in sol.min_distances])}"'

    @classmethod
    def log_header(cls):
        return "min dist.,border, delta, x, y, l, w, rd, h, r,[min dist.s],"
        # return "min dist.,status,gap,mutation,delta,x,y,l,w,rd,h,r,[min dist.s],"

    # def report_str(self, sol: Obstacle2Solution):
    #     direct_path = LineString([(wp.x, wp.y) for wp in sol.test.mission.waypoints])
    #     traveled_path = sol.result.to_line()
    #     deviation = max(direct_path.distance(Point(c)) for c in traveled_path.coords)
    #     return f"{sol.aggregate.status.value},{round(sol.min_distance,3)},{round(sol.gap,3)},{round(deviation,3)},{round(sol.result.positions[-1].timestamp - sol.result.positions[0].timestamp,1)},{round(length(traveled_path),3)},{round(length(direct_path),3)},{self.property},{round(self.delta,3)}"

    # @classmethod
    # def report_header(cls):
    #     return "status,distance,gap,deviation,duration,traveled,direct,mutation,delta"
