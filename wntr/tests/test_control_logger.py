import unittest
import sys
import os, inspect
resilienceMainDir = os.path.abspath(
    os.path.join( os.path.dirname( os.path.abspath( inspect.getfile(
        inspect.currentframe() ) ) ), '..', '..' ))



class TestLoggerDictionaries(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        sys.path.append(resilienceMainDir)
        import wntr
        self.wntr = wntr

        inp_file = resilienceMainDir + '/wntr/tests/networks_for_testing/time_controls_test_network.inp'
        self.wn = self.wntr.network.WaterNetworkModel(inp_file)
        self.wn.options.report_timestep = 'all'
        self.wn.options.duration = 172800
        for jname, j in self.wn.nodes(self.wntr.network.Junction):
            j.minimum_pressure = 0.0
            j.nominal_pressure = 15.0

        sim = self.wntr.sim.WNTRSimulator(self.wn, pressure_driven=True)
        self.sim = sim
        self.results = sim.run_sim()

    @classmethod
    def tearDownClass(self):
        sys.path.remove(resilienceMainDir)

    def test_control_times_added(self):
        import wntr
        self._control_log = wntr.sim.WNTRSimulator.get_control_log(self.sim)
        self.control_logger_working = False
        link = self.wn.get_link('pipe2')
        if 18000 in self._control_log.times[link]['status'] and 0 in self._control_log.values[link][
            'status'] and 'LINKpipe2CLOSEDATTIME18000' in self._control_log.control_names[link]['status']:
            self.control_logger_working = True
        self.assertEqual(self.control_logger_working, True)