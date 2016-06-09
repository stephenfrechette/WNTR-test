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
        self.objects = {}  # {obj_name: obj}
        self.times = {}  # {obj_name: {attr: [list_of_times_in_seconds]}}
        self.values = {}  # {obj_name: {attr: [list_of_values]}}
        self.control_names = {}  # {obj_name: {attr: [list_of_control_names]}}
        self.changes_made = 0
        #self.objects_changes = set()

        
        for link_name, link in wn._links.iteritems():
            self.objects[link_name + '_link'] = link
            self.times[link_name + '_link'] = {}
            self.values[link_name + '_link'] = {}
            self.control_names[link_name + '_link'] = {}

            self.times[link_name + '_link']['status'] = [-1]
            self.values[link_name + '_link']['status'] = [link.status]
            self.control_names[link_name + '_link']['status'] = [None]

            self.times[link_name + '_link']['_status'] = [-1]
            self.values[link_name + '_link']['_status'] = [link._status]
            self.control_names[link_name + '_link']['_status'] = [None]

        for pipe_name, pipe in wn._pipes.iteritems():
            self.times[pipe_name + '_link']['roughness'] = [-1]
            self.values[pipe_name + '_link']['roughness'] = [pipe.roughness]
            self.control_names[pipe_name + '_link']['roughness'] = [None]

        for pump_name, pump in wn._pumps.iteritems():
            self.times[pump_name + '_link']['speed'] = [-1]
            self.values[pump_name + '_link']['speed'] = [pump.speed]
            self.control_names[pump_name + '_link']['speed'] = [None]

            self.times[pump_name + '_link']['power'] = [-1]
            self.values[pump_name + '_link']['power'] = [pump.power]
            self.control_names[pump_name + '_link']['power'] = [None]

        for node_name, node in wn._nodes.iteritems():
            self.objects[node_name + '_node'] = node
            self.times[node_name + '_node'] = {}
            self.values[node_name + '_node'] = {}
            self.control_names[node_name + '_node'] = {}

        for junction_name, junction in wn._junctions.iteritems():
            self.times[junction_name + '_node']['leak_status'] = [-1]
            self.values[junction_name + '_node']['leak_status'] = [junction.leak_status]
            self.control_names[junction_name + '_node']['leak_status'] = [None]

            self.times[junction_name + '_node']['leak_area'] = [-1]
            self.values[junction_name + '_node']['leak_area'] = [junction.leak_area]
            self.control_names[junction_name + '_node']['leak_area'] = [None]

            self.times[junction_name + '_node']['leak_discharge_coeff'] = [-1]
            self.values[junction_name + '_node']['leak_discharge_coeff'] = [junction.leak_discharge_coeff]
            self.control_names[junction_name + '_node']['leak_discharge_coeff'] = [None]

        for tank_name, tank in wn._tanks.iteritems():
            self.times[tank_name + '_node']['leak_status'] = [-1]
            self.values[tank_name + '_node']['leak_satatus'] = [tank.leak_status]
            self.control_names[tank_name + '_node']['leak_status'] = [None]

            self.times[tank_name + '_node']['leak_area'] = [-1]
            self.values[tank_name + '_node']['leak_area'] = [tank.leak_area]
            self.control_names[tank_name + '_node']['leak_area'] = [None]

            self.times[tank_name + '_node']['leak_discharge_coeff'] = [-1]
            self.values[tank_name + '_node']['leak_discharge_coeff'] = [tank.leak_discharge_coeff]
            self.control_names[tank_name + '_node']['leak_discharge_coeff'] = [None]

        for reservoir_name, reservoir in wn._reservoirs.iteritems(): 
            self.times[reservoir_name + '_node']['head'] = [-1]
            self.values[reservoir_name + '_node']['head'] = [reservoir.head]
            self.control_names[reservoir_name + '_node']['head'] = [None]


    def get_original_changes(self):
        return self.changes_made

    def check_for_changes(self, original_changes):

        flag = False
        if self.changes_made > original_changes:
            #print 'TRUTH'
            flag = True
            #logger.debug('setting {0} {1} to {2} because of control {3}'.format(obj_name,attr,self.values[obj_name][attr][-1], self.control_names[obj_name][attr][-1]))
        return flag

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
        """

        #print t
        #self.objects_changed.add(tuple(obj, attr))
        
        if isinstance(obj, Link):
            name = obj._link_name + '_link'
        if isinstance(obj, Node):
            name = obj._name + '_node'
        
        if t == self.times[name][attr][-1]:
            if value == self.values[name][attr][-2]:
                self.times[name][attr].pop(-1)
                self.values[name][attr].pop(-1)
                self.changes_made -= 1
                #print 'Nope'
            elif value != self.values[name][attr][-1]:
                self.values[name][attr][-1] = value
                self.control_names[name][attr][-1] = control_name
                self.changes_made += 1
                #print 'Yes'
            else:
                #print 'Yes Please'
                pass
        else:
            if value == self.values[name][attr][-1]:
                #print 'perhaps once'
                pass
            else:
                self.times[name][attr].append(t)
                self.values[name][attr].append(value)
                self.control_names[name][attr].append(control_name)
                self.changes_made += 1
                #print 'perhaps twice'
        #if t == 14298:
            #logger.info(' ')
            #logger.info('HELLO')
            #logger.info('setting {0} {1} to {2} because of control {3}'.format(name,attr,self.values[name][attr][-1], self.control_names[name][attr][-1]))
            #logger.info('HELLO')
            #logger.info(' ')

        
        

        """
        elif isinstance(obj, Node):
            if t == self.times[obj._name + '_node'][attr][-1]:
                if value == self.values[obj._name + '_node'][attr][-2]:
                    self.times[obj._name + '_node'][attr].pop(-1)
                    self.values[obj._name + '_node'][attr].pop(-1)
                else:
                    self.values[obj._name + '_node'][attr][-1] = value
                    self.control_names[obj._name + '_node'][attr][-1] = control_name
            else:
                if value == self.values[obj._name + '_node'][attr][-1]:
                    pass
                else:
                    self.times[obj._name + '_node'][attr].append(t)
                    self.values[obj._name + '_node'][attr].append(value)
                    self.control_names[obj._name + '_node'][attr].append(control_name)
                    
        """
                    
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
