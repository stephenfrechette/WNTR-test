# -*- coding: utf-8 -*-
"""
Classes and methods used for specifying controls and control actions
that may modify parameters in the network during simulation.
"""

"""
Created on Sat Sep 26 12:33 AM 2015

@author: claird
"""

import weakref
import numpy as np

class ControlAction(object):
    """ 
    A base class for deriving new control actions.
    The control action is fired by calling FireAction

    This class is not meant to be used directly. Derived classes
    must implement the FireActionImpl method.
    """
    def __init__(self):
        pass

    def FireControlAction(self):
        """ 
        This method is called to fire the corresponding control action.
        """
        self._FireControlActionImpl()

    def _FireControlActionImpl(self):
        """
        Implements the specific action that will be fired when FireAction
        is called. This method should be overridded in derived classes
        """
        raise NotImplementedError('_FireActionImpl is not implemented. '
                                  'This method must be implemented in '
                                  'derived classes of ControlAction.')

class TargetAttributeControlAction(ControlAction):
    """
    A general class for specifying an ControlAction that simply
    modifies the attribute of a target.

    Parameters
    ----------
    target_obj : object
        object that will be changed when the event is fired

    attribute : string
        the attribute that will be changed on the object when
        the event is fired

    value : any
        the new value for the attribute when the event is fired
    """
    def __init__(self, target_obj, attribute, value):
        if target_obj is None:
            raise ValueError('target_obj is None in TargetAttributeControlAction::__init__. A valid target_obj is needed.')
        if not hasattr(target_obj, attribute):
            raise ValueError('attribute given in TargetAttributeControlAction::__init__ is not valid for target_obj')

        self._target_obj_ref = weakref.ref(target_obj)
        self._attribute = attribute
        self._value = value

    def _FireControlActionImpl(self):
        """
        This is an overridden method from the ControlAction class. 
        Here, it changes the target_obj's attribute to the provided value.

        This method should not be called directly. Use FireAction of the 
        ControlAction base class instead.
        """
        target = self._target_obj_ref()
        assert target is not None, 'target is None inside TargetAttribureControlAction::_FireControlActionImpl'
        if target is not None:
            assert hasattr(target, self._attribute), 'attribute specified in TargetAttributeControlAction is not valid for targe_obj'
            setattr(target, self._attribute, value)

