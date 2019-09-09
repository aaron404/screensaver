#!/router/bin/python-2.7.10

import math
import os
import random
import subprocess
import sys
import time

import numpy as np
from PIL import Image

from OpenGL.GL      import *
from OpenGL.GLUT    import *
from OpenGL.GLU     import *

#modes
SHUFFLE = 0
DIFFUSION = 1
WOBBLE = 2



filename = os.path.join(os.path.dirname(__file__), "screen.png")



def r(x, y, tileSize):
    return np.ix_(range(x, x+tileSize), range(y, y+tileSize))

class Controller():

    def __init__(self, w, h, size=2, mode=SHUFFLE):
        self.w = w
        self.h = h
        self.size = 2
        self.mode = SHUFFLE 
        
        self.screenBuffer = None
        self.canvas = None
        self.textureID = None

        self.numSteps = 0
        self.stepTime = 0
        self.numDraws = 0
        self.drawTime = 0

        # wobble vars
        self.gridWidth = 2
        self.gridHeight = max(2, int(self.gridWidth / (self.w / self.h)))
        
        self.maxSpeed = 0.005 
        self.points = np.array([[[x, y] for x in np.linspace(0, self.w, self.gridWidth)] for y in np.linspace(0, self.h, self.gridHeight)])
        self.vertCoords = np.array([[[x, y] for x in np.linspace(0, self.w, self.gridWidth)] for y in np.linspace(0, self.h, self.gridHeight)], dtype=np.float32)
        self.imgCoords  = np.array([[[x, y] for x in np.linspace(0, self.w, self.gridWidth)] for y in np.linspace(0, self.h, self.gridHeight)], dtype=np.uint)
        
        self.velocities = np.array([[0, 0],
                                    [0, 0],
                                    [0, 0],
                                    [0, 0]], dtype = np.float32)
        
        self.init()
        self.bufferType = 0
        self.stepFunctions=[self.stepShuffle, self.stepDiffusion, self.stepWobble]

    def init(self):
        os.system('import -window root {}'.format(filename))        
        img = Image.open(filename)
        self.screenBuffer = np.array(list(img.getdata()), np.uint8)
        self.screenBufferF = self.screenBuffer.astype(np.float32) / 256.0
        self.canvas = self.screenBuffer.reshape((self.h, self.w, 3))
        self.canvasF = self.screenBufferF.reshape((self.h, self.w, 3))
        self.bufferType = [0, 1, 0][self.mode]

        print "width:  {}".format(self.w)
        print "height: {}".format(self.h)
        print "size:   {}".format(self.screenBuffer.shape)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
        self.textureID = glGenTextures(1)

        if self.mode == WOBBLE:
            #self.velocities[0][0] = 0.01
            for v in self.velocities[:1]:
                v[0] = random.random() * self.maxSpeed * 2 - self.maxSpeed
                v[1] = random.random() * self.maxSpeed * 2 - self.maxSpeed

    def quit(self):
        print "average draw time: {}".format(1000 * self.drawTime / self.numDraws)
        print "average step time: {}".format(1000 * self.stepTime / self.numSteps)

    def stepShuffle(self):

        xTiles = self.w // tileSize
        yTiles = self.h // tileSize

        x1 = random.randint(0, yTiles - 2) * tileSize
        x2 = x1 + tileSize
        y1 = random.randint(0, xTiles - 2) * tileSize
        y2 = y1 + tileSize

        window = self.canvas[r(x1, y1, tileSize)] 
        if random.randint(0, 1):
            self.canvas[r(x1, y1, tileSize)] = self.canvas[r(x1, y2, tileSize)]
            self.canvas[r(x1, y2, tileSize)] = window
        else:
            self.canvas[r(x1, y1, tileSize)] = self.canvas[r(x2, y1, tileSize)]
            self.canvas[r(x2, y1, tileSize)] = window
    
    def stepDiffusion(self):
        x = random.randint(0, self.w - 1)
        y = random.randint(0, self.h - 1)

        val = self.canvasF[y][x]
        total = np.array([0, 0, 0], dtype=np.float32)
        for i in range(-self.size, self.size + 1):
            for j in range(-self.size, self.size + 1):
                cx = (x + i) % self.w
                cy = (y + j) % self.h
                total += self.canvasF[cy][cx]
        self.canvasF[y][x] = total / ((self.size * 2 + 1) ** 2)

    def stepWobble(self):
        
        for i in range(4):
            self.points[i] += self.velocities[i]
            
            if self.points[i][0] < 0:
                self.points[i][0] *= -1
                self.velocities[i][0] = -random.random() * self.maxSpeed
            if self.points[i][1] < 0:
                self.points[i][1] *= -1
                self.velocities[i][1] = random.random() * self.maxSpeed
            if self.points[i][0] > self.w:
                self.points[i][0] -= 2 * (self.points[i][0] - self.w)
                self.velocities[i][0] = 0#random.random() * self.maxSpeed
            if self.points[i][1] > self.h:
                self.points[i][1] -= 2 * (self.points[i][1] - self.h)
                self.velocities[i][1] = 0#random.random() * self.maxSpeed


    def step(self):
        global tileSize
        t0 = time.time()

        self.stepFunctions[self.mode]()
        # self.stepShuffle()
        self.numSteps += 1
        self.stepTime += time.time() - t0

    def draw(self):
        t0 = time.time()

        glColor4f(1.0, 1.0, 1.0, 1.0)

        glViewport(0, 0, self.w, self.h)
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        gluOrtho2D(0.0, self.w, 0.0, self.h)

        glEnable(GL_TEXTURE_2D)

        glBindTexture(GL_TEXTURE_2D, self.textureID)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_BASE_LEVEL, 0)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 0)
        glTexImage2D(GL_TEXTURE_2D, 
                     0, 
                     GL_RGB, 
                     self.w, 
                     self.h, 
                     0, 
                     GL_RGB, 
                     [GL_UNSIGNED_BYTE, GL_FLOAT][self.bufferType], 
                     [self.screenBuffer, self.screenBufferF][self.bufferType])

        glScalef(0.5, -0.5, 1.0)

        glBegin(GL_QUADS)
        """
        glTexCoord2f(self.points[0][0], self.points[0][1]);     glVertex2i(0, 0)
        glTexCoord2f(self.points[1][0], self.points[1][1]);     glVertex2i(self.w, 0)
        glTexCoord2f(self.points[2][0], self.points[2][1]);     glVertex2i(self.w, self.h)
        glTexCoord2f(self.points[3][0], self.points[3][1]);     glVertex2i(0, self.h)
        """
        for y in range(self.gridHeight - 1):
            for x in range(self.gridWidth - 1):

                glTexCoord2f(self.vertCoords[y][x][0],      self.vertCoords[y][x][1]);      glVertex2i(self.imgCoords[y][x][0],     self.imgCoords[y][x][1])
                glTexCoord2f(self.vertCoords[y][x+1][0],    self.vertCoords[y][x+1][1]);    glVertex2i(self.imgCoords[y][x+1][0],   self.imgCoords[y][x+1][1])
                glTexCoord2f(self.vertCoords[y+1][x+1][0],  self.vertCoords[y+1][x+1][1]);  glVertex2i(self.imgCoords[y+1][x+1][0], self.imgCoords[y+1][x+1][1])
                glTexCoord2f(self.vertCoords[y+1][x][0],    self.vertCoords[y+1][x][1]);    glVertex2i(self.imgCoords[y+1][x][0],   self.imgCoords[y+1][x][1])
        
        glEnd()
        glFlush()
        glDisable(GL_TEXTURE_2D)
        
        self.numDraws += 1
        self.drawTime += time.time() - t0

