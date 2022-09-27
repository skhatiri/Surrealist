#!/usr/bin/python3
from argparse import ArgumentParser
import logging
import os
import sys
from decouple import config
from aerialist.px4.obstacle import Obstacle
from aerialist.px4.trajectory import Trajectory
from aerialist.px4.command import Command

try:
    from .search.command_projector_search import CommandProjectorSearch
    from .search.command_solution import CommandSolution
    from .search.command_segment_search import CommandSegmentSearch
    from .search.obstacle2_search import Obstacle2Search
    from .search.obstacle2_solution import Obstacle2Solution
    from .search.obstacle_search import ObstacleSearch
    from .search.obstacle_solution import ObstacleSolution
except:
    from search.command_projector_search import CommandProjectorSearch
    from search.command_solution import CommandSolution
    from search.command_segment_search import CommandSegmentSearch
    from search.obstacle2_search import Obstacle2Search
    from search.obstacle2_solution import Obstacle2Solution
    from search.obstacle_search import ObstacleSearch
    from search.obstacle_solution import ObstacleSolution


logger = logging.getLogger(__name__)


def arg_parse():
    parser = ArgumentParser(
        description="Comunicate with and send control commands to drones"
    )
    parser.add_argument(
        "-e",
        "--env",
        default=config("SIMULATOR", default="gazebo"),
        choices=["gazebo", "jmavsim", "avoidance"],
        help="the simulator environment to run",
    )

    parser.add_argument("--log", default=None, help="original log file address")
    parser.add_argument("--commands", default=None, help="seed commands file address")
    parser.add_argument(
        "--trajectory", default=None, help="expected trajectory file address"
    )
    parser.add_argument(
        "-m", "--mission", default=None, help="original mission file address"
    )
    parser.add_argument("--params", default=None, help="params file address")
    parser.add_argument("--path", default=None, help="cloud output path to copy logs")
    parser.add_argument(
        "-n",
        default=1,
        type=int,
        help="no. of parallel evaluations",
    )

    parser.add_argument(
        "--obst",
        nargs=6,
        type=float,
        help="obstacle poisition and size to put in simulation environment: [x1,y1,z1,x2,y2,z2] in order",
        default=[],
    )
    parser.add_argument(
        "--obst2",
        nargs=6,
        type=float,
        help="obstacle poisition and size to put in simulation environment: [x1,y1,z1,x2,y2,z2] in order",
        default=[],
    )
    sub_parsers = parser.add_subparsers(help="sub-command help")
    search_parser = sub_parsers.add_parser(
        "search", help="search for best set of commands to replicate the scenario"
    )
    search_parser.add_argument(
        "obj",
        help="search objective",
        choices=["projector", "segment", "obstacle", "obstacle2"],
    )
    search_parser.add_argument(
        "-t",
        "--tries",
        default=10,
        type=int,
        help="max # of tries to find better solution",
    )
    search_parser.add_argument(
        "-r", "--runs", default=3, type=int, help="max # of runs"
    )
    search_parser.add_argument(
        "-p",
        "--projection",
        default=1,
        type=float,
        help="initial projection on the original commands",
    )

    search_parser.set_defaults(func=run_search)

    return args


def run_search(args):
    if not args.obj.startswith("obstacle"):
        Trajectory.IGNORE_AUTO_MODES = True
    if args.trajectory is None:
        trajectory = Trajectory.extract_from_log(args.log, is_jmavsim=args.jmavsim)
    else:
        trajectory = Trajectory.extract_from_csv(args.trajectory)
    if args.obj == "projector" or args.obj == "segment":
        if args.commands:
            commands = Command.extract_from_csv(args.commands)
        else:
            commands = Command.extract_from_log(args.log)

        seed = CommandSolution(commands)
        if args.projection != 1:
            seed = seed.project(
                args.projection, args.projection, args.projection, args.projection
            )
        if args.obj == "projector":
            searcher_type = CommandProjectorSearch
        elif args.obj == "segment":
            searcher_type = CommandSegmentSearch

    elif args.obj == "obstacle":
        obs = Obstacle.from_coordinates(args.obst)
        seed = ObstacleSolution(args.mission, obs)
        searcher_type = ObstacleSearch

    elif args.obj == "obstacle2":
        obs1 = Obstacle.from_coordinates(args.obst)
        obs2 = Obstacle.from_coordinates(args.obst2)
        seed = Obstacle2Solution(args.mission, obs1, obs2)
        trajectory = None
        searcher_type = Obstacle2Search

    searcher = searcher_type(seed, trajectory, args.runs)
    searcher.search(args.tries)


def config_loggers():
    os.makedirs("logs/", exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        filename="logs/root.log",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler("logs/lib.log")
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    px4 = logging.getLogger("px4")
    main = logging.getLogger("__main__")
    alg = logging.getLogger("algorithms")
    px4.addHandler(c_handler)
    alg.addHandler(c_handler)
    main.addHandler(c_handler)
    px4.addHandler(f_handler)
    alg.addHandler(f_handler)
    main.addHandler(f_handler)


if __name__ == "__main__":
    try:
        config_loggers()
        args = arg_parse()
        logger.info(f"preparing the experiment environment...{args}")
        args.func(args)

    except Exception as e:
        logger.exception("program terminated:" + str(e), exc_info=True)
        sys.exit(1)
