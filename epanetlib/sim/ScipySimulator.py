"""
QUESTIONS
"""

"""
TODO
1. Support for valves.
2. Support for reservoir head patterns.
"""

import epanetlib as en
from epanetlib.units import convert
import matplotlib.pyplot as plt
import numpy as np
np.set_printoptions(threshold='nan', linewidth=300, precision=3, suppress=True)
from scipy.optimize import fsolve
#import numdifftools as ndt
import warnings
import copy
import sys
import time

from WaterNetworkSimulator import *
from epanetlib.network.WaterNetworkModel import Junction, Tank, Reservoir, Pipe, Pump
import pandas as pd

class ScipySimulator(WaterNetworkSimulator):
    """
    Run simulations using scipy.optimize.
    """

    def __init__(self, wn):
        """
        Simulator object to be used for running scipy simulations.

        Parameters
        ---------
        wn : WaterNetworkModel
            A water network
        """
        WaterNetworkSimulator.__init__(self, wn)

        # Create dictionaries with node and link id's to names
        self._node_id_to_name = {}
        self._link_id_to_name = {}
        self._node_name_to_id = {}
        self._node_name_to_tank_id = {}
        self._tank_id_to_node_name = {}
        self._node_name_to_reservoir_id = {}
        self._link_name_to_id = {}
        n = 0
        t = 0
        r = 0
        for node_name, node in self._wn.nodes():
            self._node_id_to_name[n] = node_name
            self._node_name_to_id[node_name] = n
            n += 1
            if isinstance(node, Tank):
                self._node_name_to_tank_id[node_name] = t
                self._tank_id_to_node_name[t] = node_name
                t += 1
            elif isinstance(node, Reservoir):
                self._node_name_to_reservoir_id[node_name] = r
                r += 1
        l = 0
        for link_name, link in self._wn.links():
            self._link_id_to_name[l] = link_name
            self._link_name_to_id[link_name] = l
            l += 1

        # Initial values for simulation variables
        self._num_tanks = getattr(self._wn, '_num_tanks')
        self._num_reservoirs = getattr(self._wn, '_num_reservoirs')

        flow_0 = 0.1*np.ones(self._wn.num_links())
        headloss_0 = 10.0*np.ones(self._wn.num_links())
        head_0 = 200.0*np.ones(self._wn.num_nodes())
        # Set initial tank head
        for tank_name, tank in self._wn.nodes(Tank):
            tank_id = self._node_name_to_id[tank_name]
            head_0[tank_id] = tank.init_level + tank.elevation
        tank_inflow_0 = 0.1*np.ones(self._num_tanks)
        reservoir_demand_0 = np.ones(self._num_reservoirs)
        # State of simulation variables
        self._X = np.concatenate((flow_0, headloss_0, head_0, tank_inflow_0, reservoir_demand_0))

        # Initialize Gradient
        self._jac = np.zeros((len(self._X), len(self._X)))
        self._jac_counter = 0

        # Hazen-Williams resistance coefficient
        self._Hw_k = 10.67 # SI units = 4.727 in EPANET GPM units. See Table 3.1 in EPANET 2 User manual.

        self._func_eval_time = 0.0

    def run_sim(self):

        # Number of hydraulic timesteps
        n_timesteps = int(round(self._sim_duration_sec/self._hydraulic_step_sec))+1

        # Get all demand for complete time interval
        demand_dict = {}
        for node_name, node in self._wn.nodes():
            if isinstance(node, Junction):
                demand_values = self.get_node_demand(node_name)
                for t in range(n_timesteps):
                    demand_dict[(node_name, t)] = demand_values[t]
            else:
                for t in range(n_timesteps):
                    demand_dict[(node_name, t)] = 0.0

        # Create time controls dictionary
        link_status = {}
        for l in self._wn.time_controls:
            status_l = []
            for t in xrange(n_timesteps):
                time_min = t*self._hydraulic_step_sec
                status_l_t = self.is_link_open(l, time_min)
                status_l.append(status_l_t)
            link_status[self._link_name_to_id[l]] = status_l

        num_tanks = getattr(self._wn, '_num_tanks')
        num_reservoirs = getattr(self._wn, '_num_reservoirs')

        # Length of variables
        num_flows = self._wn.num_links()
        num_headloss = self._wn.num_links()
        num_heads = self._wn.num_nodes()

        # data for results object
        node_name = []
        node_type = []
        node_times = []
        node_head = []
        node_demand = []
        node_pressure = []
        link_name = []
        link_type = []
        link_times = []
        link_velocity = []
        link_flowrate = []

        # Create results object
        results = NetResults()

        # Load general simulation options into the results object
        self._load_general_results(results)

        #
        self._func_eval_time = 0.0

        # Create Delta time series
        results.time = pd.timedelta_range(start='0 minutes',
                                          end=str(self._sim_duration_sec) + ' seconds',
                                          freq=str(self._hydraulic_step_sec/60) + 'min')


        # Assert conditional controls are only provided for Tanks
        self._verify_conditional_controls_for_tank()

        # List of closed pump ids
        pumps_closed = []

        ######### MAIN SIMULATION LOOP ###############
        for t in xrange(n_timesteps):
            if t == 0:
                first_timestep = True
                last_tank_head = []
                for tank_id in xrange(num_tanks):
                    tank = self._wn.get_node(self._tank_id_to_node_name[tank_id])
                    last_tank_head.append(tank.elevation + tank.init_level)
            else:
                first_timestep = False

            # Get demands
            current_demands = [demand_dict[(self._node_id_to_name[n],t)] for n in xrange(self._wn.num_nodes())]

            pipes_closed = []
            # Get time controls
            for l_id, status in link_status.iteritems():
                if not status[t]:
                    pipes_closed.append(l_id)

            # Combine list of closed links
            links_closed = pipes_closed + pumps_closed

            prev_X = copy.copy(self._X)

            # Use scipy to solve
            [x, info, flag, msg] = fsolve(self._hydraulic_equations, prev_X, fprime=self._jacobian,
                                          args=(last_tank_head, current_demands, first_timestep, links_closed),
                                          maxfev=100000, xtol=1e-6, full_output=True)

            # Update results only if fsolve converged
            if flag == 1:
                self._X = x
            else:
                print msg
                self._X = x

            # Jacobian function
            #temp_func = lambda x: self._hydraulic_equations(x, last_tank_head, current_demands, first_timestep, links_closed)
            #Jfunc = ndt.Jacobian(temp_func)
            #
            #new_jac = Jfunc(self._X)
            #
            ##print "Numerical Jacobian: "
            ##print new_jac
            #
            ##print "Analytical Jacobian: "
            ##print self._jac
            #
            ##print self._jac == new_jac
            ##print self._jac - new_jac
            #all_close = np.allclose(new_jac, self._jac)
            #print all_close
            #if not all_close:
            #    print self._jac - new_jac
            #    print "\n\n Numerical Jacobian: "
            #    print new_jac.shape
            #    print new_jac
            #
            #    print "\n\n Analytical Jacobian: "
            #    print self._jac.shape
            #    print self._jac
            #    exit()

            # Load results from scipy
            flow = self._X[0:num_flows]
            headloss = self._X[num_flows:num_flows+num_headloss]
            head = self._X[num_flows+num_headloss:num_flows+num_headloss+num_heads]
            tank_inflow = self._X[num_flows+num_headloss+num_heads:num_flows+num_headloss+num_heads+num_tanks]
            reservoir_demand = self._X[num_flows+num_headloss+num_heads+num_tanks:num_flows+num_headloss+num_heads+num_tanks+num_reservoirs]
            for tank_id in xrange(num_tanks):
                node_id = self._node_name_to_id[self._tank_id_to_node_name[tank_id]]
                last_tank_head[tank_id] = head[node_id]

            # Apply conditional controls
            pumps_closed = self._apply_conditional_controls(head, pumps_closed)

            # Load all node results
            timedelta = results.time[t]
            print "Running Hydraulic Simulation at time ", timedelta, " ..."
            for n in xrange(self._wn.num_nodes()):
                name = self._node_id_to_name[n]
                node = self._wn.get_node(name)
                node_name.append(name)
                node_type.append(self._get_node_type(name))
                node_times.append(timedelta)
                node_head.append(head[n])
                # Add node demand
                if isinstance(node, Junction):
                    node_demand.append(current_demands[n])
                elif isinstance(node, Reservoir):
                    reserv_id = self._node_name_to_reservoir_id[name]
                    node_demand.append(reservoir_demand[reserv_id])
                elif isinstance(node, Tank):
                    tank_id = self._node_name_to_tank_id[name]
                    node_demand.append(tank_inflow[tank_id])
                else:
                    node_demand.append(0.0)
                # Add pressure
                if isinstance(node, Reservoir):
                    pressure_n_t = 0.0
                else:
                    pressure_n_t = head[n] - node.elevation
                node_pressure.append(pressure_n_t)

            # Load all link results
            for l in xrange(self._wn.num_links()):
                name = self._link_id_to_name[l]
                link = self._wn.get_link(name)
                link_name.append(name)
                link_type.append(self._get_link_type(name))
                link_times.append(timedelta)
                link_flowrate.append(flow[l])
                if isinstance(link, Pipe):
                    velocity_l_t = 4.0*abs(flow[l])/(math.pi*link.diameter**2)
                else:
                    velocity_l_t = 0.0
                link_velocity.append(velocity_l_t)

        # END MAIN SIM LOOP

        # Save results into the results object
        node_data_frame = pd.DataFrame({'time': node_times,
                                        'node': node_name,
                                        'demand': node_demand,
                                        'head': node_head,
                                        'pressure': node_pressure,
                                        'type': node_type})

        node_pivot_table = pd.pivot_table(node_data_frame,
                                          values=['demand', 'head', 'pressure', 'type'],
                                          index=['node', 'time'],
                                          aggfunc= lambda x: x)
        results.node = node_pivot_table

        link_data_frame = pd.DataFrame({'time': link_times,
                                        'link': link_name,
                                        'flowrate': link_flowrate,
                                        'velocity': link_velocity,
                                        'type': link_type})

        link_pivot_table = pd.pivot_table(link_data_frame,
                                              values=['flowrate', 'velocity', 'type'],
                                              index=['link', 'time'],
                                              aggfunc= lambda x: x)
        results.link = link_pivot_table

        print "Function evaluation time: ", self._func_eval_time
        return results

    def _hydraulic_equations(self, x, last_tank_head, nodal_demands, first_timestep, links_closed):

        t0 = time.time()
        # Get number of network components
        num_nodes = self._wn.num_nodes()
        num_links = self._wn.num_links()
        num_tanks = getattr(self._wn, '_num_tanks')
        num_reservoirs = getattr(self._wn, '_num_reservoirs')

        # Calculate number of variables
        num_flows = num_links
        num_headloss = num_links
        num_heads = num_nodes

        # Variables
        # x is concatination of following variables = [flow(each link), headloss(each link), head(each node), tank_inflow(each tank), reservoir_demand(each reservoir)]
        flow = x[0:num_flows]
        headloss = x[num_flows:num_flows+num_headloss]
        head = x[num_flows+num_headloss:num_flows+num_headloss+num_heads]
        tank_inflow = x[num_flows+num_headloss+num_heads:num_flows+num_headloss+num_heads+num_tanks]
        reservoir_demand = x[num_flows+num_headloss+num_heads+num_tanks:num_flows+num_headloss+num_heads+num_tanks+num_reservoirs]

        # Reinitialize Jacobian and counter
        self._jac_counter = 0
        self._jac = np.zeros((len(self._X), len(self._X)))

        # Node balance
        node_balance_residual = self._node_balance_residual(flow, tank_inflow, reservoir_demand, nodal_demands)

        # Headloss balance
        headloss_residual = self._headloss_residual(headloss, flow, links_closed)

        # Node head definition
        head_residual = self._head_residual(head, headloss, links_closed)

        # Tank head
        tank_head_residual = self._tank_head_residual(head, tank_inflow, last_tank_head, first_timestep)

        # Reservoir head residual
        reservoir_head_residual = self._reservoir_head_residual(head)

        # Closed links flow residual
        closed_links_flow_residual = self._closed_link_flow_residual(flow, links_closed)

        # Closed links headloss residual
        closed_links_headloss_residual = self._closed_link_headloss_residual(headloss, links_closed)

        all_residuals = np.concatenate((node_balance_residual,
                         headloss_residual,
                         head_residual,
                         tank_head_residual,
                         reservoir_head_residual,
                         closed_links_flow_residual,
                         closed_links_headloss_residual))

        self._func_eval_time += time.time() - t0
        return all_residuals

    def _node_balance_residual(self, flow, tank_inflow, reservoir_demand, nodal_demands):
        """
        Mass balance at all the nodes

        Parameters
        ---------
        flow : list of floats
             List of flow values in each pipe

        Return
        --------
        List of residuals of the node mass balances
        """
        residual = []
        tank_inflow_offset = 2*self._wn.num_links() + self._wn.num_nodes()
        reservoir_demand_offset = tank_inflow_offset + self._num_tanks

        for node_name, node in self._wn.nodes():
            node_id = self._node_name_to_id[node_name]
            connected_links = self._wn.get_links_for_node(node_name)
            expr = 0
            for l in connected_links:
                link = self._wn.get_link(l)
                if link.start_node() == node_name:
                    link_id = self._link_name_to_id[l]
                    expr -= flow[link_id]
                    self._jac[self._jac_counter, link_id] = -1.0
                elif link.end_node() == node_name:
                    link_id = self._link_name_to_id[l]
                    expr += flow[link_id]
                    self._jac[self._jac_counter, link_id] = 1.0
                else:
                    raise RuntimeError('Node link is neither start nor end node.')
            if isinstance(node, Junction):
                residual.append(expr - nodal_demands[node_id])
            elif isinstance(node, Tank):
                tank_id = self._node_name_to_tank_id[node_name]
                residual.append(expr - tank_inflow[tank_id])
                self._jac[self._jac_counter, tank_inflow_offset+tank_id] = -1.0
            elif isinstance(node, Reservoir):
                reservoir_id = self._node_name_to_reservoir_id[node_name]
                residual.append(expr - reservoir_demand[reservoir_id])
                self._jac[self._jac_counter, reservoir_demand_offset + reservoir_id] = -1.0
            else:
                raise RuntimeError('Node type not recognised.')
            # Increment jacobian counter
            self._jac_counter += 1

        return residual

    def _headloss_residual(self, headloss, flow, links_cosed):

        residual = []
        headloss_offset = self._wn.num_links()

        for link_name, link in self._wn.links():
            link_id = self._link_name_to_id[link_name]
            if link_id in links_cosed:
                continue
            elif isinstance(link, Pipe):
                pipe_resistance_coeff = self._Hw_k*(link.roughness**(-1.852))*(link.diameter**(-4.871))*link.length # Hazen-Williams
                pipe_headloss = pipe_resistance_coeff*flow[link_id]*(abs(flow[link_id]))**0.852
                #pipe_headloss = pipe_resistance_coeff*LossFunc(flow[link_id])
                residual.append(pipe_headloss - headloss[link_id])
                #self._jac[self._jac_counter, link_id] = pipe_resistance_coeff*1.852*abs(flow[link_id])**0.852
                self._jac[self._jac_counter, link_id] = pipe_resistance_coeff*LossFuncDeriv(abs(flow[link_id]))
                self._jac[self._jac_counter, headloss_offset + link_id] = -1.0
            elif isinstance(link, Pump):
                A, B, C = link.get_head_curve_coefficients()
                pump_headgain = -1.0*A + B*abs(flow[link_id])**C
                residual.append(pump_headgain - headloss[link_id])
                self._jac[self._jac_counter, link_id] = B*C*abs(flow[link_id])**(C-1)
                self._jac[self._jac_counter, headloss_offset + link_id] = -1.0
            else:
                residual.append(0.0 - headloss[link_id])
                raise RuntimeError("Valves are currently not supported.")
            # Increment jacobian counter
            self._jac_counter += 1

        return residual

    def _head_residual(self, head, headloss, links_closed):

        residual = []
        headloss_offset = self._wn.num_links()
        head_offset = 2*self._wn.num_links()

        for link_name, link in self._wn.links():
            link_id = self._link_name_to_id[link_name]
            if link_id in links_closed:
                continue
            else:
                start_node_id = self._node_name_to_id[link.start_node()]
                end_node_id = self._node_name_to_id[link.end_node()]
                link_head_residual = headloss[link_id] - (head[start_node_id] - head[end_node_id])
                residual.append(link_head_residual)
                self._jac[self._jac_counter, headloss_offset + link_id] = 1.0
                self._jac[self._jac_counter, head_offset + start_node_id] = -1.0
                self._jac[self._jac_counter, head_offset + end_node_id] = 1.0
                # Increment jacobian counter
                self._jac_counter += 1

        return residual

    def _tank_head_residual(self, head, tank_inflow, last_tank_head, first_timestep):

        residual = []
        head_offset = 2*self._wn.num_links()
        tank_inflow_offset = 2*self._wn.num_links() + self._wn.num_nodes()

        for tank_name, tank in self._wn.nodes(Tank):
            tank_id = self._node_name_to_tank_id[tank_name]
            node_id = self._node_name_to_id[tank_name]
            if first_timestep:
                tank_residual = head[node_id] - (tank.init_level + tank.elevation)
                self._jac[self._jac_counter, head_offset + node_id] = 1.0
            else:
                tank_residual = (tank_inflow[tank_id]*self._hydraulic_step_sec*4.0)/(math.pi*(tank.diameter**2)) - (head[node_id]-last_tank_head[tank_id])
                self._jac[self._jac_counter, head_offset + node_id] = -1.0
                self._jac[self._jac_counter, tank_inflow_offset + tank_id] = (self._hydraulic_step_sec*4.0)/(math.pi*(tank.diameter**2))
            residual.append(tank_residual)
            # Increment jacobian counter
            self._jac_counter += 1

        return residual

    def _reservoir_head_residual(self, head):

        residual = []
        head_offset = 2*self._wn.num_links()

        for reservoir_name, reservoir in self._wn.nodes(Reservoir):
            node_id = self._node_name_to_id[reservoir_name]
            residual.append(head[node_id] - reservoir.base_head)
            self._jac[self._jac_counter, head_offset + node_id] = 1.0
            # Increment jacobian counter
            self._jac_counter += 1

        return residual

    def _closed_link_flow_residual(self, flow, links_closed):

        residual = []

        for l in links_closed:
            residual.append(flow[l])
            self._jac[self._jac_counter, l] = 1.0
            # Increment jacobian counter
            self._jac_counter += 1

        return residual

    def _closed_link_headloss_residual(self, headloss, links_closed):

        residual = []
        head_offset = 2*self._wn.num_links()

        for l in links_closed:
            residual.append(headloss[l])
            self._jac[self._jac_counter, head_offset + l] = 1.0
            # Increment jacobian counter
            self._jac_counter += 1

        return residual

    def _load_general_results(self, results):
        """
        Load general simulation options into the results object.

        Parameter
        ------
        results : NetworkResults object
        """
        # Load general results
        results.network_name = self._wn.name

        # Load simulator options
        results.simulator_options['type'] = 'SCIPY'
        results.simulator_options['start_time'] = self._sim_start_sec
        results.simulator_options['duration'] = self._sim_duration_sec
        results.simulator_options['pattern_start_time'] = self._pattern_start_sec
        results.simulator_options['hydraulic_time_step'] = self._hydraulic_step_sec
        results.simulator_options['pattern_time_step'] = self._pattern_step_sec

    def _verify_conditional_controls_for_tank(self):
        for link_name in self._wn.conditional_controls:
            for control in self._wn.conditional_controls[link_name]:
                for i in self._wn.conditional_controls[link_name][control]:
                    node_name = i[0]
                    node = self._wn.get_node(node_name)
                    assert(isinstance(node, Tank)), "Scipy simulator only supports conditional controls on Tank."

    def _apply_conditional_controls(self, head, pumps_closed):
        for link_name_k, value in self._wn.conditional_controls.iteritems():
            link_id_k = self._link_name_to_id[link_name_k]
            open_above = value['open_above']
            open_below = value['open_below']
            closed_above = value['closed_above']
            closed_below = value['closed_below']
            # If link is closed and the tank level goes below threshold, then open the link
            for i in open_below:
                node_name_i = i[0]
                value_i = i[1]
                tank_i = self._wn.get_node(node_name_i)
                node_id_i = self._node_name_to_id[node_name_i]
                current_tank_level = head[node_id_i] - tank_i.elevation
                if link_id_k in pumps_closed:
                    if current_tank_level <= value_i:
                        pumps_closed.remove(link_id_k)
                        print "Pump ", link_name_k, " opened"
            # If link is open and the tank level goes above threshold, then close the link
            for i in closed_above:
                node_name_i = i[0]
                value_i = i[1]
                tank_i = self._wn.get_node(node_name_i)
                node_id_i = self._node_name_to_id[node_name_i]
                current_tank_level = head[node_id_i] - tank_i.elevation
                if link_id_k not in pumps_closed and current_tank_level >= value_i:
                    pumps_closed.append(link_id_k)
                    print "Pump ", link_name_k, " closed"
            # If link is closed and tank level goes above threshold, then open the link
            for i in open_above:
                node_name_i = i[0]
                value_i = i[1]
                tank_i = self._wn.get_node(node_name_i)
                node_id_i = self._node_name_to_id[node_name_i]
                current_tank_level = head[node_id_i] - tank_i.elevation
                if link_id_k in pumps_closed:
                    if current_tank_level >= value_i:
                        pumps_closed.remove(link_id_k)
                        print "Pump ", link_name_k, " opened"
            # If link is open and the tank level goes below threshold, then close the link
            for i in closed_below:
                node_name_i = i[0]
                value_i = i[1]
                tank_i = self._wn.get_node(node_name_i)
                node_id_i = self._node_name_to_id[node_name_i]
                current_tank_level = head[node_id_i] - tank_i.elevation
                if link_id_k not in pumps_closed and current_tank_level <= value_i:
                    pumps_closed.append(link_id_k)
                    print "Pump ", link_name_k, " closed"

        return pumps_closed

    # Dummy function for fsolve to return the jacobian
    def _jacobian(self, x, last_tank_head, current_demands, first_timestep, links_closed):
        return self._jac