class Control(object):
    """
    This is the base class for all control objects.
    Control objects are used to modify a model based on current
    state in the simulation. For example, if a pump is supposed 
    to be turned on when the simulation time reaches 6 AM, or a
    pipe is supposed to be closed when a tank reaches a minimum
    height.

    From an implementation standpoint, derived Control classes
    implement a particular mechanism for monitoring state (e.g.
    checking the simulation time to see if a change should be
    made). Then, they typically call FireAction on a derived
    ControlAction class.

    New control classes (classes derived from Control) must implement
    the following methods:
       _IsControlActionRequired(self, wnm)
       _FireControlAction(self, wnm)
    """
    def __init__(self):
        pass

    def InformSuccessfulTimestep(self, wnm):
        """
        This method is called by the simulator to let the control know
        about a successful timestep. This allows the control to log
        any history information that it may need to log.

        Parameters
        ----------

        wnm : WaterNetworkModel object
            The water network model object that is being simulated
        """
        self._InformSuccessfulTimestepImpl(wnm)
        
    def _InformSuccessfulTimestepImpl(self, wnm):
        """
        This method should be overriden by derived classes from Control. 
        Please see Control::InformSuccessfulTimestep for documentation 
        information. This should not be called directly, instead 
        InformSuccessfulTimestep should be called.

        Parameters
        ----------

        wnm : WaterNetworkModel object
            The water network model object that is being simulated
        """
        raise NotImplementedError('_InformSuccessfulTimestepImpl is not implemented. '
                                  'This method must be implemented in any '
                                  ' class derived from Control.')  

    def IsControlActionRequired(self, wnm):
        """
        This method is called to see if any action is required
        by this control object. This method returns a tuple
        that indicates if action is required and a recommended
        time for the simulation to backup (in seconds as a positive
        number) before firing the control action.

        Note: The control action will actually be fired when 
        _IsActionRequiredImpl returns (True, t) with a t that is 
        lower than a simulator tolerance - indicating that
        action is required and no additional time backup is required.

        Parameters
        ----------
        wnm : WaterNetworkModel
            An instance of the current WaterNetworkModel object that
            is being simulated.
        """
        return _IsControlActionRequiredImpl(self, wnm)

    def _IsControlActionRequiredImpl(self, wnm)
        """
        This method should be implemented in derived Control classes as 
        the main implementation of IsActionRequired.

        The derived classes that override this method should return 
        a tuple that indicates if action is required and a recommended
        time for the simulation to backup before firing the control 
        action.

        This method should not be called directly. Use IsActionRequired
        instead.

        Parameters
        ----------
        wnm : WaterNetworkModel
            An instance of the current WaterNetworkModel object that
            is being simulated.
        """
        raise NotImplementedError('_IsControlActionRequiredImpl is not implemented. '
                                  'This method must be implemented in any '
                                  ' class derived from Control.')  

    def FireControlAction(self, wnm):
        """
        This method is called to fire the control action after
        a call to IsControlActionRequired indicates that an action is required.

        Note: Derived classes should not override this method, but should
        override _FireControlActionImpl instead.

        Parameters
        ----------
        wnm : WaterNetworkModel
            An instance of the current WaterNetworkModel object that
            is being simulated.
        """
        return _FireControlActionImpl(wnm)

    def _FireControlActionImpl(wnm):
        """
        This is the method that should be overridden in derived classes
        to implement the action of firing the control.

        Parameters
        ----------
        wnm : WaterNetworkModel
            An instance of the current WaterNetworkModel object that
            is being simulated.
        """
        raise NotImplementedError('_FireControlActionImpl is not implemented. '
                                  'This method must be implemented in '
                                  'derived classes of ControlAction.')


class TimeControl(Control):
    """
    A class for creating time controls to fire a control action at a
    particular time.

    Parameters
    ----------
    time_sec : float
        time (in seconds) when the events should be fired.

    time_flag : string, ('SIM_TIME', 'CLOCK_TIME')

        SIM_TIME: indicates that the value of time_sec is in seconds
            since the start of the simulation

        SHIFTED_TIME: indicates that the value of time_sec is shifted
            by the start time set for the simulation. That is,
            time_sec is in seconds since 12 AM on the first day of the
            simulation.  Therefore, 7200 refers to 2:00 AM regardless
            of the start time in the simulation.

    daily_flag : bool
        False : control will execute once when time is first encountered
        True : control will execute at the same time daily

    control_action : An object derived from ControlAction This is the
       event action that will be fired at the specified time
    """

    def __init__(self, wnm, time_sec, time_flag, daily_flag, control_action):
        self._time_sec = time_sec
        self._time_flag = time_flag
        assert time_flag == 'SIM_TIME' or time_flag == 'SHIFTED_TIME'
        self._daily_flag = daily_flag
        self._control_action = control_action
        self._control_complete = False
        self._prev_time_sec = None

        if daily_flag and time_sec > 24*3600:
            raise ValueError('In TimeControl, a daily control was requested, however, the time passed in was not between 0 and 24*3600')
        
        if time_flag == 'SIM_TIME' and self._time_sec < wnm.sim_time_sec:
            self._control_complete = True

        if time_flag == 'SHIFTED_TIME' and self._time_sec < wnm.shifted_time_sec():
            self._time_sec += 24*3600

    @classmethod
    def WithTarget(time_sec, time_flag, daily_flag, target_obj, attribute, value):
        t = TargetAttributeControlAction(target_obj, attribute, value)
        return TimeControl(time_sec, time_flag, daily_flag, t)

    def _InformSuccessfulTimestepImpl(self, wnm):
        # time controls don't need to store any history at this point
        pass
    
    def _IsControlActionRequiredImpl(self, wnm)
        """
        This implements the derived method from Control. Please see
        the Control class and the documentation for this class.
        """
        if self._control_complete:
            return (False, None)

        if self._time_flag == 'SIM_TIME':
            if self._time_sec <= wnm.sim_time_sec:
                return (True, wnm.sim_time_sec - self._time_sec)
        elif self._time_flag == 'SHIFTED_TIME':
            if self._time_sec <= wnm.shifted_time_sec():
                return (True, wnm.shifted_time_sec() - self._time_sec)

        return (False, None)

    def _FireControlActionImpl(wnm):
        """
        This implements the derived method from Control. Please see
        the Control class and the documentation for this class.
        """
        assert self._control_action is not None, '_control_action is None inside TimeControl'
        self._control_action.FireControlAction(wnm)
        if self._daily_flag:
            self._time_sec += 24*3600
        else:
            self._control_complete = True