def initFunc():
    global w, h
    glClearColor(0, 0, 0, 1)
    glColor3f(0, 0, 0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0, w, 0.0, h)
    
def keyboardFunc(key, x, y):
    global controller
    if key == 'q':
        controller.quit()
        os.remove(filename)
        exit()
    elif key == 'r':
        for i in range(controller.gridWidth):
            for j in range(controller.gridHeight):
                controller.vertCoords[i][j][0] += random.random() * 10 - 5
                controller.vertCoords[i][j][1] += random.random() * 10 - 5


def displayFunc():
    global controller
    controller.draw()

targetFPS = 10
def idleFunc():
    global controller
    drawTime = controller.drawTime / max(1, controller.numDraws)
    stepTime = controller.stepTime / max(1, controller.numSteps)
    steps = (1.0 / targetFPS - drawTime) / max(0.0000001, stepTime)
    clampedSteps = min(5000, max(1, int(steps)))
    #print drawTime, stepTime, steps, clampedSteps, clampedSteps * targetFPS
    for i in range(clampedSteps):
        controller.step()
    glutPostRedisplay()

w, h = (-1, -1)
controller = None
tileSize = 8


if __name__ == "__main__":

    if len(sys.argv) > 1:
        try:
            tileSize = int(sys.argv[1])
        except:
            exit()

    glutInit()

    w = glutGet(GLUT_SCREEN_WIDTH)
    h = glutGet(GLUT_SCREEN_HEIGHT)

    glutInitWindowSize(1, 1)
    glutInitWindowPosition(w, h)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutCreateWindow("screen")

    glutFullScreen()
    
    glutIdleFunc(idleFunc)
    glutDisplayFunc(displayFunc)
    glutKeyboardFunc(keyboardFunc)

    initFunc()
    controller = Controller(w, h)

    glutMainLoop()
