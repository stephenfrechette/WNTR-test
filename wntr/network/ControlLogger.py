import pandas


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

        for link_name, link in wn.links():
            self.objects[link.name()] = link
            self.times[link.name()] = {}
            self.values[link.name()] = {}
            self.control_names[link.name()] = {}

            self.times[link.name()]['status'] = [0]
            self.values[link.name()]['status'] = [link.status]
            self.control_names[link.name()]['status'] = [None]

            self.times[link.name()]['_status'] = [0]
            self.values[link.name()]['_status'] = [link._status]
            self.control_names[link.name()]['_status'] = [None]

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
        if obj not in self.objects:
            raise ValueError('Changes in the specified object are not supported.')
        if attr not in self.times[obj.name()]:
            raise ValueError('Changes in the specified attribute are not supported.')

        if t == self.times[obj.name()][attr][-1]:
            if value == self.values[obj.name()][attr][-2]:
                self.times[obj.name()][attr].pop(-1)
                self.values[obj.name()][attr].pop(-1)
            else:
                self.values[obj.name()][attr][-1] = value
                self.control_names[obj.name()][attr][-1] = control_name
        else:
            if value == self.values[obj.name()][attr][-1]:
                pass
            else:
                self.times[obj.name()][attr].append(t)
                self.values[obj.name()][attr].append(value)
                self.control_names[obj.name()][attr].append(control_name)

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
        log = pandas.DataFrame(index=)