#from gameTest import Creature
from creature import *
import matplotlib.pyplot as plt
import matplotlib.axes as axes
import numpy as np
import networkx as nx
from random import choice

from qiskit import QuantumRegister, ClassicalRegister, \
    QuantumCircuit, execute, Aer, IBMQ
from qiskit.compiler import transpile, assemble
from qiskit_optimization.applications import Maxcut, Tsp
from qiskit.algorithms import VQE
from qiskit.tools.jupyter import *
from qiskit.visualization import *
from ibm_quantum_widgets import *
from qiskit.tools.visualization import circuit_drawer
from qiskit.utils import algorithm_globals, QuantumInstance
from qiskit.algorithms.optimizers import SPSA
from qiskit.circuit.library import TwoLocal
from itertools import combinations




USER_TOKEN = None

varCounter = -1

class Placeholder:
    def __init__(self, id = -1):
        self.id = id
        self.team = False

class AI:
    def __init__(self, creatures):
        clauses = AI.StateToNae(creatures)
        self.clauses = []
        for clause in clauses:
            for threeClause in AI.NaeToNae3(clauses[clause]):
                self.clauses.append(threeClause)

        #print(self.clauses)
        self.vars = []
        for ii in self.clauses:
            for jj in ii:
                if jj[0] not in self.vars:
                    self.vars.append(jj[0])
        print(f'number of variables: {len(self.vars)}')
        self.graph = AI.Nae3ToGraph(self.vars, self.clauses)
        print(self.graph.nodes)


    def draw_graph(self):
        G = self.graph
        default_axes = plt.axes(frameon=True)
        nx.draw_networkx(G, node_color=['r' if (int(node[3:-1]) if node[0] != '-' else int(node[4:-1])) >= 0 else 'b' for node in G.nodes],\
             node_size = 600, alpha = 0.8, ax = default_axes, pos = nx.spring_layout(G))
        
    

        


    def StateToNae(creatures):

        clauses = {ii+kk : [] for ii in ['a','b','c'] for kk in ['True','False']}

        for creature in creatures:
            for gene in ['a', 'b', 'c']:
                if creature.genes[gene] != None:
                    clauses[gene+(str(creature.genes[gene]))] += [creature]

        return clauses


    def NaeToNae3(clause):
        global varCounter
        k = len(clause)
        if k == 0:
            return []
        if k == 1:
            return [[(clause[0], True),(clause[0], True),(clause[0], True)]]
        if k == 2:
            varCounter -= 1
            return [[(clause[0], True), (clause[1], True), (Placeholder(varCounter+1), True)],\
                [(clause[0], False), (clause[1], False), (Placeholder(varCounter+1), True)]]
        if k == 3:
            return [[(c, True) for c in clause]]

        p = [[(clause[0], True), (clause[1], True), (Placeholder(varCounter), True)]]
        for ii in range(2, k-2):
            p.append([(Placeholder(varCounter), False), (clause[ii], True), (Placeholder(varCounter - 1), True)])
            varCounter -= 1
        p.append([(Placeholder(varCounter), False), (clause[-2], True), (clause[-1], True)])
        return p
        
    def Nae3ToGraph(vars, clauses):
        m = len(clauses)
        G = nx.Graph()
        for var in vars:
            G.add_node('X_('+str(var.id)+')')
            G.add_node('-X_('+str(var.id)+')')
        for node in G.nodes:
            if node[0] != '-':
                G.add_edge(node, '-'+node, weight = 10*m)
        for clause in clauses:
            if len(clause) != 3:
                print('failed: nae clause != 3')
                return
            G.add_edge('-'*clause[0][1]+'X_('+str(clause[0][0].id)+')', '-'*clause[1][1]+'X_('+str(clause[1][0].id)+')', weight = 1)
            G.add_edge('-'*clause[0][1]+'X_('+str(clause[0][0].id)+')', '-'*clause[2][1]+'X_('+str(clause[2][0].id)+')', weight = 1)
            G.add_edge('-'*clause[1][1]+'X_('+str(clause[1][0].id)+')', '-'*clause[2][1]+'X_('+str(clause[2][0].id)+')', weight = 1)
        return G

    def bruteForce(weights):
        nodeCount = len(weights)
        bestState = []
        maxCost = 0
        for b in range(2**nodeCount):
            x = [int(t) for t in reversed(list(bin(b)[2:].zfill(nodeCount)))]
            cost = 0
            for i in range(nodeCount):
                for j in range(nodeCount):
                    cost = cost + weights[i, j] * x[i] * (1-x[j])
            if maxCost < cost:
                maxCost = cost
                bestState = x
        return bestState, maxCost

    def geneticAlgorithm():
        pass

    def solve_graph(graph):
        ''' exactly what it says '''
        # calculate all possible cuts
        sub_lists = []
        for i in range(0, len(graph.nodes())+1):
            temp = [list(x) for x in combinations(graph.nodes(), i)]
            sub_lists.extend(temp)
    
        # calculate cost of all cuts
        cut_size = 0
        bestCutSize = 0
        bestCut = sub_lists[0]
        for sub_list in sub_lists:
            cut_size = (sub_list,nx.algorithms.cuts.cut_size(graph,sub_list,weight='weight'))
            if cut_size > bestCutSize:
                bestCutSize = cut_size
                bestCut = sub_list
            
        # sort by the cost; we know this brute force approach works
        return bestCut



    def getWeights(graph):
        nodeToInt = {}
        intToNode = {}

        intCounter = 0

        for ii in graph.nodes:
            nodeToInt[ii] = intCounter
            intCounter += 1
        for ii in nodeToInt:
            intToNode[nodeToInt[ii]] = ii
        nodeCount = len(graph.nodes)
        weights = np.zeros([nodeCount, nodeCount])
        for ii in graph.nodes:
            for jj in graph.nodes:
                temp = graph.get_edge_data(ii, jj, default = 0)
                if temp != 0:
                    weights[nodeToInt[ii], nodeToInt[jj]] = temp['weight']
        return weights

    def optimizeBruteForce(graph):
        bestState, maxCost = AI.bruteForce(AI.getWeights(graph))
        return bestState, maxCost

    def anneal(graph, backend, timeSteps):
        nodeCount = len(graph.nodes)
        weights = np.zeros([nodeCount, nodeCount])

        nodeToInt = {}
        intToNode = {}

        intCounter = 0

        for ii in graph.nodes:
            nodeToInt[ii] = intCounter
            intCounter += 1
        for ii in nodeToInt:
            intToNode[nodeToInt[ii]] = ii

        print(nodeToInt)
        print(intToNode)


        for ii in graph.nodes:
            for jj in graph.nodes:
                temp = graph.get_edge_data(ii, jj, default = 0)
                if temp != 0:
                    weights[nodeToInt[ii], nodeToInt[jj]] = temp['weight']

        maxWeight = np.amax(weights)

        qReg = QuantumRegister(nodeCount)
        cReg = ClassicalRegister(nodeCount)
        circuit = QuantumCircuit(qReg, cReg)
        for ii in qReg:
            circuit.h(ii)
        for t in range(timeSteps):
            a = (t+1)/(timeSteps+1)/2
            b = 1/2-a
            for ii in qReg:
                circuit.rx(b, ii)
            for ii in range(len(qReg)):
                for jj in range(len(qReg)):
                    if weights[ii, jj]:
                        if ii != jj:
                            circuit.rzz(-a * weights[ii, jj]/maxWeight, qReg[ii], qReg[jj])
        circuit.measure(qReg, cReg)
        #circuit.draw(output='mpl', style={'backgroundcolor': '#EEEEEE'}) 

        job = execute(circuit, backend, shots = 2000)

        result = job.result()

        counts = result.get_counts(circuit)  

        best = max(counts, key=counts.get)
        best = [int(ii) for ii in best]

        cost = 0
        for i in range(nodeCount):
            for j in range(nodeCount):
                cost = cost + weights[i, j] * int(best[i]) * (1-int(best[j]))       
        return best, cost


    


    def GraphToHamiltonian():
        pass