class ConditionalControl(Control):
    """
    A class for creating conditional controls to fire a control action
    when a particular object/attribute becomes higher or lower than a 
    specified value.

    Parameters
    ----------
    source_obj : object
       The source object that contains the attribute being monitored

    source_attribute : string
       The name of the attribute being monitored

    operation : one the numpy operations listed below
       The comparison operation to be used. This must be 
       one of the numpy comparison operations, e.g.:

       greater(x1, x2[, out]) Return the truth value of (x1 > x2) element-wise.
       greater_equal(x1, x2[, out]) Return the truth value of (x1 >= x2) element-wise.
       less(x1, x2[, out]) Return the truth value of (x1 < x2) element-wise.
       less_equal(x1, x2[, out]) Return the truth value of (x1 =< x2) element-wise.

    threshold : float
       The threshold value to compare against. In this implementation, this must
       be a float.

    control_action : An object derived from ControlAction This is the
       event action that will be fired when the condition becomes true
    """

    def __init__(self, source_obj, source_attribute, operation, threshold, control_action):
        self._source_obj = source_obj
        self._source_attribute = source_attribute
        self._operation = operation
        self._threshold = threshold
        self._control_action = control_action
        self._prev_time_sec = 0
        self._prev_value = None
        if source_obj is None:
            raise ValueError('source_obj of None passed to ConditionalControlObject.')
        if not hasattr(source_obj, source_attribute):
            raise ValueError('In ConditionalControlObject, source_obj does not contain the attribute specified by source_attribute.')

    @classmethod
    def WithTarget(source_obj, source_attribute, operation, threshold, target_obj, target_attribute, target_value):
        ca = TargetAttributeControlAction(target_obj, target_attribute, target_value)
        return ConditionalControl(source_obj, source_attribute, operation, threshold, ca)

    def _InformSuccessfulTimestepImpl(self, wnm):
        # set the previous value and previous time for linear interpolation
        self._prev_time_sec = wnm.sim_time_sec
        self._prev_value = getattr(source_obj, source_attribute)

    def _IsControlActionRequiredImpl(self, wnm)
        """
        This implements the derived method from Control. Please see
        the Control class and the documentation for this class.
        """
        value = getattr(source_obj, source_attribute)
        if self._operation(value, self._threshold):
            # control action is required
            if self._prev_time_sec is None or self._prev_value is None:
                assert wnm.time_step == 0, 'This should only happen during the first simulation timestep'
                
            # let's do linear interpolation to determine the estimated switch time
            change_required = True
            m = (value - self._prev_value)/(wnm.time_sec - self._prev_time)
            new_time = (self._threshold - self._prev_value)/m + self._prev_time
            return (True, new_time)

        self._prev_time_sec = wnm.time_sec
        self._prev_value = value
        
        return (False, None)
        

    def _FireControlActionImpl(wnm):
        """
        This implements the derived method from Control. Please see
        the Control class and the documentation for this class.
        """
        assert self._control_action is not None, '_control_action is None inside TimeControl'
        self._control_action.FireControlAction(wnm)



    