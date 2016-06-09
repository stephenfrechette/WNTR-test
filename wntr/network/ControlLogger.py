import pandas
from wntr.network import Link, Node
import logging
import traceback

logger = logging.getLogger(__name__)

class ControlLogger(object):
    def __init__(self, wn):
        """
        A class to track changes made by controls during the simulation.

        Parameters
        ----------
        wn : WaterNetworkModel
        """
        self.times = {}  # {obj_name: {attr: [list_of_times_in_seconds]}}
        self.values = {}  # {obj_name: {attr: [list_of_values]}}
        self.control_names = {}  # {obj_name: {attr: [list_of_control_names]}}
        self.changes_made = False
        self.objects_changed = set()
        self.objects_controlled = {}

        
        for link_name, link in wn._links.iteritems():
            self.times[link] = {}
            self.values[link] = {}
            self.control_names[link] = {}

            self.times[link]['status'] = [-1]
            self.values[link]['status'] = [link.status]
            self.control_names[link]['status'] = [None]

            self.times[link]['_status'] = [-1]
            self.values[link]['_status'] = [link._status]
            self.control_names[link]['_status'] = [None]

        for pipe_name, pipe in wn._pipes.iteritems():
            self.times[pipe]['roughness'] = [-1]
            self.values[pipe]['roughness'] = [pipe.roughness]
            self.control_names[pipe]['roughness'] = [None]

        for pump_name, pump in wn._pumps.iteritems():
            self.times[pump]['speed'] = [-1]
            self.values[pump]['speed'] = [pump.speed]
            self.control_names[pump]['speed'] = [None]

            self.times[pump]['power'] = [-1]
            self.values[pump]['power'] = [pump.power]
            self.control_names[pump]['power'] = [None]

            self.times[pump]['_power_outage'] = [-1]
            self.values[pump]['_power_outage'] = [pump._power_outage]
            self.control_names[pump]['_power_outage'] = [None]

        for node_name, node in wn._nodes.iteritems():
            self.times[node] = {}
            self.values[node] = {}
            self.control_names[node] = {}

        for junction_name, junction in wn._junctions.iteritems():
            self.times[junction]['leak_status'] = [-1]
            self.values[junction]['leak_status'] = [junction.leak_status]
            self.control_names[junction]['leak_status'] = [None]

            self.times[junction]['leak_area'] = [-1]
            self.values[junction]['leak_area'] = [junction.leak_area]
            self.control_names[junction]['leak_area'] = [None]

            self.times[junction]['leak_discharge_coeff'] = [-1]
            self.values[junction]['leak_discharge_coeff'] = [junction.leak_discharge_coeff]
            self.control_names[junction]['leak_discharge_coeff'] = [None]

        for tank_name, tank in wn._tanks.iteritems():
            self.times[tank]['leak_status'] = [-1]
            self.values[tank]['leak_satatus'] = [tank.leak_status]
            self.control_names[tank]['leak_status'] = [None]

            self.times[tank]['leak_area'] = [-1]
            self.values[tank]['leak_area'] = [tank.leak_area]
            self.control_names[tank]['leak_area'] = [None]

            self.times[tank]['leak_discharge_coeff'] = [-1]
            self.values[tank]['leak_discharge_coeff'] = [tank.leak_discharge_coeff]
            self.control_names[tank]['leak_discharge_coeff'] = [None]

        for reservoir_name, reservoir in wn._reservoirs.iteritems(): 
            self.times[reservoir]['head'] = [-1]
            self.values[reservoir]['head'] = [reservoir.head]
            self.control_names[reservoir]['head'] = [None]

    def reset_changes(self):
        self.changes_made = False
        self.objects_controlled = {(None, None) : 'control'}

    def check_for_changes(self, t):
        for obj, attr in self.objects_controlled:
            control_name = self.objects_controlled[(obj, attr)]
            if obj == None:
                continue
            new_value = getattr(obj, attr)
            old_value = self.values[obj][attr][-1]
            if new_value != old_value:
                self.changes_made = True
                self.values[obj][attr].append(new_value)
                self.times[obj][attr].append(t)
                self.control_names[obj][attr].append(control_name)
                self.objects_changed.add((obj, attr))
        return self.changes_made, self.objects_changed

    def add(self, t, obj, attr, value, control_name):
        """
        Each time a control is fired, this method should be called in order to track the change.

        Parameters
        ----------
        t : int
            time of the change
        obj : object being modified
        attr : attribute being modified
        value : new value of the attribute
        control_name : name of control modifying an object
        """

        self.objects_controlled[(obj, attr)] = control_name

        
 
    def get_log(self):
        times = []
        for obj_name, time_dict in self.times.iteritems():
            for attr, time_list in time_dict.iteritems():
                time_list.pop(0)
                times = times + time_list
                self.values[obj_name][attr].pop(0)
                self.control_names[obj_name][attr].pop(0)
        times = list(set(times))
        times.sort()
        log = pandas.DataFrame(index)
