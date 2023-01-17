# SURREALIST: Simulation-based Test Case Generation for UAVs in the Neighborhood of Real Flights

Unmanned aerial vehicles (UAVs), also known as drones, are acquiring increasing autonomy. With their commercial adoption, the problem of testing their functional and non-functional, and in particular their safety requirements has become a critical concern.
Simulation-based testing represents a fundamental practice, but the testing scenarios considered in software-in-the-loop testing may not be representative of the actual scenarios experienced in the field.
Here, we propose Surrealist (teSting Uavs in the neighboRhood of REAl fLIghtS), a novel search-based approach that analyses logs of real UAV flights and automatically generates simulation-based tests in the neighborhood of such real flights, thereby improving the realism and representativeness of the simulation-based tests.
This is done in two steps: first, Surrealist faithfully replicates the given UAV flight in the simulation environment, generating a simulation-based test that mirrors a pre-logged real-world behavior. Then, it smoothly manipulates the replicated flight conditions to discover slightly modified flight scenarios that are challenging or trigger misbehaviors of the UAV under test in simulation.
In our experiments, we were able to replicate a real flight accurately in the simulation environment and to expose unstable and potentially unsafe behavior in the neighborhood of a flight, which even led to crashes.

Surrealist internally uses [Aerialist](https://github.com/skhatiri/Aerialist), A UAV test bench developed on top of PX4, to evalute the UAV test cases in the simulation environment.

![surrealist approach overview](docs/overview.jpg)

## algorithms/

This package includes implementation of different (search-based) algorithms to (currently) reconstruct a recorded flight in simulation. This is done by starting with the initial series of commands logged during original flight, and searching for best parameters to reproduce the simulated flight as similar as possible to the original one.

## Setup

The toolkit requires python > 3.7 and has been tested with PX4 development environment on ubuntu 18.04 and 20.04

1. Setup PX4 development environment. Follow the instrudctions [here](https://docs.px4.io/master/en/dev_setup/dev_env_linux_ubuntu.html)
2. Clone this repository and cd into its root directory
3. `pip3 install -r requiremetns.txt`
4. `sudo apt-get install python3.7-tk`
5. Create a file named .env in the repository's root directory. Then copy and customize contents of [template.env](template.env) into it.

**Note:** Update *PX4_HOME* and *RESULTS_DIR* variables according to your installation.

## command-line interface

You can utilize the toolkit with following command line options:

**Note:** Before running any command, make sure you are at the root directory of the repository:

`cd drone-experiments/`

You can use `--help` option anywhere to get help on the command parameters.

- Replaying a pre-recorder PX4 log:

`python3 run.py --log resources/logs/t0.ulg experiment replay`

- Running an existing series of commands stored in a csv file. Look [here](resources/logs/t0_commands.csv) for an example (corresponding to previous .ulg file).

`python3 run.py --log resources/logs/t0_commands.csv experiment replay`

- Replaying a pre-recorder PX4 log with collission prevention enabled:

`python3 run.py --env avoidance --drone ros --log resources/logs/ta0.ulg experiment replay`

- running a manual flight through keyboard commands:

`python3 run.py experiment manual`

Look [here](https://github.com/skhatiri/drone-experiments/blob/5b7950dc99318d08dacab61ea8686c6d65402438/px4/drone.py#L76) for possible commands to send

**Note:** remaining commands are still actively on development and not stable.

- Search for best command serie to reconstruct a flight scenario:

`python3 run.py --log resources/logs/t0.ulg search --rounds 10`

## Using Docker

You can use the dockerfile to build a Docker image with all the requirements.

1. `docker build . -t drone-experiments`
2. `docker run -it drone-experiments bash`

You can now execute all the commands in the containers bash.

**Note:** Your user should be able to run docker commands without sudo. [check here](https://docs.docker.com/engine/install/linux-postinstall/)
**Note:** The .env for the docker image come from [template.env](template.env). You can customize them using environment variables for the Docker container.
