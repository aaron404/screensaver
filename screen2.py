#!/router/bin/python-2.7.10

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

filename = '/users/aaronhil/Pictures/screen.png'

def r(x, y, tileSize):
    return np.ix_(range(x, x+tileSize), range(y, y+tileSize))

class Controller():

    def __init__(self, w, h):
        self.w = w
        self.h = h
        
        self.screenBuffer = None
        self.canvas = None
        self.textureID = None

        self.numSteps = 0
        self.stepTime = 0
        self.numDraws = 0
        self.drawTime = 0

        self.init()

    def init(self):
        os.system('import -window root {}'.format(filename))        
        img = Image.open(filename)
        self.screenBuffer = np.array(list(img.getdata()), np.uint8)
        self.canvas = self.screenBuffer.reshape((self.h, self.w, 3))
        
        print "width:  {}".format(self.w)
        print "height: {}".format(self.h)
        print "size:   {}".format(self.screenBuffer.shape)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
        self.textureID = glGenTextures(1)

    def quit(self):
        print "average draw time: {}".format(1000 * self.drawTime / self.numDraws)
        print "average step time: {}".format(1000 * self.stepTime / self.numSteps)


    def step(self):
        global tileSize
        t0 = time.time()
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
                     GL_UNSIGNED_BYTE, 
                     self.screenBuffer)

        glScalef(0.5, -0.5, 1.0)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);             glVertex2i(0, 0)
        glTexCoord2f(self.w, 0);        glVertex2i(self.w, 0)
        glTexCoord2f(self.w, self.h);   glVertex2i(self.w, self.h)
        glTexCoord2f(0, self.h);        glVertex2i(0, self.h)
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
    if key == 'q':
        controller.quit()
        exit()

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
