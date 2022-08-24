import pygame, sys
import time
import itertools
from random import choice, sample
from math import sqrt, ceil
from ai import AI
from cost_function import cost_function


pygame.init()
pygame.font.init()
font = pygame.font.Font(pygame.font.get_default_font(),32)

PLAYER_COLOR = (63+50,0+50,15+50)
COMPUTER_COLOR = (252,90,141)
FONT_COLOR = (200,200,200)
TITLE_FONT_COLOR = (235,235,220)
TITLE_BACKGROUND_COLOR = (100,200,100)
#NAMEPLATE_COLOR = (50,42,50)
NAMEPLATE_COLOR = (0,0,0)
BACKGROUND_COLOR = (100,200,100)

TICK_RATE = 200

def dist(a, b):
    return sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)


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

class Entity:
    def __init__(self, team: bool,size, group = None, posx = 0, posy = 0, genes = (None, None, None)):
        self.creature = Creature(team, a = genes[0], b = genes[1], c = genes[2])
        if group != None:
            self.creature.group = group
        self.posx = posx
        self.posy = posy
        self.lastposx = None
        self.lastposy = None
        self.size = size
        self.fill = PLAYER_COLOR if team else COMPUTER_COLOR
        aText = 'T' if genes[0] else 'N' if genes[0] == None else 'F'
        bText = 'T' if genes[1] else 'N' if genes[1] == None else 'F'
        cText = 'T' if genes[2] else 'N' if genes[2] == None else 'F'
        self.idLabel = font.render(aText+bText+cText, True, FONT_COLOR, NAMEPLATE_COLOR)
        # image credit: https://www.pngkey.com/png/full/822-8224774_cow-clipart-vector-cow-cartoon-images-transparent.png
        self.imageSprite = pygame.image.load('cow.png').convert_alpha() # dimensions 640x480 in original
        scale = 7
        self.imageDimension = (640/scale, 480/scale)
        self.imageSprite = pygame.transform.scale(self.imageSprite, self.imageDimension)
        self.imageSprite.fill(self.fill, special_flags=pygame.BLEND_ADD) # has to be duplicated, hackathon lol

    def makeFromCreature(self, creature, size, posx = 0, posy = 0):
        self.creature = creature
        self.posx = posx
        self.posy = posy
        self.size = size
        aText = 'T' if creature.genes['a'] else 'N' if creature.genes['a'] == None else 'F'
        bText = 'T' if creature.genes['b'] else 'N' if creature.genes['b'] == None else 'F'
        cText = 'T' if creature.genes['c'] else 'N' if creature.genes['c'] == None else 'F'
        self.fill = PLAYER_COLOR if creature.team else COMPUTER_COLOR
        self.idLabel = font.render(aText+bText+cText, True, (0, 255, 0), (0, 0, 255))
        self.imageSprite = pygame.image.load('cow.png').convert_alpha() # dimensions 640x480 in original
        scale = 7
        self.imageDimension = (640/scale, 480/scale)
        self.imageSprite = pygame.transform.scale(self.imageSprite, self.imageDimension)
        self.imageSprite.fill(self.fill, special_flags=pygame.BLEND_ADD) # has to be duplicated, hackathon lol

    def setPos(self, posx = 0, posy = 0):
        self.lastposx = self.posx
        self.lastposy = self.posy
        self.posx = posx
        self.posy = posy

    def getPos(self):
        return self.posx,self.posy

    def getPosRange(self):
        # solve for the line between the two positions
        inverseSpeed = 10
        # if infinite slope
        if self.posx == self.lastposx:
            print('DEBUG: no x movement, avoided "div by zero"')
            positions = [(self.lastposx,self.lastposy)]
            totalYDist = self.posy - self.lastposy
            for i in range(inverseSpeed):
                positions.append((self.lastposx, positions[-1][1]+totalYDist/inverseSpeed))
        # get length of the line, subdivide
        else:
            slope = (self.posy-self.lastposy)/(self.posx-self.lastposx)
            yIntercept = self.posy - slope*self.posx
            positions = [(self.lastposx, self.lastposy)]
            totalXDist = self.posx-self.lastposx
            for i in range(inverseSpeed):
                nextX = positions[-1][0] + totalXDist/inverseSpeed
                positions.append((nextX, slope*nextX + yIntercept))
        return positions

