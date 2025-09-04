from decouple import config
import os
import pandas as pd
import logging

from aerialist.px4 import file_helper

from .obstacle_search import ObstacleSearch
from .obstacle2_solution import Obstacle2Solution, Obstacle2MutationParams
from .search import Search


logger = logging.getLogger(__name__)


class Obstacle2Search(ObstacleSearch):
    MUTATIONS_LIST = config("SEARCH_OBST_MUTATIONS", default="x,y")

    def __init__(
        self,
        seed: Obstacle2Solution,
        eval_runs: int = 1,
        path=Search.WEBDAV_DIR,
        id=Search.SEARCH_FLD_NAME,
    ) -> None:
        super().__init__(
            seed,
            eval_runs,
            path,
            id,
        )
        # self.csv_report = CsvLogger(
        #     filename=f"{self.dir}report.csv",
        #     level=logging.DEBUG,
        #     header=f"time,iteration,improved,{self.mutation_type.report_header()}",
        # )

    def summary(self):
        report_path = f"{self.dir}report.csv"
        if not os.path.exists(report_path):
            logger.warning(f"Report file not found: {report_path}")
            return
        df = pd.read_csv(report_path)
        df.columns = df.columns.str.strip()

        # ignoring the last row (normally contains repeated entry of the best test)
        if len(df) > 1:
            df = df.iloc[:-1]

        group_stats = (
            df.groupby("status")
            .agg(
                count=("distance", "count"),
                min_distance=("distance", "min"),
                max_distance=("distance", "max"),
                avg_distance=("distance", "mean"),
                min_gap=("gap", "min"),
                max_gap=("gap", "max"),
                avg_gap=("gap", "mean"),
                min_deviation=("deviation", "min"),
                max_deviation=("deviation", "max"),
                avg_deviation=("deviation", "mean"),
                min_duration=("duration", "min"),
                max_duration=("duration", "max"),
                avg_duration=("duration", "mean"),
                min_traveled=("traveled", "min"),
                max_traveled=("traveled", "max"),
                avg_traveled=("traveled", "mean"),
            )
            .reset_index()
        )

        overall_stats = pd.DataFrame(
            {
                "status": ["ALL"],
                "count": [df["distance"].count()],
                "min_distance": [df["distance"].min()],
                "max_distance": [df["distance"].max()],
                "avg_distance": [df["distance"].mean()],
                "min_gap": [df["gap"].min()],
                "max_gap": [df["gap"].max()],
                "avg_gap": [df["gap"].mean()],
                "min_deviation": [df["deviation"].min()],
                "max_deviation": [df["deviation"].max()],
                "avg_deviation": [df["deviation"].mean()],
                "min_duration": [df["duration"].min()],
                "max_duration": [df["duration"].max()],
                "avg_duration": [df["duration"].mean()],
                "min_traveled": [df["traveled"].min()],
                "max_traveled": [df["traveled"].max()],
                "avg_traveled": [df["traveled"].mean()],
            }
        )

        summary = pd.concat([group_stats, overall_stats], ignore_index=True)

        summary.to_csv(
            f"{self.dir}summary.csv",
            index=False,
            float_format="%.2f",
        )

    # def log_step(
    #     self,
    #     sol: Obstacle2Solution,
    #     mut: Obstacle2MutationParams,
    #     taken: bool,
    #     comparison: int,
    #     desc: str = None,
    # ):
    #     # report = f"{len(self.all_log)},{taken},{mut.report_str(sol)}"
    #     # self.csv_report.info(report)
    #     # if self.webdav_dir is not None:
    #     #     file_helper.upload(self.csv_report.filename, self.webdav_dir)

    #     super().log_step(sol, mut, taken, comparison, desc)
