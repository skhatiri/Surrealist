#!/usr/bin/python3
from argparse import ArgumentParser
import logging
import os
import sys
from decouple import config

config("MAKEING_SURE_TO_INIT_CONFIG_BEFORE_LOADING_AERIALIST", default=True)
from aerialist.px4.trajectory import Trajectory
from aerialist.px4.drone_test import (
    AssertionConfig,
    DroneConfig,
    DroneTest,
    SimulationConfig,
    TestConfig,
)

try:
    # from .search.command_projector_search import CommandProjectorSearch
    # from .search.command_solution import CommandSolution
    # from .search.command_segment_search import CommandSegmentSearch
    from .search.obstacle3_search import Obstacle3Search
    from .search.obstacle3_solution import Obstacle3Solution
    from .search.obstacle2_search import Obstacle2Search
    from .search.obstacle2_solution import Obstacle2Solution
    from .search.obstacle_search import ObstacleSearch
    from .search.obstacle_solution import ObstacleSolution
    from .search.search import Search
except:
    # from search.command_projector_search import CommandProjectorSearch
    # from search.command_solution import CommandSolution
    # from search.command_segment_search import CommandSegmentSearch
    from search.obstacle3_search import Obstacle3Search
    from search.obstacle3_solution import Obstacle3Solution
    from search.obstacle2_search import Obstacle2Search
    from search.obstacle2_solution import Obstacle2Solution
    from search.obstacle_search import ObstacleSearch
    from search.obstacle_solution import ObstacleSolution
    from search.search import Search


logger = logging.getLogger(__name__)


def arg_parse():
    parser = ArgumentParser(
        description="Search for best simulation-based test configurations to replicate the field test scenario"
    )
    parser.add_argument("--seed", default=None, help="seed test description yaml file")

    # search configs
    parser.add_argument(
        "objective",
        help="search objective",
        choices=[
            "obstacle",
            "obstacle2",
            "obstacle3",
            # "projector",
            # "segment",
        ],
    )
    parser.add_argument(
        "--budget",
        default=10,
        type=int,
        help="global budget of the search algorithm",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="experiment id",
    )
    # parser.add_argument(
    #     "-p",
    #     "--projection",
    #     default=1,
    #     type=float,
    #     help="initial projection on the original commands",
    # )

    # agent configs
    parser.add_argument(
        "-n",
        default=1,
        type=int,
        help="no. of parallel runs",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="cloud output path to copy logs",
    )

    # drone configs
    parser.add_argument(
        "--mission",
        default=None,
        help="input mission file address",
    )
    parser.add_argument(
        "--params",
        default=None,
        help="params file address",
    )

    # simulator configs
    parser.add_argument(
        "--simulator",
        default=config("SIMULATOR", default="gazebo"),
        choices=["gazebo", "jmavsim", "ros"],
        help="the simulator environment to run",
    )
    parser.add_argument(
        "--obstacle",
        nargs=7,
        type=float,
        help="obstacle poisition and size to put in simulation environment: [x1,y1,z1,x2,y2,z2] in order",
        default=[],
    )
    parser.add_argument(
        "--obstacle2",
        nargs=7,
        type=float,
        help="obstacle poisition and size to put in simulation environment: [x1,y1,z1,x2,y2,z2] in order",
        default=[],
    )

    # test configs
    parser.add_argument(
        "--commands",
        default=None,
        help="input commands file address",
    )

    # assertion configs
    parser.add_argument(
        "--log",
        default=None,
        help="original log file address",
    )

    parser.set_defaults(func=run_search)
    args = parser.parse_args()
    return args


def run_search(args):
    if args.objective == "projector" or args.objective == "segment":
        Trajectory.IGNORE_AUTO_MODES = True

    if args.seed is not None:
        seed_test = DroneTest.from_yaml(args.seed)
    else:
        drone_config = DroneConfig(
            port=(
                DroneConfig.ROS_PORT
                if args.simulator == SimulationConfig.ROS
                else DroneConfig.SITL_PORT
            ),
            params_file=args.params,
            mission_file=args.mission,
        )
        simulation_config = SimulationConfig(
            simulator=args.simulator,
            speed=1,
            headless=True,
            obstacles=args.obstacle + args.obstacle2,
        )
        test_config = TestConfig(
            commands_file=args.commands,
            speed=1,
        )
        if args.log is not None:
            assertion_config = AssertionConfig(
                log_file=args.log,
                variable=AssertionConfig.TRAJECTORY,
            )
        else:
            assertion_config = None
        seed_test = DroneTest(
            drone=drone_config,
            simulation=simulation_config,
            test=test_config,
            assertion=assertion_config,
        )
    # if args.projection != 1:
    #     seed_test = seed_test.project(
    #         args.projection, args.projection, args.projection, args.projection
    #     )

    if args.objective == "obstacle":
        seed_sol = ObstacleSolution(seed_test)
        searcher = ObstacleSearch(seed_sol, args.n, args.path, args.id)
    elif args.objective == "obstacle2":
        seed_sol = Obstacle2Solution(seed_test)
        searcher = Obstacle2Search(seed_sol, args.n, args.path, args.id)
    elif args.objective == "obstacle3":
        seed_sol = Obstacle3Solution(seed_test)
        searcher = Obstacle3Search(seed_sol, args.n, args.path, args.id)

    searcher.search(args.budget)


def config_loggers():
    os.makedirs("logs/", exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        filename="logs/root.txt",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler("logs/lib.txt")
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    px4 = logging.getLogger("aerialist")
    main = logging.getLogger("__main__")
    alg = logging.getLogger("search")
    ent = logging.getLogger("entry")
    px4.addHandler(c_handler)
    alg.addHandler(c_handler)
    main.addHandler(c_handler)
    ent.addHandler(c_handler)
    px4.addHandler(f_handler)
    alg.addHandler(f_handler)
    main.addHandler(f_handler)
    ent.addHandler(f_handler)


def main():
    try:
        config_loggers()
        args = arg_parse()
        logger.info(f"preparing the experiment environment...{args}")
        run_search(args)

    except Exception as e:
        logger.exception("program terminated:" + str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