class Manager:
    def __init__(self, screen, screenWidth, screenHeight, maxRowSize = 5):
        self.clock = pygame.time.Clock() # variables for running the game
        self.skullAndBones = pygame.image.load('skull-and-crossbones.png') # 320x308 https://www.freeiconspng.com/images/skull-and-crossbones-png
        scale = 4
        self.skullAndBonesImageDimension = (320/scale, 308/scale)
        self.skullAndBones = pygame.transform.scale(self.skullAndBones, self.skullAndBonesImageDimension)

        self.entities = []
        self.screen = screen
        self.maxRowSize = maxRowSize
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        self.numEntities = 0
        self.entitySize = screenWidth/(2*maxRowSize) - screenWidth/30

    def addEntity(self, team, group, genes = (None, None, None)):
        self.entities.append(Entity(team, self.entitySize, group=group, genes = genes))
        self.numEntities += 1
        self.arrangeEntities()

    def addEntityFromCreature(self, creature):
        newEntity = Entity(False, 0)
        newEntity.makeFromCreature(creature, self.entitySize)
        self.entities.append(newEntity)
        self.numEntities += 1
        self.arrangeEntities()

    def drawEntities(self):

        for entity in self.entities:
            entitySurface = pygame.Surface((self.entitySize*2, self.entitySize*2))
            #entitySurface.fill((255,255,255))
            entitySurface.fill(BACKGROUND_COLOR)
            entitySurface.set_alpha(50)
            #pygame.draw.circle(entitySurface, tuple(entity.fill), (self.entitySize, self.entitySize), entity.size)
            #pygame.draw.circle(self.screen, tuple(entity.fill) if entity.creature.age > 0 else (247, 255, 0), (entity.posx, entity.posy), self.entitySize, ceil(self.entitySize/10))
            pygame.draw.circle(self.screen, tuple(entity.fill) , (entity.posx, entity.posy), self.entitySize, ceil(self.entitySize/10))


            # nameplate
            #tr = entity.idLabel.get_rect()
            #tr.center = (entity.posx, entity.posy+entity.imageDimension[1])
            pygame.draw.rect(self.screen, NAMEPLATE_COLOR, pygame.Rect(entity.posx-30, entity.posy+entity.imageDimension[1]/3*2, 60, 30))
            pygame.draw.rect(self.screen, FONT_COLOR, pygame.Rect(entity.posx-27, entity.posy+entity.imageDimension[1]/3*2+3, 54, 24))

            # fill colors for genes
            pygame.draw.rect(self.screen, PLAYER_COLOR if entity.creature.genes['a'] else FONT_COLOR if entity.creature.genes['a'] == None else COMPUTER_COLOR, 
                             pygame.Rect(entity.posx-27, entity.posy+entity.imageDimension[1]/3*2+3, 54/3,24))
            pygame.draw.rect(self.screen, PLAYER_COLOR if entity.creature.genes['b'] else FONT_COLOR if entity.creature.genes['b'] == None else COMPUTER_COLOR, 
                             pygame.Rect(entity.posx-27+54/3, entity.posy+entity.imageDimension[1]/3*2+3, 54/3,24))
            pygame.draw.rect(self.screen, PLAYER_COLOR if entity.creature.genes['c'] else FONT_COLOR if entity.creature.genes['c'] == None else COMPUTER_COLOR, 
                             pygame.Rect(entity.posx-27+54/3*2, entity.posy+entity.imageDimension[1]/3*2+3, 54/3,24))

            # borders for nameplate
            pygame.draw.rect(self.screen, NAMEPLATE_COLOR, pygame.Rect(entity.posx-27+54/3, entity.posy+entity.imageDimension[1]/3*2, 3, 30))
            pygame.draw.rect(self.screen, NAMEPLATE_COLOR, pygame.Rect(entity.posx-27+54/3*2, entity.posy+entity.imageDimension[1]/3*2, 3, 30))

            self.screen.blit(entity.imageSprite, (entity.posx-entity.imageDimension[0]/2, entity.posy-entity.imageDimension[1]/2))
            self.screen.blit(entitySurface, (entity.posx-self.entitySize,entity.posy-self.entitySize))
            #self.screen.blit(entity.idLabel, tr)
    
    def getArrangement(self):
        arrangement = []
        trueEntities = []
        falseEntities = []
        for ii in self.entities:
            if ii.creature.group:
                trueEntities.append(ii)
            else:
                falseEntities.append(ii)

        numTrue = len(trueEntities)
        numFalse = len(falseEntities)
        
        trueRows = [0]
        currentCount = 0
        currentRow = 0
        while(numTrue):
            if currentCount == 5:
                currentCount = 0
                currentRow += 1
                trueRows.append(0)
            numTrue -= 1
            currentCount += 1
            trueRows[currentRow] += 1
        falseRows = [0]
        currentCount = 0
        currentRow = 0
        while(numFalse):
            if currentCount == 5:
                currentCount = 0
                currentRow += 1
                falseRows.append(0)
            numFalse -= 1
            currentCount += 1
            falseRows[currentRow] += 1
        



        for ii in range(len(falseRows)):
            for jj in range(falseRows[ii]):
                arrangement.append([self.screenWidth/falseRows[ii]*(jj+0.5), self.screenWidth/self.maxRowSize * (ii+1/2), False])
       
        for ii in range(len(trueRows)):
            for jj in range(trueRows[ii]):
                arrangement.append([self.screenWidth/trueRows[ii]*(jj+0.5), self.screenWidth-self.screenWidth/self.maxRowSize * (ii+1/2), True])
         
        return arrangement

    def arrangeEntities(self):
        arrangement = self.getArrangement()
        newPositions = [None] * self.numEntities
        for ii in arrangement:
            minDistance = 10000000000
            best = None
            for kk in range(self.numEntities):
                if dist((self.entities[kk].posx, self.entities[kk].posy), (ii[0], ii[1])) < minDistance \
                    and newPositions[kk] == None and self.entities[kk].creature.group == ii[2]:
                    best = kk
                    minDistance = dist((self.entities[kk].posx, self.entities[kk].posy), (ii[0], ii[1]))
            newPositions[best] = ii

        for ii in range(self.numEntities):
            currPos = self.entities[ii].getPos()
            if currPos == (newPositions[ii][0], newPositions[ii][1]):
                continue
            self.entities[ii].setPos(newPositions[ii][0], newPositions[ii][1])
            # implement animation; for now, just slide cows across the screen
            posRange = self.entities[ii].getPosRange()
            for pos in posRange:
                self.entities[ii].setPos(pos[0],pos[1])
                #self.refreshScreen()
                self.drawScreen()
                self.clock.tick(TICK_RATE)

            #if currPos != (newPositions[ii][0], newPositions[ii][1]):
            #    print(currPos)
            #    print((newPositions[ii][0], newPositions[ii][1]))
            #    print('blob moved!')
            #    exit(1)

    def breed(self):
        trueEntities = []
        falseEntities = []
        for ii in self.entities:
            if ii.creature.group:
                trueEntities.append(ii)
            else:
                falseEntities.append(ii)
        trueBreeders = []
        falseBreeders = []
        if len(trueEntities) >= 2:
            trueBreeders = sample(trueEntities, 2)
        if len(falseEntities) >= 2:
            falseBreeders = sample(falseEntities, 2)
        if trueBreeders:
            # do breeding animation
            self.animateBreed(True, trueBreeders[0], trueBreeders[1])
            self.addEntityFromCreature(Creature.breed(trueBreeders[0].creature, \
                trueBreeders[1].creature))
        if falseBreeders:
            self.animateBreed(False, falseBreeders[0], falseBreeders[1])
            self.addEntityFromCreature(Creature.breed(falseBreeders[0].creature, \
                falseBreeders[1].creature))
        self.arrangeEntities()

    def animateBreed(self, group, creature1, creature2):
        print(creature1, creature2)
        for i,creature in enumerate([creature1, creature2]):
            destx = 300 + i*50
            if group:
                desty = 360
            else:
                desty = 240
            #desty = 460 if group else 440
            creature.setPos(destx, desty)
            posRange = creature.getPosRange()
            for pos in posRange:
                creature.setPos(pos[0],pos[1])
                self.drawScreen()
                self.clock.tick(TICK_RATE)
        time.sleep(2)

    def kill(self):
        trueEntities = []
        falseEntities = []
        for ii in range(len(self.entities)):
            if self.entities[ii].creature.group:
                trueEntities.append(ii)
            else:
                falseEntities.append(ii)
        trueWeightedElements = []
        falseWeightedElements = []
        for ii in trueEntities:
            trueWeightedElements.extend([ii]*(self.entities[ii].creature.age))
        for ii in falseEntities:
            falseWeightedElements.extend([ii]*(self.entities[ii].creature.age))
        tInd = None
        if trueWeightedElements: 
            ind = choice(trueWeightedElements)
            tInd = ind
            print(self.entities[ind].fill)
            #self.entities[ind].fill[1] = 255
            print(self.entities[ind].fill)
            #self.refreshScreen()

            self.drawImage(self.skullAndBones, (self.entities[ind].posx-self.skullAndBonesImageDimension[0]/2, self.entities[ind].posy-self.skullAndBonesImageDimension[0]/2))

            time.sleep(2)

            #self.clock.tick(600)
            print(f'killed true creature: {self.entities[ind].creature.id}\nGroup: \
                {self.entities[ind].creature.group}\nteam: {self.entities[ind].creature.team}')
            del self.entities[ind]
            self.numEntities -= 1


        if falseWeightedElements:
            ind = choice(falseWeightedElements)
            if tInd != None and ind > tInd:
                ind -= 1
            #self.entities[ind].fill[1] = 255
            #self.refreshScreen()

            self.drawImage(self.skullAndBones, (self.entities[ind].posx-self.skullAndBonesImageDimension[0]/2, self.entities[ind].posy-self.skullAndBonesImageDimension[0]/2))
            time.sleep(2)
            #self.clock.tick(600)
            print(f'killed false creature: {self.entities[ind].creature.id}\nGroup: \
                {self.entities[ind].creature.group}\nteam: {self.entities[ind].creature.team}')

            del self.entities[ind]
            self.numEntities -= 1
    
    def age(self):
        for ii in self.entities:
            ii.creature.age += 1
            ii.fill = [kk - 10 * ii.creature.age \
                if kk - 10 * ii.creature.age >= 0 else 0 \
                    for kk in ii.fill]
            print(ii.fill)

    def refreshScreen(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.arrangeEntities()
        self.drawEntities()
        pygame.display.flip()

    def drawScreen(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.drawEntities()
        pygame.display.flip()       

    def drawImage(self, image, pos):
        self.screen.fill(BACKGROUND_COLOR)
        self.drawEntities()
        self.screen.blit(image, pos)#(self.entities[ind].posx, self.entities[ind].posy))
        pygame.display.flip()   

    def getMove(self):
        creatures = [entity.creature for entity in self.entities]
        ai = AI(creatures)

        nodeToInt = {}
        intToNode = {}
        intCounter = 0

        for ii in ai.graph.nodes:
            nodeToInt[ii] = intCounter
            intCounter += 1
        for ii in nodeToInt:
            intToNode[nodeToInt[ii]] = ii
        optimalState, optimalScore = AI.optimizeBruteForce(ai.graph)


        currentState = [int(creature.group) for creature in creatures]
        orderedOptimalState = []
        botIndices = []
        for creature in creatures:
            orderedOptimalState.append(optimalState[nodeToInt['X_('+str(creature.id)+')']])
        for ii in range(len(creatures)):
            if not creatures[ii].team:
                botIndices.append(ii)
        newState = cost_function(currentState, orderedOptimalState, botIndices)
        print('Current State:',currentState, 'New State:', newState)
        for ii in range(len(newState)):
            if newState[ii] != currentState[ii]:
                return creatures[ii]
        print('something went wrong in getMove')
        return None






def main():

    screenWidth = 600
    screenHeight = 900

    #pygame.init()
    screen = pygame.display.set_mode((screenWidth, screenHeight))

    manager = Manager(screen, screenWidth, screenHeight)

    manager.addEntity(True, group=True, genes = (True, True, True))
    manager.addEntity(True, group=True, genes = (True, True, None))
    #manager.addEntity(True, group=True, genes = (True, True, None))
    #manager.addEntity(True, group=True, genes = (True, None, None))
    #manager.addEntity(True, group=True, genes = (True, None, None))
    manager.addEntity(False, group=False, genes = (False, False, False))
    manager.addEntity(False, group=False, genes = (False, False, None))
    #manager.addEntity(False, group=False, genes = (False, False, None))
    #manager.addEntity(False, group=False, genes = (False, None, None))
    #manager.addEntity(False, group=False, genes = (False, None, None))
    manager.age()



    maxRowSize = 10
    blobGap = screenWidth/60

    blobWidth = screenWidth/maxRowSize - (2*blobGap)






    clicked = None
    activeCreature = None
    currentTurn = True
    moveCounter = False

    while(True):

        manager.clock.tick(3) 

        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()


            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for ii in manager.entities:
                    if sqrt((ii.posx-pos[0])**2+(ii.posy-pos[1])**2) < blobWidth/2+blobGap:
                        clicked = ii

            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                for ii in manager.entities:
                    if sqrt((ii.posx-pos[0])**2+(ii.posy-pos[1])**2) < blobWidth/2+blobGap:
                        if ii == clicked:
                            print(clicked.creature.team)
                            if ii.creature.team == currentTurn:
                                ii.creature.move()
                                manager.refreshScreen()
                                time.sleep(2)
                                currentTurn = not currentTurn
                                if not currentTurn:
                                    print('Bot is Thinking')
                                    manager.getMove().move()
                                    manager.refreshScreen()
                                    time.sleep(2)
                                    currentTurn = not currentTurn
                                    moveCounter = not moveCounter
                                if moveCounter:
                                    manager.age()
                                    manager.breed()
                                    manager.kill()
                                moveCounter = not moveCounter
                clicked = None


        manager.refreshScreen()
        #for ii in range(len(trueArrangement)):
        #    pygame.draw.circle(screen, (0, 0, 255), (trueArrangement[ii][0], trueArrangement[ii][1]), blobWidth/2)
        #   pygame.draw.circle(screen, (255, 0, 0), (falseArrangement[ii][0], falseArrangement[ii][1]), blobWidth/2)
        pygame.display.flip()


    c1 = Creature(False, a = False)
    c2 = Creature(False)
    c3 = Creature(True, a = True, b = True)
    c4 = Creature(True)
    
    babies = [Creature.breed(c1, c3) for ii in range(5)]
    for ii in babies:
        ii.print()


if __name__ == '__main__':
    main()
