import os
import sys
from sim_user import SimulatedUser
from progress_indicator import ProgressIndicator
from config_readers.simulation_config_reader import SimulationConfigReader
import gc
import logging
import time


def main(config_filename, mock=False):
    """
    The main simulation!
    For every configuration permutation, create a Simulated user object, and run the simulation (the while loop).
    Then save, report, and repeat ad naseum.
    """
    logging.basicConfig(filename="sim.log", level=logging.DEBUG)
    config_reader = SimulationConfigReader(config_filename, mock=mock)

    # For each combination of the iterables (i.e. each user type vs topic)
    for configuration in config_reader:
        # Check for output file
        log_file = configuration.base_id + ".log"
        log_file = os.path.join(configuration.output._OutputController__base_directory, log_file)
        start_time = time.time()
        user = SimulatedUser(configuration)  # Load user
        progress = ProgressIndicator(configuration)
        # configuration.output.display_config()

        while not configuration.user.logger.is_finished():
            progress.update()  # Update the progress indicator in the terminal.
            user.decide_action()

        configuration.output.display_report()
        configuration.output.save()
        print(f"done in {time.time()-start_time}s")
        gc.collect()

    completed_file = open(os.path.join(config_reader.get_base_dir(), "COMPLETED"), "w")
    completed_file.close()


def usage(script_name):
    """
    Prints the usage message to the output stream.
    """
    print("Usage: {0} [configuration_filename]".format(script_name))


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        usage(sys.argv[0])
    elif len(sys.argv) == 3 and sys.argv[2] == "--mock":
        main(sys.argv[1], True)
    else:
        main(sys.argv[1])
