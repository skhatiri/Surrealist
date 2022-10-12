from __future__ import annotations
import copy
import math
from aerialist.px4.drone_test import DroneTest
from aerialist.px4.obstacle import Obstacle
from .solution import Solution, MutationParams


class ObstacleSolution(Solution):
    def __init__(self, test: DroneTest) -> None:
        super().__init__(test)
        self.obstacle = test.simulation.obstacles[0]

    def mutate(self, param: ObstacleMutationParams) -> ObstacleSolution:
        mutant = self
        mutant = mutant.move_border(param.border, param.delta)
        return mutant

    def move_border(self, border, delta):
        mutant_test = copy.deepcopy(self.test)
        obstacle = mutant_test.simulation.obstacles[0]
        if border == "sx":
            obstacle.size.x += delta
        if border == "sy":
            obstacle.size.y += delta
        if border == "sz":
            obstacle.size.z += delta
        if border == "x1":
            obstacle.size.x += delta
            # obstacle.p2.x += delta
        if border == "y1":
            obstacle.size.y += delta
            # obstacle.p2.y += delta
        if border == "z1":
            obstacle.size.z += delta
        if border == "x2":
            obstacle.size.x += delta
            obstacle.position.x -= delta * math.cos(obstacle.angle)
            obstacle.position.y -= delta * math.sin(obstacle.angle)
            # obstacle.p1.x += delta
        if border == "y2":
            obstacle.size.y += delta
            obstacle.position.x -= delta * math.sin(obstacle.angle)
            obstacle.position.y -= delta * math.cos(obstacle.angle)
            # obstacle.p1.y += delta

        if border == "x":
            obstacle.position.x += delta
            # obstacle.p1.x += delta
            # obstacle.p2.x += delta
        if border == "y":
            obstacle.position.y += delta
            # obstacle.p1.y += delta
            # obstacle.p2.y += delta
        if border == "r":
            obstacle.angle += delta

        if obstacle.size.x <= 0 or obstacle.size.y <= 0 or obstacle.size.z <= 0:
            # mutation is invalid (size has negative elements)
            mutant = copy.deepcopy(self)
            mutant.obstacle = obstacle
            mutant.fitness = -9999
        else:
            mutant_test.simulation.obstacles[0] = Obstacle(
                obstacle.size, obstacle.position, obstacle.angle
            )
            mutant = type(self)(mutant_test)

        return mutant


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
