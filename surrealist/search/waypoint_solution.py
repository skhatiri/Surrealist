from __future__ import annotations
import copy
import logging
from shapely.geometry import Point, LineString
from shapely import length

from aerialist.px4.aerialist_test import AerialistTest
from aerialist.px4.obstacle import Obstacle
from aerialist.px4.trajectory import Trajectory


from .obstacle2_solution import Obstacle2Solution, Obstacle2MutationParams

logger = logging.getLogger(__name__)


class WaypointSolution(Obstacle2Solution):

    def __init__(self, test: AerialistTest) -> None:
        super().__init__(test)
        self.mutation_type = WaypointMutationParams
        self.waypoint = test.mission.waypoints[0]

    def get_fitness(self, trajectory: Trajectory):
        # todo: fitness based on time to reach the goal (prioritize spending more time to find a path, but will also prioritize waypoints furthur away)
        # todo: fitness based on distance to the goal (will prioritize waypoints closer to the goal)
        sum_dist = trajectory.distance_to_obstacles(self.test.simulation.obstacles)
        return -(sum_dist + 2 * self.get_min_distance(trajectory))

    def mutate(self, param: WaypointMutationParams) -> WaypointSolution:
        mutant_waypoint = self.modify_waypoint(
            self.waypoint, param.property, param.delta
        )
        mutant_test = copy.deepcopy(self.test)
        mutant_test.mission.waypoints[0] = mutant_waypoint
        mutant = type(self)(mutant_test)

        return mutant

    def modify_waypoint(
        self, waypoint: Obstacle.Position, property: str, delta: float
    ) -> Obstacle.Position:
        mutant_waypoint = copy.deepcopy(waypoint)
        ### change position
        if property == "wp_x":
            mutant_waypoint = Obstacle.Position(
                x=mutant_waypoint.x + delta,
                y=mutant_waypoint.y,
                z=mutant_waypoint.z,
                r=mutant_waypoint.r,
            )
            # mutant_obstacle.position.x += delta
        if property == "wp_y":
            mutant_waypoint = Obstacle.Position(
                x=mutant_waypoint.x,
                y=mutant_waypoint.y + delta,
                z=mutant_waypoint.z,
                r=mutant_waypoint.r,
            )
            # mutant_obstacle.position.y += delta

        ### rotation
        if property == "wp_r":
            mutant_waypoint = Obstacle.Position(
                x=mutant_waypoint.x,
                y=mutant_waypoint.y,
                z=mutant_waypoint.z,
                r=mutant_waypoint.r + delta,
            )
            # mutant_obstacle.position.r += delta
        return mutant_waypoint


class WaypointMutationParams(Obstacle2MutationParams):
    def __init__(
        self,
        border=None,
        delta=0,
    ) -> None:
        super().__init__(border, delta)

    def log_str(self, sol: WaypointSolution):
        return f'{round(sol.min_distance,3)},{sol.aggregate.status.value},{round(sol.gap,3)},{self.property},{self.delta},{sol.waypoint.x},{sol.waypoint.y},{sol.waypoint.r},"{str([round(fit,1) for fit in sol.min_distances])}"'

    @classmethod
    def log_header(cls):
        return "min dist.,status,gap,mutation,delta,wp_x,wp_y,wp_r,[min dist.s],"

    def report_str(self, sol: WaypointSolution):
        direct_path = LineString([(wp.x, wp.y) for wp in sol.test.mission.waypoints])
        traveled_path = sol.result.to_line()
        deviation = max(direct_path.distance(Point(c)) for c in traveled_path.coords)
        return f"{sol.aggregate.status.value},{round(sol.min_distance,3)},{round(sol.gap,3)},{round(deviation,3)},{round(sol.result.positions[-1].timestamp - sol.result.positions[0].timestamp,1)},{round(length(traveled_path),3)},{round(length(direct_path),3)},{self.property},{round(self.delta,3)}"

    @classmethod
    def report_header(cls):
        return "status,distance,gap,deviation,duration,traveled,direct,mutation,delta"
