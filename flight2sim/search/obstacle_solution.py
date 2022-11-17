from __future__ import annotations
import copy
import math
from aerialist.px4.drone_test import DroneTest
from aerialist.px4.obstacle import Obstacle
from .solution import Solution, MutationParams


class ObstacleSolution(Solution):
    def __init__(self, test: DroneTest) -> None:
        super().__init__(test)
        self.mutation_type = ObstacleMutationParams
        self.obstacle = test.simulation.obstacles[0]

    def mutate(self, param: ObstacleMutationParams) -> ObstacleSolution:
        mutant_obstacle = self.move_border(self.obstacle, param.border, param.delta)
        if (
            mutant_obstacle.size.x <= 0
            or mutant_obstacle.size.y <= 0
            or mutant_obstacle.size.z <= 0
        ):
            # mutation is invalid (size has negative elements)
            mutant = copy.deepcopy(self)
            mutant.obstacle = mutant_obstacle
            mutant.fitness = self.INVALID_SOL_FITNESS
        else:
            mutant_test = copy.deepcopy(self.test)
            mutant_test.simulation.obstacles[0] = Obstacle(
                mutant_obstacle.size, mutant_obstacle.position, mutant_obstacle.angle
            )
            mutant = type(self)(mutant_test)

        return mutant

    def move_border(self, obstacle: Obstacle, border: str, delta: float) -> Obstacle:
        mutant_obstacle = copy.deepcopy(obstacle)
        if border == "sx":
            mutant_obstacle.size.x += delta
        if border == "sy":
            mutant_obstacle.size.y += delta
        if border == "sz":
            mutant_obstacle.size.z += delta
        if border == "x1":
            mutant_obstacle.size.x += delta
            # obstacle.p2.x += delta
        if border == "y1":
            mutant_obstacle.size.y += delta
            # obstacle.p2.y += delta
        if border == "z1":
            mutant_obstacle.size.z += delta
        if border == "x2":
            mutant_obstacle.size.x += delta
            mutant_obstacle.position.x -= delta * math.cos(mutant_obstacle.angle)
            mutant_obstacle.position.y -= delta * math.sin(mutant_obstacle.angle)
            # obstacle.p1.x += delta
        if border == "y2":
            mutant_obstacle.size.y += delta
            mutant_obstacle.position.x -= delta * math.sin(mutant_obstacle.angle)
            mutant_obstacle.position.y -= delta * math.cos(mutant_obstacle.angle)
            # obstacle.p1.y += delta

        if border == "x":
            mutant_obstacle.position.x += delta
            # obstacle.p1.x += delta
            # obstacle.p2.x += delta
        if border == "y":
            mutant_obstacle.position.y += delta
            # obstacle.p1.y += delta
            # obstacle.p2.y += delta
        if border == "r":
            mutant_obstacle.angle += delta

        return mutant_obstacle


class ObstacleMutationParams(MutationParams):
    def __init__(
        self,
        border=None,
        delta=0,
    ) -> None:
        super().__init__()
        self.border = border
        self.delta = delta

    def log_str(self, sol: ObstacleSolution):
        return f"{self.border},{self.delta},{sol.obstacle.position.x},{sol.obstacle.position.y},{sol.obstacle.size.x},{sol.obstacle.size.y},{sol.obstacle.size.z},{sol.obstacle.angle}"

    @classmethod
    def log_header(cls):
        return "border, delta, x, y, l, w, h, r,"