def draw_graph(G, colors, pos):
    default_axes = plt.axes(frameon=True)
    nx.draw_networkx(G, node_color=colors,node_size=600,alpha=0.8,ax=default_axes,pos=pos)
    edge_labels = nx.get_edge_attributes(G,'weight')
    nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels, ax=default_axes)
    edge_labels = nx.get_edge_attributes(G,'weight')
    nx.draw_networkx_edge_labels(G, pos=pos, edge_labels=edge_labels, ax=default_axes)

    

if __name__ == '__main__':
    tf = [True, False]
    creatures = [Creature(choice(tf) , choice(tf) , choice(tf) , choice(tf) ) for ii in range(10)]
    ai = AI(creatures)
    colors = ['b' for node in ai.graph.nodes()]
    pos = nx.spring_layout(ai.graph)
    print(ai.graph.nodes)
    draw_graph(ai.graph, colors, pos)
    #plt.show()

    provider = IBMQ.load_account()
    backend = provider.get_backend('simulator_mps')
    #backend = Aer.get_backend("qasm_simulator")        
    nodeCount = len(ai.graph.nodes)
    weights = np.zeros([nodeCount, nodeCount])
    print('now testing quantum...')

    AI.anneal(ai.graph, backend, 4)

    nodeToInt = {}
    intToNode = {}

    intCounter = 0

    for ii in ai.graph.nodes:
        nodeToInt[ii] = intCounter
        intCounter += 1
    for ii in nodeToInt:
        intToNode[nodeToInt[ii]] = ii

    print(nodeToInt)
    print(intToNode)

    for ii in ai.graph.nodes:
        for jj in ai.graph.nodes:
            temp = ai.graph.get_edge_data(ii, jj, default = 0)
            if temp != 0:
                weights[nodeToInt[ii], nodeToInt[jj]] = temp['weight']
    
    maxCost = 0
    for b in range(2**nodeCount):
        x = [int(t) for t in reversed(list(bin(b)[2:].zfill(nodeCount)))]
        cost = 0
        for i in range(nodeCount):
            for j in range(nodeCount):
                cost = cost + weights[i, j] * x[i] * (1-x[j])
        if maxCost < cost:
            maxCost = cost
            bestState = x
        
    print(f'\nbest solution: {str(bestState) }. cost = {maxCost}')
    for ii in intToNode:
        print(f'{intToNode[ii]}: {bestState[ii]}')

    # maxCut = Maxcut(weights)
    # qp = maxCut.to_quadratic_program()
    # qubitOp, offset =  qp.to_ising()
    # tstr = str(qubitOp).split('\n')
    # gates = [ii.split(' ')[-1] for ii in tstr]
    # qReg = QuantumRegister(nodeCount)
    # cReg = ClassicalRegister(nodeCount)
    # circuit = QuantumCircuit(qReg, cReg)
    # for t in range(timeSteps):
    #     for ii in qReg:
    #         circuit.h(ii)
    #     for ii in qReg:
    #         circuit.rx(2, ii)
    # for layer in gates:
    #     qubits = []
    #     for qubit in range(len(layer)):

    #         if layer[qubit] == 'Z':
    #             qubits.append(qubit)
    #     circuit.rzz(weights[qubits[0], qubits[1]], qReg[qubits[0]], qReg[qubits[1]])
    # circuit.measure(qReg, cReg)
    # circuit.draw(output='mpl', style={'backgroundcolor': '#EEEEEE'}) 
    
    # #print(counts)
    # print('starting quantum')
    # quantum_instance = QuantumInstance(backend, seed_simulator=10598, seed_transpiler=10598)
    # spsa = SPSA(maxiter=5)
    # ry = TwoLocal(qubitOp.num_qubits, 'ry', 'cz', reps=5, entanglement='linear')
    # vqe = VQE(ry, optimizer = spsa, quantum_instance=quantum_instance)
    # result = vqe.compute_minimum_eigenvalue(qubitOp)
    # x = maxCut.sample_most_likely(result.eigenstate)
    # print('energy:', result.eigenvalue.real)
    # print('max-cut objective:', result.eigenvalue.real + offset)
    # print('solution:', x)
    # print('solution objective:', qp.objective.evaluate(x))

    plt.show()
