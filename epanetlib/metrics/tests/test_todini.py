from nose.tools import *
from os.path import abspath, dirname, join
import numpy as np
import matplotlib.pyplot as plt

import sys
sys.path.append('C:\kaklise\EPA-Resilience\Evaluation Tool')
import epanetlib as en

testdir = dirname(abspath(str(__file__)))
datadir = join(testdir,'..','..','..','networks')

def test_Todini_Fig2_optCost_GPM():
    enData = en.pyepanet.ENepanet()
    enData.inpfile = join(datadir,'Todini_Fig2_optCost_GPM.inp') 
    enData.ENopen(enData.inpfile,'tmp.rpt')
    
    G = en.network.epanet_to_MultiDiGraph(enData)
    
    # Run base hydarulic simulation and save data
    enData.ENopenH()
    G = en.sim.eps_hydraulic(enData, G)

    # Compute todini index
    todini = en.metrics.todini(G, 30) # h* = 30 m
    
    print 'Todini: Fig2_optCost'
    print todini[0]
    
    expected = 0.22
    error = abs((todini[0] - expected)/expected)
    assert_less(error, 0.1) # 10% error

def test_Todini_Fig2_optCost_CMH():
    enData = en.pyepanet.ENepanet()
    enData.inpfile = join(datadir,'Todini_Fig2_optCost_CMH.inp') 
    enData.ENopen(enData.inpfile,'tmp.rpt')
    
    G = en.network.epanet_to_MultiDiGraph(enData)
    
    # Run base hydarulic simulation and save data
    enData.ENopenH()
    G = en.sim.eps_hydraulic(enData, G)

    # Compute todini index
    todini = en.metrics.todini(G, 30) # h* = 30 m
    
    print 'Todini: Fig2_optCost'
    print todini[0]
    
    expected = 0.22
    error = abs((todini[0] - expected)/expected)
    assert_less(error, 0.1) # 10% error
    
def test_Todini_Fig2_solA_GPM():
    enData = en.pyepanet.ENepanet()
    enData.inpfile = join(datadir,'Todini_Fig2_solA_GPM.inp') 
    enData.ENopen(enData.inpfile,'tmp.rpt')
    
    G = en.network.epanet_to_MultiDiGraph(enData)
    
    # Run base hydarulic simulation and save data
    enData.ENopenH()
    G = en.sim.eps_hydraulic(enData, G)

    # Compute todini index
    todini = en.metrics.todini(G, 30)
    plt.figure()
    plt.title('Todini Index')
    plt.plot(np.array(G.graph['time'])/3600, todini, 'b.-')
    
    print 'Todini: Fig2_solA'
    print todini[0]
    
    expected = 0.41
    error = abs((todini[0] - expected)/expected)
    assert_less(error, 0.1) # 10% error

def test_Todini_Fig2_solA_CMH():
    enData = en.pyepanet.ENepanet()
    enData.inpfile = join(datadir,'Todini_Fig2_solA_CMH.inp') 
    enData.ENopen(enData.inpfile,'tmp.rpt')
    
    G = en.network.epanet_to_MultiDiGraph(enData)
    
    # Run base hydarulic simulation and save data
    enData.ENopenH()
    G = en.sim.eps_hydraulic(enData, G)

    # Compute todini index
    todini = en.metrics.todini(G, 30)
    plt.figure()
    plt.title('Todini Index')
    plt.plot(np.array(G.graph['time'])/3600, todini, 'b.-')
    
    print 'Todini: Fig2_solA'
    print todini[0]
    
    expected = 0.41
    error = abs((todini[0] - expected)/expected)
    assert_less(error, 0.1) # 10% error
    
def test_BWSN_Network_2():
    enData = en.pyepanet.ENepanet()
    enData.inpfile = join(datadir,'BWSN_Network_2.inp') 
    enData.ENopen(enData.inpfile,'tmp.rpt')
    
    # change duration to 51 hours
    enData.ENsettimeparam(en.pyepanet.EN_DURATION, 51*3600) 
    
    G = en.network.epanet_to_MultiDiGraph(enData)
    
    # Run base hydarulic simulation and save data
    enData.ENopenH()
    G = en.sim.eps_hydraulic(enData, G)

    # Compute todini index
    todini = en.metrics.todini(G, 21.1)
    plt.figure()
    plt.title('Todini Index')
    plt.plot(np.array(G.graph['time'])/3600, todini, 'b.-')
    
    todini = np.array(todini)
    Tave = np.mean(todini)
    Tmax = max(todini)
    Tmin = min(todini)
    
    print 'Todini: BWSN_Network_2'
    print "  average index: " + str(Tave)
    print "  max index: " + str(Tmax)
    print "  min index: " + str(Tmin)
    
    expected_Taverage = 0.836
    error = abs((Tave - expected_Taverage)/expected_Taverage)
    assert_less(error, 0.1) # 10% error
    
    expected_Tmax = 0.930
    error = abs((Tmax - expected_Tmax)/expected_Tmax)
    assert_less(error, 0.1) # 10% error
    
    expected_Tmin = 0.644
    error = abs((Tmin - expected_Tmin)/expected_Tmin)
    assert_less(error, 0.1) # 10% error

def test_Net6():
    enData = en.pyepanet.ENepanet()
    enData.inpfile = join(datadir,'Net6.inp') 
    enData.ENopen(enData.inpfile,'tmp.rpt')
    
    # change duration to 48 hours
    enData.ENsettimeparam(en.pyepanet.EN_DURATION, 48*3600) 
    
    G = en.network.epanet_to_MultiDiGraph(enData)
    
    # Run base hydarulic simulation and save data
    enData.ENopenH()
    G = en.sim.eps_hydraulic(enData, G)

    # Compute todini index
    todini = en.metrics.todini(G, 21.1)
    plt.figure()
    plt.title('Todini Index')
    plt.plot(np.array(G.graph['time'])/3600, todini, 'b.-')
    
    todini = np.array(todini)
    Tave = np.mean(todini)
    Tmax = max(todini)
    Tmin = min(todini)
    
    print 'Todini: Net6'
    print "  average index: " + str(Tave)
    print "  max index: " + str(Tmax)
    print "  min index: " + str(Tmin)
    
    expected_Taverage = 0.267
    error = abs((Tave - expected_Taverage)/expected_Taverage)
    assert_less(error, 0.1) # 10% error
    
    expected_Tmax = 0.547
    error = abs((Tmax - expected_Tmax)/expected_Tmax)
    assert_less(error, 0.1) # 10% error
    
    expected_Tmin = 0.075
    error = abs((Tmin - expected_Tmin)/expected_Tmin)
    assert_less(error, 0.1) # 10% error
    
if __name__ == '__main__':
    test_Net6()