import pandas as pd
import numpy as np
import datetime

class NetResults(object):
    def __init__(self):
        """
        A class to store water network simulation results.
        """

        # Simulation time series
        self.time = None
        self.generated_datetime = datetime.datetime
        self.network_name = None
        self.simulator_options = {}
        self.solver_statistics = {}
        self.link = None
        self.node = None

    def export_to_csv(self, csv_file_name):
        """
        Write the simulation results to csv file.

        Parameters
        ----------
        csv_file_name : string
            Name of csv file
        """
        # TODO

        pass

    def export_to_yml(self, yml_file_name):
        """
        Write the simulation results to yml file.

        Parameters
        ----------
        yml_file_name : string
            Name of yml file
        """
        # TODO
        pass