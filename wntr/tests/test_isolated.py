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

        inp_file = resilienceMainDir + '/wntr/tests/networks_for_testing/test_isolated.inp'
        self.wn = self.wntr.network.WaterNetworkModel(inp_file)
        self.wn.options.report_timestep = 'all'
        self.wn.options.duration = 0
        for jname, j in self.wn.nodes(self.wntr.network.Junction):
            j.minimum_pressure = 0.0
            j.nominal_pressure = 15.0

        sim = self.wntr.sim.WNTRSimulator(self.wn, pressure_driven=True)
        self.sim = sim
        self.results = sim.run_sim()

    @classmethod
    def tearDownClass(self):
        sys.path.remove(resilienceMainDir)

    def test_isolated(self):
        isolated = self.sim._get_isolated_junctions_and_links()
        self.assertEqual(isolated, (['11'],['22']))