def f1(x):
    return 0.01*x


def f2(x):
    return 1.0*x**1.852


def Px(x):
    #return 1.05461308881e-05 + 0.0494234328901*x - 0.201070504673*x**2 + 15.3265906777*x**3
    return 2.45944613543e-06 + 0.0138413824671*x - 2.80374270811*x**2 + 430.125623753*x**3

def d_f1(x):
    return 0.01


def d_f2(x):
    return 1.852*x**0.852


def d_Px(x):
    #return 1.05461308881e-05 + 0.0494234328901*x - 0.201070504673*x**2 + 15.3265906777*x**3
    return 0.0138413824671 - 2*2.80374270811*x + 3*430.125623753*x**2

def LossFunc(Q):
    #q1 = 0.01
    #q2 = 0.05
    headloss = 0.
    abs_Q = abs(Q)
    q1 = 0.00349347323944
    q2 = 0.00549347323944
    if abs_Q < q1:
        headloss = f1(abs_Q)
    elif abs_Q > q2:
        headloss = f2(abs_Q)
    else:
        headloss = Px(abs_Q)

    if Q < 0:
        return -1*headloss
    else:
        return headloss

def LossFuncDeriv(abs_Q):
    #q1 = 0.01
    #q2 = 0.05
    headloss = 0.
    q1 = 0.00349347323944
    q2 = 0.00549347323944
    if abs_Q < q1:
        d_headloss = d_f1(abs_Q)
    elif abs_Q > q2:
        d_headloss = d_f2(abs_Q)
    else:
        d_headloss = d_Px(abs_Q)

    return d_headloss