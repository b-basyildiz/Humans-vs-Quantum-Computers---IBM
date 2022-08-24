from ai import AI, draw_graph
import matplotlib.pyplot as plt
from gameTest import Creature
from random import choice
from time import perf_counter
import networkx as nx


t = perf_counter()
creatureNum = 4
tf = [True, False]
creatures = [Creature(choice(tf), choice(tf), choice(tf), choice(tf))\
     for ii in range(creatureNum)]

ai = AI(creatures)
colors = ['b' for node in ai.graph.nodes()]
pos = nx.spring_layout(ai.graph)
print(ai.graph.nodes)
draw_graph(ai.graph, colors, pos)
plt.show()
print(AI.optimizeBruteForce(ai.graph))
print(f'Total time: {perf_counter()-t}')