

import itertools
from random import choice

class Creature:

    __id_iter__ = itertools.count()
    def __init__(self, team: bool, a = None, b = None, c = None):
        self.team = team
        self.group = team
        self.genes = {'a': a, 'b': b, 'c': c}
        self.id = next(Creature.__id_iter__)
        self.age = 0

    def breed(self, other):
        offspring = Creature(self.team)
        for ii in self.genes:
            if self.genes[ii] != None and other.genes[ii] == None:
                offspring.genes[ii] = self.genes[ii]
            elif self.genes[ii] == None and other.genes[ii] != None:
                offspring.genes[ii] = other.genes[ii]
            elif self.genes[ii] != None and other.genes[ii] != None:
                offspring.genes[ii] = choice([self.genes[ii], other.genes[ii]])
        numGenes = {True: 0, False: 0}
        for ii in offspring.genes:
            if offspring.genes[ii] != None:
                numGenes[offspring.genes[ii]] += 1
        offspring.team = self.team if numGenes[True] == numGenes[False] else \
            numGenes[True] > numGenes[False]
        offspring.group = self.group
        print(f'new creature: {offspring.id}')

        return offspring

    def print(self):
        print(f'creature id: {self.id}\nteam: {self.team}\ngenes: \
            {self.genes}\ngroup: {self.group}\nage: {self.age}\n')

    def move(self):
        self.group = not self.group