from __future__ import annotations
import copy
from aerialist.px4.drone_test import DroneTest
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
        if border == "x1":
            mutant_test.simulation.obstacles[0].p1.x += delta
        if border == "y1":
            mutant_test.simulation.obstacles[0].p1.y += delta
        if border == "x2":
            mutant_test.simulation.obstacles[0].p2.x += delta
        if border == "y2":
            mutant_test.simulation.obstacles[0].p2.y += delta
        if border == "x":
            mutant_test.simulation.obstacles[0].p1.x += delta
            mutant_test.simulation.obstacles[0].p2.x += delta
        if border == "y":
            mutant_test.simulation.obstacles[0].p1.y += delta
            mutant_test.simulation.obstacles[0].p2.y += delta
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
        return f"{self.border},{self.delta},{sol.obstacle.p1.x},{sol.obstacle.p1.y},{sol.obstacle.p2.x},{sol.obstacle.p2.y}"

    @classmethod
    def log_header(cls):
        return "border, delta, x1, y1, x2, y2,"
