from wntr.network import Link, Node, Pipe, Pump, Valve, Junction, Tank, Reservoir
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
        self._values = {}
        self.all_controls = {}
        self.changes_made = False
        self.pump_speed_changed = False
        self.objects_changed = set()
        self.objects_controlled = {}
        self.log_times = []

        
        for link_name, link in wn.links():
            self.times[link] = {}
            self.values[link] = {}
            self._values[link] = {}
            self.control_names[link] = {}

            self.times[link]['status'] = ['initial']
            self.values[link]['status'] = [link.status]
            self._values[link]['status'] = [link.status]
            self.control_names[link]['status'] = ['N/A']

            self.times[link]['_status'] = ['initial']
            self.values[link]['_status'] = [link._status]
            self._values[link]['_status'] = [link._status]
            self.control_names[link]['_status'] = ['N/A']

        for pipe_name, pipe in wn.links(Pipe):
            self.times[pipe]['roughness'] = ['initial']
            self.values[pipe]['roughness'] = [pipe.roughness]
            self._values[pipe]['roughness'] = [pipe.roughness]
            self.control_names[pipe]['roughness'] = ['N/A']

        for pump_name, pump in wn.links(Pump):
            self.times[pump]['speed'] = ['initial']
            self.values[pump]['speed'] = [pump.speed]
            self._values[pump]['speed'] = [pump.speed]
            self.control_names[pump]['speed'] = ['N/A']

            self.times[pump]['power'] = ['initial']
            self.values[pump]['power'] = [pump.power]
            self._values[pump]['power'] = [pump.power]
            self.control_names[pump]['power'] = ['N/A']

            self.times[pump]['_power_outage'] = ['initial']
            self.values[pump]['_power_outage'] = [pump._power_outage]
            self._values[pump]['_power_outage'] = [pump._power_outage]
            self.control_names[pump]['_power_outage'] = ['N/A']

        for node_name, node in wn.nodes():
            self.times[node] = {}
            self.values[node] = {}
            self._values[node] = {}
            self.control_names[node] = {}

        for junction_name, junction in wn.nodes(Junction):
            self.times[junction]['leak_status'] = ['initial']
            self.values[junction]['leak_status'] = [junction.leak_status]
            self._values[junction]['leak_status'] = [junction.leak_status]
            self.control_names[junction]['leak_status'] = ['N/A']

            self.times[junction]['leak_area'] = ['initial']
            self.values[junction]['leak_area'] = [junction.leak_area]
            self._values[junction]['leak_area'] = [junction.leak_area]
            self.control_names[junction]['leak_area'] = ['N/A']

            self.times[junction]['leak_discharge_coeff'] = ['initial']
            self.values[junction]['leak_discharge_coeff'] = [junction.leak_discharge_coeff]
            self._values[junction]['leak_discharge_coeff'] = [junction.leak_discharge_coeff]
            self.control_names[junction]['leak_discharge_coeff'] = ['N/A']

        for tank_name, tank in wn.nodes(Tank):
            self.times[tank]['leak_status'] = ['initial']
            self.values[tank]['leak_status'] = [tank.leak_status]
            self._values[tank]['leak_status'] = [tank.leak_status]
            self.control_names[tank]['leak_status'] = ['N/A']

            self.times[tank]['leak_area'] = ['initial']
            self.values[tank]['leak_area'] = [tank.leak_area]
            self._values[tank]['leak_area'] = [tank.leak_area]
            self.control_names[tank]['leak_area'] = ['N/A']

            self.times[tank]['leak_discharge_coeff'] = ['initial']
            self.values[tank]['leak_discharge_coeff'] = [tank.leak_discharge_coeff]
            self._values[tank]['leak_discharge_coeff'] = [tank.leak_discharge_coeff]
            self.control_names[tank]['leak_discharge_coeff'] = ['N/A']

        for reservoir_name, reservoir in wn.nodes(Reservoir):
            self.times[reservoir]['head'] = ['initial']
            self.values[reservoir]['head'] = [reservoir.head]
            self._values[reservoir]['head'] = [reservoir.head]
            self.control_names[reservoir]['head'] = ['N/A']

    def reset_changes(self):
        self.changes_made = False
        self.objects_controlled = {(None, None) : 'control'}
        self.pump_speed_changed = False

    def check_for_changes(self, t):
        for obj, attr in self.objects_controlled:
            control_name = self.objects_controlled[(obj, attr)]
            if obj is None:
                continue
            new_value = getattr(obj, attr)
            old_value = self._values[obj][attr][-1]
            if new_value != old_value:
                self.changes_made = True
                if attr == 'speed':
                    self.pump_speed_changed = True
                self._values[obj][attr].append(new_value)
                self.objects_changed.add((obj, attr))
                if t not in self.all_controls:
                    self.all_controls[t] = {}
                if obj not in self.all_controls[t]:
                    self.all_controls[t][obj]= {}
                self.all_controls[t][obj][attr] = (new_value, control_name)
                if t == self.times[obj][attr][-1]:
                    if len(self.values[obj][attr]) > 1:
                        if new_value == self.values[obj][attr][-2]:
                            self.times[obj][attr].pop(-1)
                            self.values[obj][attr].pop(-1)
                            self.control_names[obj][attr].pop(-1)
                    elif new_value != self.values[obj][attr][-1]:
                        self.values[obj][attr][-1] = new_value
                        self.control_names[obj][attr][-1] = control_name
                else:
                    self.times[obj][attr].append(t)
                    self.values[obj][attr].append(new_value)
                    self.control_names[obj][attr].append(control_name)
        return self.changes_made, self.objects_changed, self.pump_speed_changed

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
        
 
    def __str__(self):
        printstr = '{0:<12} {1:<12} {2:<12} {3:<12} {4:<12}\n'.format('Time','Object','Attribute','Value','Control Name')
        t_list = []
        for t in self.all_controls:
            t_list.append(t)
        t_list.sort()
        for t in t_list:
            for obj in self.all_controls[t]:
                for attr in self.all_controls[t][obj]:
                    value = self.all_controls[t][obj][attr][0]
                    control_name = self.all_controls[t][obj][attr][1]
                    obj_name = 0
                    if hasattr(obj,'_link_name'):
                        obj_name = obj._link_name
                    elif hasattr(obj,'_name'):
                        obj_name = obj._name
                    str_t = str(t)
                    value = str(value)

                    text_format = '{0:<12} {1:<12} {2:<12} {3:<12} {4:<12}\n'
                    printstr += text_format.format(str_t,obj_name,attr,value,control_name,'')

        return printstr






