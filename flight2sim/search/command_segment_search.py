import random
import logging
from decouple import config
from aerialist.px4.trajectory import Trajectory
from .command_projector_search import CommandProjectorSearch
from .command_solution import (
    CommandProjectionParams,
    CommandSegmentParams,
    CommandSolution,
)
from .search import Search

logger = logging.getLogger(__name__)


class CommandSegmentSearch(Search):
    BETA = config("SEARCH_SEG_BETA", cast=int, default=5)

    def __init__(
        self, seed: CommandSolution, goal: Trajectory, eval_runs: int = 1
    ) -> None:
        super().__init__(seed, goal, eval_runs, CommandSegmentParams)
        self.manual_segments = []
        for i in range(len(seed.command_segments)):
            # skip too short or auto-mode segments
            if seed.is_manual_segment(i):
                self.manual_segments.append(i)

    def search_mutation(self, budget: int = 5):
        segments = self.best.trajectory.extract_segments()

        for i in range(len(segments)):
            seg_start = segments[i].positions[0].timestamp
            seg_end = segments[i].positions[-1].timestamp
            if i + 1 < len(segments):
                trj_end = segments[i + 1].positions[-1].timestamp
            else:
                trj_end = seg_end
            Trajectory.TIME_RANGE = (seg_start, trj_end)
            self.best.evaluate(self.goal)
            self.log_step(self.best, CommandProjectionParams(), True, 0, "segment seed")
            for i in [3, 0, 1, 2]:
                for d in [1, -1]:
                    mutation_init = (
                        lambda p: CommandProjectionParams.dimension_projector(
                            i, 1 + d * p, (seg_start, seg_end)
                        )
                    )
                    sol = self.psudo_binary_search(
                        mutation_init,
                        self.best,
                        budget,
                        CommandProjectorSearch.ALPHA,
                        0,
                    )
                    if sol is not None:
                        self.best = sol
                        break

        # for i in self.manual_segments:
        #     time_start = 0
        #     # (
        #     #     self.get_trajectory_segment(
        #     #         self.best.trajectory, self.best.command_segments[i][0].timestamp
        #     #     )
        #     #     .positions[0]
        #     #     .timestamp
        #     # )
        #     time_end = (
        #         self.get_next_trajectory_segment(
        #             self.best.trajectory, self.best.command_segments[i][-1].timestamp
        #         )
        #         .positions[-1]
        #         .timestamp
        #     )
        #     Trajectory.TIME_RANGE = (time_start, time_end)
        #     self.best.evaluate(self.goal)
        #     self.log_step(self.best, CommandSegmentParams(), True, 0, "segment seed")
        #     for d in [-1, +1]:
        #         mutation_init = lambda c: CommandSegmentParams(i, int(d * c))
        #         sol = self.psudo_binary_search(
        #             mutation_init, self.best, budget, self.BETA, 1
        #         )
        #         if sol is not None:
        #             self.best = sol
        #             break

        Trajectory.TIME_RANGE = None
        self.best.evaluate(self.goal)
        self.log_step(self.best, CommandSegmentParams(), True, 0, "final solution")

    @classmethod
    def get_trajectory_segment(cls, trj: Trajectory, timestamp: int):
        segments = trj.extract_segments()
        for seg in segments:
            if seg.positions[-1].timestamp >= timestamp:
                return seg
        return segments[0]

    @classmethod
    def get_next_trajectory_segment(cls, trj: Trajectory, timestamp: int):
        segments = trj.extract_segments()
        for i in range(len(segments)):
            if segments[i].positions[-1].timestamp >= timestamp:
                if i + 1 < len(segments):
                    return segments[i + 1]
                else:
                    return segments[i]
        return segments[-1]

    def get_mutation_random(self):
        segment_ind = random.choice(self.manual_segments)
        segment = self.best.command_segments[segment_ind]
        ind = random.randrange(len(segment))
        next = CommandSegmentParams(
            seg_ind=segment_ind,
            count=random.randrange(1, self.BETA),
        )
        if random.choice([True, False]):
            next.rmv_ind = ind
        else:
            next.dup_ind = ind
        return next

    def get_mutation_around(self, last_mutation: CommandSegmentParams):
        next = CommandSegmentParams(
            seg_ind=last_mutation.seg_ind,
            rmv_ind=last_mutation.rmv_ind,
            dup_ind=last_mutation.dup_ind,
            count=int(last_mutation.count / 2),
        )
        return next

    def get_mutation_invert(self, last_mutation: CommandSegmentParams):
        next = CommandSegmentParams(
            seg_ind=last_mutation.seg_ind,
            rmv_ind=last_mutation.dup_ind,
            dup_ind=last_mutation.rmv_ind,
            count=random.randrange(1, self.BETA),
        )
        next.inverted = True
        return next
