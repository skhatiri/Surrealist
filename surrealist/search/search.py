from typing import Callable, Union
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from os import makedirs
from decouple import config
from csv_logger import CsvLogger
import logging
from aerialist.px4 import file_helper
from aerialist.px4.trajectory import Trajectory
from .solution import Solution, MutationParams


logger = logging.getLogger(__name__)


class Search(object):
    SEARCH_FLD_NAME = config("SEARCH_FLD_NAME", "")
    WEBDAV_DIR = config("WEBDAV_UP_FLD", default=None)
    LOCAL_DIR = config("RESULTS_DIR", default="results/")

    def __init__(
        self,
        seed: Solution,
        goal: Trajectory,
        eval_runs: int = 1,
        path=WEBDAV_DIR,
        id=SEARCH_FLD_NAME,
    ) -> None:
        super().__init__()
        logger.info(f"init searcher with {eval_runs} evaluations")
        if not path.endswith("/"):
            path += "/"
        if id is None or id == "":
            folder_name = file_helper.time_filename()
        else:
            folder_name = id + "-" + file_helper.time_filename()

        self.dir = f"{self.LOCAL_DIR}{folder_name}/"
        makedirs(self.dir)
        Trajectory.DIR = self.dir
        seed.DIR = self.dir

        if path is not None:
            self.webdav_dir = f"{path}{folder_name}/"
            file_helper.create_dir(self.webdav_dir)
            Trajectory.WEBDAV_DIR = self.webdav_dir
            Solution.WEBDAV_DIR = self.webdav_dir

        self.mutation_type = seed.mutation_type
        self.csv_logger = CsvLogger(
            filename=f"{self.dir}log.csv",
            level=logging.DEBUG,
            header=f"time, iteration, fitness, taken?, comparison,{self.mutation_type.log_header()}[fitnesses], desc.",
        )
        self.seed = seed
        self.goal = goal
        self.best_log = []
        self.all_log = []
        self.mutation_log = []
        self.runs = eval_runs

        self.best = seed

    def __del__(self):
        if self.WEBDAV_DIR is not None:
            logger.info("uploading logs at cleanup")
            file_helper.upload("logs/lib.txt", self.webdav_dir)
            file_helper.upload("logs/root.txt", self.webdav_dir)

    def search(self, budget: int = 5):
        logger.info(f"searching with {budget} tries")
        self.best.evaluate(self.goal, self.runs, len(self.all_log))
        # to make invalid mutants recognizable
        Solution.INVALID_SOL_FITNESS = round(self.seed.fitness * 2) + 0.0000001
        self.log_step(self.best, self.mutation_type(), True, 0, "seed")
        try:
            self.search_mutation(budget)
        except Exception as e:
            logger.exception("search terminated:" + str(e), exc_info=True)
            file_helper.upload("logs/lib.txt", self.webdav_dir)
            file_helper.upload("logs/root.txt", self.webdav_dir)
            self.log_step(self.best, self.mutation_type(), True, 0, "final solution")
            raise e
        self.log_step(self.best, self.mutation_type(), True, 0, "final solution")

        file_helper.upload("logs/lib.txt", self.webdav_dir)
        file_helper.upload("logs/root.txt", self.webdav_dir)

    def search_mutation(self, budget: int = 5):
        raise NotImplementedError()

    def greedy_search(
        self,
        mutation_init: Callable[[Union[int, float]], MutationParams],
        seed: Solution,
        budget: int,
        step_size: Union[int, float],
        default_param: Union[int, float] = 0,
        max_stall_iterations=5,
        max_same_steps=2,
        min_step_size: Union[int, float] = 0,
    ):
        best_param = default_param  # set to default (identity mutation)
        best_sol = seed
        eval_map = {default_param: seed}
        evaluations = 0
        step = step_size
        positive_moves = 0
        negative_moves = 0
        stall_iterations = 0
        while evaluations <= budget and stall_iterations <= max_stall_iterations:
            # initializing the solutions to compare
            # either new evaluations or from the cache
            param_up = best_param + step
            if param_up in eval_map:
                sol_up = eval_map[param_up]
                sol_up_eval = False
            else:
                mut_up = mutation_init(param_up)
                sol_up = seed.mutate(mut_up)
                sol_up.evaluate(self.goal, self.runs, len(self.all_log))
                eval_map[param_up] = sol_up
                sol_up_eval = True
                evaluations += 1

            param_down = best_param - step
            if param_down in eval_map:
                sol_down = eval_map[param_down]
                sol_down_eval = False
            else:
                mut_down = mutation_init(param_down)
                sol_down = seed.mutate(mut_down)
                sol_down.evaluate(
                    self.goal,
                    self.runs,
                    len(self.all_log) + sol_up_eval,
                )
                eval_map[param_down] = sol_down
                sol_down_eval = True
                evaluations += 1

            # comparing the solutions to take the best direction
            if sol_up.compare_to(best_sol) >= 1 and sol_up.compare_to(sol_down) >= 1:
                comparison = 1
                best_sol = sol_up
                best_param = param_up
                stall_iterations = 0
                positive_moves += 1
                negative_moves = 0
                if positive_moves >= max_same_steps:
                    step *= 2

            elif (
                sol_down.compare_to(best_sol) >= 1 and sol_down.compare_to(sol_up) >= 1
            ):
                comparison = -1
                best_sol = sol_down
                best_param = param_down
                stall_iterations = 0
                negative_moves += 1
                positive_moves = 0
                if negative_moves >= max_same_steps:
                    step *= 2
            else:
                comparison = 0
                step = step / 2
                if step < min_step_size or (
                    sol_up.compare_to(best_sol) == 0
                    and sol_down.compare_to(best_sol) == 0
                ):
                    stall_iterations = 1000
                else:
                    stall_iterations += 1

            # logging new evaluations
            if sol_up_eval:
                self.log_step(
                    sol_up,
                    mut_up,
                    comparison >= 1,
                    comparison,
                    f"up - step:{step} - budget:{budget-evaluations} - stall:{stall_iterations} ",
                )
            if sol_down_eval:
                self.log_step(
                    sol_down,
                    mut_down,
                    comparison <= -1,
                    -comparison,
                    f"down - step:{step} - budget:{budget-evaluations} - stall:{stall_iterations}  ",
                )

        if best_sol != seed:
            return (best_sol, evaluations)
        else:
            return (None, evaluations)

    def psudo_binary_search(
        self,
        mutation_init: Callable[[Union[int, float]], MutationParams],
        seed: Solution,
        budget: int,
        step: Union[int, float],
        min: Union[int, float] = 0,
    ):
        if min != 0:
            upper_band = min
        else:
            upper_band = step
        best = None
        while budget > 0:
            budget -= 1
            mutation = mutation_init(upper_band)
            current_sol = seed.mutate(mutation)
            current_sol.evaluate(self.goal, self.runs, len(self.all_log))
            comparison = current_sol.compare_to(seed if best is None else best)
            self.log_step(
                current_sol, mutation, comparison >= 1, comparison, "pre binary search"
            )

            if comparison <= -1 or (comparison == 0 and best is not None):
                return self.binary_search(
                    mutation_init,
                    seed,
                    budget,
                    upper_band - step,
                    upper_band,
                    best,
                )

            if comparison >= 1:
                best = current_sol

            upper_band += step

        return best

    def binary_search(
        self,
        mutation_init: Callable[[Union[int, float]], MutationParams],
        seed: Solution,
        budget: int,
        lower_bound: Union[int, float],
        upper_bound: Union[int, float],
        solution: Solution = None,
    ):
        if budget <= 0 or lower_bound >= upper_bound:
            return solution

        mid = (lower_bound + upper_bound) / 2
        if type(lower_bound) is int and type(upper_bound) is int:
            mid = int(mid)
        if mid == lower_bound or mid == upper_bound:
            return solution

        budget -= 1
        mutation = mutation_init(mid)

        if mutation is None:  # contract for no applyable mutation
            return self.binary_search(
                mutation_init, seed, budget, lower_bound, mid, solution
            )

        mid_sol = seed.mutate(mutation)
        mid_sol.evaluate(self.goal, self.runs, len(self.all_log))

        best = solution
        if best is None:
            best = seed

        comparison = mid_sol.compare_to(best)
        self.log_step(mid_sol, mutation, comparison >= 1, comparison, "binary search")
        if comparison >= 1:
            solution = mid_sol
            return self.binary_search(
                mutation_init, seed, budget, mid, upper_bound, solution
            )

        elif comparison <= -1:
            return self.binary_search(
                mutation_init, seed, budget, lower_bound, mid, solution
            )
        else:
            return solution

    def reverse_binary_search(
        self,
        mutation_init: Callable[[Union[int, float]], MutationParams],
        seed: Solution,
        budget: int,
        mid_point: Union[int, float],
        solution: Solution = None,
    ):
        if budget <= 0:
            return solution
        budget -= 1
        mutation = mutation_init(mid_point)
        mid_sol = seed.mutate(mutation)
        mid_sol.evaluate(self.goal, self.runs, len(self.all_log))

        best = solution
        if best is None:
            best = seed

        lower = mid_point / 2
        if type(mid_point) is int:
            lower = int(lower)

        comparison = mid_sol.compare_to(best)
        self.log_step(mid_sol, mutation, comparison >= 1, comparison)
        if comparison <= -1:
            return solution
            # if solution is not None:
            #     return self.binary_search(
            #         mutation_init, seed, budget, lower, mid_point, solution
            #     )
            # else:
            #     return None

        else:
            if comparison >= 1:
                solution = mid_sol
                return self.reverse_binary_search(
                    mutation_init, seed, budget, mid_point * 2, solution
                )
            elif solution is None:
                return self.reverse_binary_search(
                    mutation_init, seed, budget, mid_point * 2, solution
                )
            else:
                return solution
                # return self.binary_search(
                #     mutation_init, seed, budget, lower, mid_point, solution
                # )

    def random_search(self, max_tries=5):
        try:
            # todo: integrate opposite in the method get_next_mutation, probably as a state variable

            logger.info(f"searching with {max_tries} tries")
            self.best.evaluate(self.goal, self.runs, len(self.all_log))
            self.log_step(self.best, self.mutation_type(), True, 0, f"seed")

            tries = 0
            next_mutation = self.get_next_mutation()
            taken_steps = 0
            while tries < max_tries:
                mutation = next_mutation
                neighbour = self.best.mutate(mutation)
                neighbour.evaluate(self.goal, self.runs, len(self.all_log))
                comparison = neighbour.compare_to(self.best)
                if comparison > 0:
                    self.best = neighbour
                    taken_steps += 1
                    tries = 0
                    next_mutation = mutation
                else:
                    if comparison <= -1 and taken_steps == 0:
                        taken_steps = -1
                    next_mutation = self.get_next_mutation(mutation, taken_steps)
                    taken_steps = 0
                    tries += 1

                self.log_step(
                    neighbour,
                    mutation,
                    comparison >= 1,
                    comparison,
                )

        except Exception as e:
            logger.exception("search terminated:" + str(e), exc_info=True)

        file_helper.upload("logs/lib.log", self.webdav_dir)
        file_helper.upload("logs/root.log", self.webdav_dir)

    def get_next_mutation(
        self, last_mutation: MutationParams = None, last_steps: int = 0
    ) -> MutationParams:
        if last_mutation is None or last_steps <= 0:
            # last mutation is useless or decreasing the fitness
            # we go in a new random direction
            return self.get_mutation_random()
        else:
            # last mutation is applied as much as we can improve
            # we take shorter steps to fine tune the improvements
            return self.get_mutation_around(last_mutation)

    def get_mutation_random(self):
        raise NotImplementedError()

    def get_mutation_around(cls, last_mutation: MutationParams):
        raise NotImplementedError()

    def get_mutation_invert(cls, last_mutation: MutationParams):
        raise NotImplementedError()

    def plot(self):
        index = range(len(self.best_log))

        fig, fit_plt = plt.subplots()
        fit_plt.plot(index, self.best_log, label="best solution", color="blue")
        fit_plt.scatter(
            index, self.all_log, label="examined solutions", color="red", s=10
        )

        fit_plt.set_ylabel("fitness")
        fit_plt.set_xlabel("iteration")
        fit_plt.xaxis.set_major_locator(MaxNLocator(integer=True))
        fig.legend(loc="upper center", ncol=2)
        fig.suptitle(" ")

        fig.savefig(f"{self.dir}progress.png")
        plt.close(fig)
        file_helper.upload(self.dir + "progress.png", self.webdav_dir)

    def log_step(
        self,
        sol: Solution,
        mut: MutationParams,
        taken: bool,
        comparison: int,
        desc: str = None,
    ):
        sol.plot(self.goal, len(self.all_log))
        log = f'{len(self.all_log)},{round(sol.fitness,3)}, {taken}, {comparison}, {mut.log_str(sol)}, "{str([round(fit,1) for fit in sol.fitnesses])}"'
        if desc != None:
            log += "," + desc
        self.csv_logger.info(log)
        file_helper.upload(self.csv_logger.filename, self.webdav_dir)

        self.all_log.append(sol.fitness)
        if taken:
            self.best_log.append(sol.fitness)
            self.mutation_log.append(mut)
        else:
            if len(self.best_log) > 0:
                self.best_log.append(self.best_log[-1])
            else:
                self.best_log.append(self.best.fitness)

        self.plot()
