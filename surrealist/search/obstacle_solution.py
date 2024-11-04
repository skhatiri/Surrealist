from __future__ import annotations
import copy
from aerialist.px4.drone_test import DroneTest
from aerialist.px4.obstacle import Obstacle
from aerialist.px4.trajectory import Trajectory
from .solution import Solution, MutationParams


class ObstacleSolution(Solution):
    def __init__(self, test: DroneTest) -> None:
        super().__init__(test)
        self.mutation_type = ObstacleMutationParams
        self.obstacle = test.simulation.obstacles[0]
        try:
            self.goal = test.assertion.expectation
        except:
            pass

    def mutate(self, param: ObstacleMutationParams) -> ObstacleSolution:
        mutant_obstacle = self.modify_obstacle(
            self.obstacle, param.property, param.delta
        )
        mutant_test = copy.deepcopy(self.test)
        mutant_test.simulation.obstacles[0] = Obstacle(
            mutant_obstacle.size, mutant_obstacle.position
        )
        mutant = type(self)(mutant_test)

        return mutant

    def check_validity(self):
        for obst in self.test.simulation.obstacles:
            if obst.size.l <= 0 or obst.size.w <= 0 or obst.size.h <= 0:
                return False
        return True

    def modify_obstacle(
        self, obstacle: Obstacle, property: str, delta: float
    ) -> Obstacle:
        mutant_obstacle = copy.deepcopy(obstacle)
        ### resize the obstacle with fixed center position
        if property == "sx":
            mutant_obstacle.size = Obstacle.Size(
                l=mutant_obstacle.size.l + delta,
                w=mutant_obstacle.size.w,
                h=mutant_obstacle.size.h,
            )
            # mutant_obstacle.size.l += delta
        if property == "sy":
            mutant_obstacle.size = Obstacle.Size(
                l=mutant_obstacle.size.l,
                w=mutant_obstacle.size.w + delta,
                h=mutant_obstacle.size.h,
            )
            # mutant_obstacle.size.w += delta
        if property == "sz":
            mutant_obstacle.size = Obstacle.Size(
                l=mutant_obstacle.size.l,
                w=mutant_obstacle.size.w,
                h=mutant_obstacle.size.h + delta,
            )
            # mutant_obstacle.size.h += delta

        ### change position
        if property == "x":
            mutant_obstacle.position = Obstacle.Position(
                x=mutant_obstacle.position.x + delta,
                y=mutant_obstacle.position.y,
                z=mutant_obstacle.position.z,
                r=mutant_obstacle.position.r,
            )
            # mutant_obstacle.position.x += delta
        if property == "y":
            mutant_obstacle.position = Obstacle.Position(
                x=mutant_obstacle.position.x,
                y=mutant_obstacle.position.y + delta,
                z=mutant_obstacle.position.z,
                r=mutant_obstacle.position.r,
            )
            # mutant_obstacle.position.y += delta

        ### rotation
        if property == "r":
            mutant_obstacle.position = Obstacle.Position(
                x=mutant_obstacle.position.x,
                y=mutant_obstacle.position.y,
                z=mutant_obstacle.position.z,
                r=mutant_obstacle.position.r + delta,
            )
            # mutant_obstacle.position.r += delta

        ### moving only one of the borders
        # if property == "x1":
        #     mutant_obstacle.size.l += delta
        # if property == "y1":
        #     mutant_obstacle.size.w += delta
        # if property == "z1":
        #     mutant_obstacle.size.h += delta
        # if property == "x2":
        #     mutant_obstacle.size.l += delta
        #     mutant_obstacle.position.x -= delta * math.cos(mutant_obstacle.position.r)
        #     mutant_obstacle.position.y -= delta * math.sin(mutant_obstacle.position.r)
        # if property == "y2":
        #     mutant_obstacle.size.w += delta
        #     mutant_obstacle.position.x -= delta * math.sin(mutant_obstacle.position.r)
        #     mutant_obstacle.position.y -= delta * math.cos(mutant_obstacle.position.r)

        return mutant_obstacle

    def get_fitness(self, trajectory: Trajectory):
        return -self.goal.distance(trajectory)


class ObstacleMutationParams(MutationParams):
    def __init__(
        self,
        property=None,
        delta=0,
    ) -> None:
        super().__init__()
        self.property = property
        self.delta = delta

    def log_str(self, sol: ObstacleSolution):
        return f"{self.property},{self.delta},{sol.obstacle.position.x},{sol.obstacle.position.y},{sol.obstacle.size.l},{sol.obstacle.size.w},{sol.obstacle.size.h},{sol.obstacle.position.r}"

    @classmethod
    def log_header(cls):
        return "property, delta, x, y, l, w, h, r,"
