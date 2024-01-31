
import math
from tkinter import END, Canvas, Event, Label, StringVar, Text, ttk
import tkinter as tk
import numpy as np
import threading
import time
import os
from numba import jit
from numba.core.errors import NumbaWarning
import warnings

warnings.simplefilter('ignore', category=NumbaWarning)

'''
This file implements Particle Life using tkInter. Note that this program is quite slow. You can change the attraction matrix using attractionMatrix.txt
'''

CANVAS_W = 500
SEED_DIGITS = 9
GROUPS = 4
PARTICLES_PER_GROUP = 30
INDICES_ARR = np.indices((GROUPS,PARTICLES_PER_GROUP), dtype=np.int16)
MAX_FRAMERATE = 12
PARTICLE_COLORS = [(255,0,0),(0,255,0),(0,0,255)]
rMin = None
rMax = None
listOfOvals: list[list[int]] = []
attractionMat  = []
btnsList = []
canvas: Canvas = None
paused = True
playThead: threading.Thread = None

class Particle():
  listOfParticles: list[list['Particle']] = []
  seed = 0
  
  def __init__(self, gNum):
    if(gNum<len(PARTICLE_COLORS)):
      self.color = PARTICLE_COLORS[gNum]
    else:
      np.random.seed(gNum + Particle.seed)
      self.color = tuple(((np.random.random(3) * 220)+25).astype(np.uint8))
    np.random.seed((gNum * PARTICLES_PER_GROUP) + len(Particle.listOfParticles[-1]) + Particle.seed)
    self.curX = np.random.random() * CANVAS_W
    np.random.seed((gNum * PARTICLES_PER_GROUP) + len(Particle.listOfParticles[-1]) + Particle.seed + (PARTICLES_PER_GROUP * GROUPS))
    self.curY = np.random.random() * CANVAS_W
    self.nextX = self.curX
    self.nextY = self.curY
    Particle.listOfParticles[-1].append(self)

  def getColor(self):
    return self.color

  @staticmethod
  def setSeed(seed):
    Particle.seed = seed

  def getCurPos(self):
    return (self.curX, self.curY)

  def getXDis(self, x):
    '''return distance to x'''
    if abs(x - self.curX) < CANVAS_W/2:
      return x - self.curX
    else:
      return ((x+CANVAS_W/2)%CANVAS_W) - ((self.curX+CANVAS_W/2)%CANVAS_W)
  
  def getYDis(self, y):
    '''return distance to y'''
    if abs(y - self.curY) < CANVAS_W/2:
      return y - self.curY
    else:
      return ((y+CANVAS_W/2)%CANVAS_W) - ((self.curY+CANVAS_W/2)%CANVAS_W)
  
  def getDis(self, par: 'Particle'):
    parPos = par.getCurPos()
    return np.sqrt((self.getXDis(parPos[0])**2) + (self.getYDis(parPos[1])**2))
  
  def addToNextPos(self, dx, dy):
    self.nextX += dx
    self.nextY += dy
    self.nextX = self.nextX % CANVAS_W
    self.nextY = self.nextY % CANVAS_W

  def move(self):
    self.curX = self.nextX
    self.curY = self.nextY
    return (self.curX, self.curY)

def initParticles():
  Particle.listOfParticles = []
  for g in range(GROUPS):
    Particle.listOfParticles.append([])
    for p in range(PARTICLES_PER_GROUP):
      Particle(g)

def initAttractionMat():
  global attractionMat

  with open(os.path.dirname(os.path.realpath(__file__)) + "/attractionMatrix.txt","r") as file:
    attractionMat = np.loadtxt(file, np.float16)
  if (len(attractionMat) < GROUPS) or (len(attractionMat[0]) < GROUPS):
    print(f"The attraction matrix should have {GROUPS} minimum rows and {GROUPS} minimum columns")
    os.abort()
  print("attraction matrix:\n", attractionMat)

def displayWindow():
  global canvas
  global btnsList

  root = tk.Tk()
  root.title("Particle Life")

  s = ttk.Style()
  s.configure('My.TFrame', background='dark gray')

  frm = ttk.Frame(root, style='My.TFrame')
  frm.grid(padx=10, pady=10)

  rMinLabel = ttk.Label(frm, text="r min:", background='dark gray')
  rMinLabel.grid(column=0, row=1, sticky="sw")
  rMinVal = StringVar(frm)
  rMinVal.set("10")
  rMinW = ttk.Entry(frm, textvariable=rMinVal)
  rMinW.grid(column=0, row=2, sticky="nw")

  rMaxLabel = ttk.Label(frm, text=f"r max (less than {CANVAS_W}):", background='dark gray')
  rMaxLabel.grid(column=0, row=3, sticky="sw")
  rMaxVal = StringVar(frm)
  rMaxVal.set("200")
  rMaxW = ttk.Entry(frm, textvariable=rMaxVal)
  rMaxW.grid(column=0, row=4, sticky="nw")

  vcmdForSeed = frm.register(seedValidator)
  seedLabel = ttk.Label(frm, text="Seed:", background='dark gray')
  seedLabel.grid(column=0, row=5, sticky="sw")
  seedText = StringVar(frm)
  seedText.set("0")
  seedEntry = ttk.Entry(frm, validate='key' , validatecommand =(vcmdForSeed,"%P"), textvariable=seedText)
  seedEntry.grid(column=0, row=6, sticky="nw")

  completeSettingBtn = ttk.Button(frm, text="set", command=None)
  completeSettingBtn.grid(column=0, row=7)

  mousePosW = ttk.Label(frm, text="Mouse Pos: ? ?", background='dark gray')
  mousePosW.grid(column=1, row=0, columnspan=3, sticky="w", padx=20)

  canvas = tk.Canvas(frm, borderwidth=0, highlightthickness=0, height=CANVAS_W, width=CANVAS_W, background="black")
  canvas.grid(column=1, row=1, columnspan=3, rowspan=6, padx=(10,10))
  canvas.bind('<Motion>', lambda e: getMousePos(e, mousePosW))
  initCanvas()

  playPauseBtn =  ttk.Button(frm, text="Play/Pause", command=setPlay)
  playPauseBtn.grid(column=1, row=7, pady=10)
  playPauseBtn["state"] = "disabled"

  nextFrameBtn = ttk.Button(frm, text="Next Frame",
                            command=lambda: threading.Thread(target=nextFrame).start() if paused else None)
  nextFrameBtn.grid(column=2, row=7, pady=10)
  nextFrameBtn["state"] = "disabled"
  
  resetBtn = ttk.Button(frm, text="Reset", command=lambda: threading.Thread(target=reset).start())
  resetBtn.grid(column=3, row=7, pady=10)
  resetBtn["state"] = "disabled"

  btnsList = [rMinW, rMaxW, seedEntry, completeSettingBtn, playPauseBtn, nextFrameBtn, resetBtn]
  completeSettingBtn.config(command=lambda: settingComplete(rMinVal.get(), rMaxVal.get()))

  root.protocol("WM_DELETE_WINDOW",os.abort)
  root.configure(background='dark gray')
  root.mainloop()

