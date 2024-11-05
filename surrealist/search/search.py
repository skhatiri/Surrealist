from typing import Callable, Union
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from os import makedirs
from decouple import config
from csv_logger import CsvLogger
import logging
from aerialist.px4 import file_helper
from aerialist.px4.plot import Plot
from aerialist.px4.drone_test import AgentConfig
from .solution import Solution, MutationParams

AGENT = config("AGENT", default=AgentConfig.DOCKER)
if AGENT == AgentConfig.DOCKER:
    from aerialist.px4.docker_agent import DockerAgent

logger = logging.getLogger(__name__)


class Search(object):
    SEARCH_FLD_NAME = config("SEARCH_FLD_NAME", "")
    WEBDAV_DIR = config("WEBDAV_UP_FLD", default=None)
    LOCAL_DIR = config("RESULTS_DIR", default="results/")

    def __init__(
        self,
        seed: Solution,
        eval_runs: int = 1,
        path=WEBDAV_DIR,
        id=SEARCH_FLD_NAME,
    ) -> None:
        super().__init__()
        logger.info(f"init searcher with {eval_runs} evaluations")

        if id is None or id == "":
            folder_name = file_helper.time_filename()
        else:
            folder_name = id + "-" + file_helper.time_filename()

        self.dir = f"{self.LOCAL_DIR}{folder_name}/"
        makedirs(self.dir)
        Plot.DIR = self.dir
        seed.DIR = self.dir
        if AGENT == AgentConfig.DOCKER:
            DockerAgent.COPY_DIR = self.dir

        if path is not None:
            if not path.endswith("/"):
                path += "/"
            self.webdav_dir = f"{path}{folder_name}/"
            file_helper.create_dir(self.webdav_dir)
            Plot.WEBDAV_DIR = self.webdav_dir
            Solution.WEBDAV_DIR = self.webdav_dir
        else:
            self.webdav_dir = None
        logger.info(f"webdav dir:{self.webdav_dir}")
        self.mutation_type = seed.mutation_type
        self.csv_logger = CsvLogger(
            filename=f"{self.dir}log.csv",
            level=logging.DEBUG,
            header=f"time, iteration, fitness, taken?, comparison,{self.mutation_type.log_header()}[fitnesses], desc.",
        )
        self.seed = seed
        self.best_log = []
        self.all_log = []
        self.mutation_log = []
        self.runs = eval_runs

        self.best = seed

    def __del__(self):
        if self.webdav_dir is not None:
            logger.info("uploading logs at cleanup")
            file_helper.upload("logs/lib.txt", self.webdav_dir)
            file_helper.upload("logs/root.txt", self.webdav_dir)

    def search(self, budget: int = 5):
        logger.info(f"searching with {budget} tries")
        self.best.evaluate(self.runs, len(self.all_log))
        # to make invalid mutants recognizable
        Solution.INVALID_SOL_FITNESS = round(self.seed.fitness * 2) + 0.0000001
        self.log_step(self.best, self.mutation_type(), True, 0, "seed")
        try:
            self.search_mutation(budget)
        except Exception as e:
            logger.exception("search terminated:" + str(e), exc_info=True)
            if self.webdav_dir is not None:
                file_helper.upload("logs/lib.txt", self.webdav_dir)
                file_helper.upload("logs/root.txt", self.webdav_dir)
            self.log_step(self.best, self.mutation_type(), True, 0, "final solution")
            raise e
        self.log_step(self.best, self.mutation_type(), True, 0, "final solution")
        if self.webdav_dir is not None:
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
        max_taken_steps: int = 1000,
    ):
        best_param = default_param  # set to default (identity mutation)
        best_sol = seed
        eval_map = {default_param: seed}
        evaluations = 0
        step = step_size
        positive_moves = 0
        negative_moves = 0
        stall_iterations = 0
        taken_steps = 0
        while (
            evaluations <= budget
            and stall_iterations <= max_stall_iterations
            and taken_steps < max_taken_steps
        ):
            # initializing the solutions to compare
            # either new evaluations or from the cache
            param_up = best_param + step
            sol_up_eval = False
            if param_up in eval_map:
                sol_up = eval_map[param_up]
            else:
                mut_up = mutation_init(param_up)
                sol_up = seed.mutate(mut_up)
                evals = sol_up.evaluate(self.runs, len(self.all_log))
                if evals > 0:
                    sol_up_eval = True
                    evaluations += 1
                eval_map[param_up] = sol_up

            param_down = best_param - step
            sol_down_eval = False
            if param_down in eval_map:
                sol_down = eval_map[param_down]
            else:
                mut_down = mutation_init(param_down)
                sol_down = seed.mutate(mut_down)
                evals = sol_down.evaluate(
                    self.runs,
                    len(self.all_log) + sol_up_eval,
                )
                if evals > 0:
                    sol_down_eval = True
                    evaluations += 1
                eval_map[param_down] = sol_down

            # comparing the solutions to take the best direction
            if (
                sol_up.is_valid
                and sol_up.compare_to(best_sol) >= 1
                and ((not sol_down.is_valid) or sol_up.compare_to(sol_down) >= 1)
            ):
                comparison = 1
                best_sol = sol_up
                best_param = param_up
                taken_steps += 1
                stall_iterations = 0
                positive_moves += 1
                negative_moves = 0
                if positive_moves >= max_same_steps:
                    step *= 2

            elif (
                sol_down.is_valid
                and sol_down.compare_to(best_sol) >= 1
                and ((not sol_up.is_valid) or sol_down.compare_to(sol_up) >= 1)
            ):
                comparison = -1
                best_sol = sol_down
                best_param = param_down
                taken_steps += 1
                stall_iterations = 0
                negative_moves += 1
                positive_moves = 0
                if negative_moves >= max_same_steps:
                    step *= 2
            else:
                comparison = 0
                step = step / 2
                if step < min_step_size or (
                    sol_up.is_valid
                    and sol_up.compare_to(best_sol) == 0
                    and sol_down.is_valid
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
        if self.webdav_dir is not None:
            file_helper.upload(self.dir + "progress.png", self.webdav_dir)

    def log_step(
        self,
        sol: Solution,
        mut: MutationParams,
        taken: bool,
        comparison: int,
        desc: str = None,
    ):
        sol.plot(len(self.all_log))
        log = f'{len(self.all_log)},{round(sol.fitness,3)},{taken},{comparison},{mut.log_str(sol)},"{str([round(fit,1) for fit in sol.fitnesses])}"'
        if desc != None:
            log += "," + desc
        self.csv_logger.info(log)
        if self.webdav_dir is not None:
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
