import unittest
import logging
import sys
import os, inspect
resilienceMainDir = os.path.abspath(
    os.path.join( os.path.dirname( os.path.abspath( inspect.getfile(
        inspect.currentframe() ) ) ), '..', '..' ))

#logging.basicConfig(level=logging.INFO)


class TestLoggerDictionaries(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        sys.path.append(resilienceMainDir)
        import wntr
        self.wntr = wntr

        inp_file = resilienceMainDir + '/wntr/tests/networks_for_testing/net_test_unusual_controls.inp'
        self.wn = self.wntr.network.WaterNetworkModel(inp_file)
        self.wn.options.report_timestep = 'all'
        self.wn.options.duration = 172800/2
        for jname, j in self.wn.nodes(self.wntr.network.Junction):
            j.minimum_pressure = 0.0
            j.nominal_pressure = 15.0

        sim = self.wntr.sim.WNTRSimulator(self.wn, pressure_driven=True)
        self.sim = sim
        self.results = sim.run_sim()

    @classmethod
    def tearDownClass(self):
        sys.path.remove(resilienceMainDir)

    def test_status_closed_by_time_open_by_tank_no_longer_min(self):
        link = self.wn.get_link('110')
        self.assertEqual(link.status, 0)
        self.assertEqual(link._status, 1)