def getMousePos(event: Event, mousePosW: tk.Label):
  mousePosW.config(text="Mouse Pos: {} {}".format(event.x, event.y))

def initCanvas():
  global listOfOvals
  canvas.delete("all")
  listOfOvals = []
  for g in range(GROUPS):
    listOfOvals.append([])
    for p in range(PARTICLES_PER_GROUP):
      par = Particle.listOfParticles[g][p]
      listOfOvals[-1].append(canvas.create_oval(par.curX-3, par.curY-3, par.curX+3, par.curY+3, fill="#%02x%02x%02x" % par.color))

def seedValidator(P):
  
  if P == "":
    P = "0"
  if str.isdigit(P) and len(P) < SEED_DIGITS:
    Particle.setSeed(int(P))
    initParticles()
    initCanvas()
    return True
  else:
    return False

def settingComplete(r1: str, r2: str):
  global rMin
  global rMax

  try:
    rMin = int(r1)
    rMax = int(r2)
  except:
    print("Please check your r values")
    return None

  if(rMax>=CANVAS_W):
    print(f"I would recommend to have Rmax significantly lesser than {CANVAS_W}")

  for btn in btnsList[:4]:  
    btn["state"] = "disabled"
  for btn in btnsList[4:]:
    btn["state"] = "enabled"

@jit(parallel=True,nopython=False)
def setParticlesNextPos():
  for g in range(GROUPS):
    for p in range(PARTICLES_PER_GROUP):
      setParticleNextPos(g,p)

@jit(parallel=True,nopython=False)
def setParticleNextPos(gPos: int, pPos: int):
  parList = Particle.listOfParticles
  first = True
  for g2 in range(gPos, GROUPS):
    for p2 in range(pPos, PARTICLES_PER_GROUP):
      if(first):
        first = False
        continue
      dis = parList[gPos][pPos].getDis(parList[g2][p2])
      attractionForce = 0
      attractionForce2 = 0
      if dis < rMin:
        attractionForce = (dis/rMin)-1
        attractionForce2 = (dis/rMin)-1
      elif dis > rMin and dis < rMax:
        #see https://www.desmos.com/calculator/t7ru0tqhmn to understand
        attractionForce = (1 - (abs((2*dis)-rMax-rMin)/(rMax-rMin))) * attractionMat[gPos][g2]
        if(g2 == gPos):
          attractionForce2 = attractionForce
        else:
          attractionForce2 = (1 - (abs((2*dis)-rMax-rMin)/(rMax-rMin))) * attractionMat[g2][gPos]
      if attractionForce != 0 or attractionForce2 != 0:
        #print(attractionForce, attractionForce2)
        dx = parList[gPos][pPos].getXDis(parList[g2][p2].curX)
        dy = parList[gPos][pPos].getYDis(parList[g2][p2].curY)
        if attractionForce != 0:
          parList[gPos][pPos].addToNextPos(
            (dx/dis) * attractionForce,
            (dy/dis) * attractionForce
          )
        if attractionForce2 != 0:
          parList[g2][p2].addToNextPos(
            -(dx/dis) * attractionForce2,
            -(dy/dis) * attractionForce2
          )

@jit(parallel=True,nopython=False)
def nextFrame():
  global canvas

  startTime = time.time()
  setParticlesNextPos()
  for g in range(GROUPS):
    for p in range(PARTICLES_PER_GROUP):
      newX, newY = Particle.listOfParticles[g][p].move()
      canvas.moveto(listOfOvals[g][p], newX-3, newY-3)
  canvas.update()
  print("Time to generate last frame:", time.time() - startTime)

def play():
  while not paused:
    nextFrame()

def setPlay():
  global paused
  global playThead

  if paused:
    print("Please wait...")
    paused = False
    playThread = threading.Thread(target=play)
    playThread.start()
  else:
    paused = True

def reset():
  global paused

  paused = True
  if(playThead != None and playThead.is_alive()):
    playThead.join()
  initParticles()
  initCanvas()
  for btn in btnsList[4:]:
    btn["state"] = "disabled"
  for btn in btnsList[:4]:
    btn["state"] = "active"

if __name__ == "__main__":
  initParticles()
  initAttractionMat()
  displayWindow()
