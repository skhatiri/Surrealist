from __future__ import annotations
from typing import List, Tuple
import copy
from decouple import config
from aerialist.px4.command import Command, FlightMode
from .solution import Solution, MutationParams


class CommandSolution(Solution):
    def __init__(
        self,
        commands: List[Command],
        command_segments: List[List[Command]] = None,
    ) -> None:
        super().__init__(commands, None, None)
        if commands != None:
            self.command_segments = Command.extract_segments(commands)
        elif command_segments != None:
            self.command_segments = command_segments
            self.commands: List[Command] = []
            for seg in self.command_segments:
                self.commands += seg

    def mutate(self, param: MutationParams) -> CommandSolution:
        mutant = self
        if type(param) is CommandProjectionParams:
            mutant = mutant.project(*param.projector, param.time_range)
        elif type(param) is CommandSegmentParams:
            if param.count > 0:
                mutant = mutant.duplicate(param.seg_ind, param.count)
            elif param.count < 0:
                mutant = mutant.remove(param.seg_ind, -param.count)
        return mutant

    def project(
        self, x, y, z, r, time_range: Tuple[int, int] = None
    ) -> CommandSolution:
        commands = []
        for c in self.commands:
            if time_range is None or (
                time_range[0] <= c.timestamp and c.timestamp < time_range[1]
            ):
                commands.append(c.project(x, y, z, r))
            else:
                commands.append(c)
        return CommandSolution(commands)

    def duplicate(self, seg_ind: int, count: int = 1) -> CommandSolution:
        segments = copy.deepcopy(self.command_segments)
        command_ind = len(segments[seg_ind]) // 2
        insert_ind = len(segments[seg_ind]) // 2
        command = segments[seg_ind][command_ind]
        delta = (
            segments[seg_ind][-1].timestamp - segments[seg_ind][0].timestamp
        ) // len(segments[seg_ind])

        segments = copy.deepcopy(self.command_segments)
        for i in range(1, count + 1):
            dup = copy.copy(command)
            dup.timestamp += i * delta
            segments[seg_ind].insert(insert_ind + i, dup)

        for c in segments[seg_ind][insert_ind + count + 1 :]:
            c.timestamp += count * delta
        for seg in segments[seg_ind + 1 :]:
            for c in seg:
                c.timestamp += count * delta

        return CommandSolution(None, segments)

    def remove(self, seg_ind: int, count: int = 1) -> CommandSolution:
        segments = copy.deepcopy(self.command_segments)
        ind = max(0, (len(segments[seg_ind]) - count) // 2)

        last_ind = min(ind + count, len(segments[seg_ind]) - 1)
        delta = segments[seg_ind][last_ind].timestamp - segments[seg_ind][ind].timestamp
        del segments[seg_ind][ind:last_ind]

        for c in segments[seg_ind][ind:]:
            c.timestamp -= delta
        for seg in segments[seg_ind + 1 :]:
            for c in seg:
                c.timestamp -= delta

        return CommandSolution(None, segments)

    def is_manual_segment(self, seg_ind: int):
        return self.command_segments[seg_ind][0].mode == FlightMode.Setpoint
        # and len(self.command_segments[seg_ind]) >= 5


class CommandProjectionParams(MutationParams):
    def __init__(
        self, projector: Tuple = (1, 1, 1, 1), time_range: Tuple = None
    ) -> None:
        super().__init__()
        self.projector = projector
        self.time_range = time_range

    @classmethod
    def dimension_projector(cls, idx: int, value: float, time_range=None):
        p = [1] * 4
        p[idx] = value
        return CommandProjectionParams(tuple(p), time_range)

    def log_str(self, sol: CommandSolution):
        return f"{self.projector[0]},{self.projector[1]},{self.projector[2]},{self.projector[3]}"

    @classmethod
    def log_header(cls):
        return "x proj.,y proj.,z proj.,r proj.,"


class CommandSegmentParams(MutationParams):
    def __init__(
        self,
        seg_ind: int = None,
        count=0,
    ) -> None:
        super().__init__()
        self.seg_ind = seg_ind
        self.count = count

    def log_str(self, sol: CommandSolution):
        return f"{len(sol.commands)},{self.seg_ind},{self.count}"

    @classmethod
    def log_header(cls):
        return "com. len., seg ind, count,"
