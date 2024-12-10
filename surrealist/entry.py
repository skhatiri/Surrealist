#!/usr/bin/python3
from argparse import ArgumentParser
import logging
import os
import sys
from decouple import config

config("MAKEING_SURE_TO_INIT_CONFIG_BEFORE_LOADING_AERIALIST", default=True)
from aerialist.px4.trajectory import Trajectory
from aerialist.px4.drone_test import DroneTest

try:
    from .search.search_factory import SearchFactory
except:
    from search.search_factory import SearchFactory


logger = logging.getLogger(__name__)


def arg_parse():
    main_parser = ArgumentParser(
        description="Surrealist Test Generation",
    )
    subparsers = main_parser.add_subparsers()
    parser = subparsers.add_parser(name="generate", description="generate test cases")

    parser.add_argument("--seed", required=True, help="seed test description yaml file")

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
        "--seed-count",
        default=1,
        type=int,
        help="number of seeds to generate",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="experiment id",
    )

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
    parser.set_defaults(func=run_search)

    # evaluation parser
    evalute_parser = subparsers.add_parser(
        name="evaluate", description="evaluate given test suite"
    )
    evalute_parser.add_argument(
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
    evalute_parser.add_argument(
        "--tests",
        required=True,
        help="test suite address (root folder)",
    )
    evalute_parser.add_argument(
        "--id",
        default=None,
        help="experiment id",
    )
    # agent configs
    evalute_parser.add_argument(
        "-n",
        default=1,
        type=int,
        help="no. of parallel runs",
    )
    evalute_parser.add_argument(
        "--path",
        default=None,
        help="cloud output path to copy logs",
    )
    evalute_parser.set_defaults(func=run_evaluate)

    args = main_parser.parse_args()
    return args


def run_search(args):
    if args.objective == "projector" or args.objective == "segment":
        Trajectory.IGNORE_AUTO_MODES = True

    seed_test = DroneTest.from_yaml(args.seed)

    factory = SearchFactory(
        seed_test,
        args.objective,
        args.budget,
        args.n,
        args.seed_count,
        args.path,
        args.id,
    )
    factory.search()


def run_evaluate(args):
    factory = SearchFactory(
        seed_test=None,
        search_method=args.objective,
        simulations_count=args.n,
        path=args.path,
        id=args.id,
    )
    factory.evaluate(args.tests)


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
        args.func(args)

    except Exception as e:
        logger.exception("program terminated:" + str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
