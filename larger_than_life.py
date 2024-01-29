
import random
from tkinter import END, Canvas, Event, Frame, OptionMenu, StringVar, ttk
import tkinter as tk
import numpy as np
import threading
import time
import os
from PIL import ImageTk, Image
import scipy.ndimage

'''
Conway's Game of Life uses this kernel:
[1,1,1]
[1,0,1]
[1,1,1]

Larger Than Life can use custom kernels. It also uses a custom range for the survival condition and birth condition, for example, if the survival condition range is [5, 6, 7, 8] and if the birth condition is [7, 8, 9], then the a cell will be born if there are 7 to  9 neighbors alive, and a cell would survive to the next generation is 5 to 8 neighbors are alive. Keep in mind that a custom kernel is used, so the number of alive neighbors can be very high if the kernel is large.

Possible kernels:
kernel Type: "Moore" and radius 2
[1,1,1,1,1]
[1,1,1,1,1]
[1,1,0,1,1]
[1,1,1,1,1]
[1,1,1,1,1]
kernel Type: "von Neumann" and radius 3
[0,0,0,1,0,0,0]
[0,0,1,1,1,0,0]
[0,1,1,1,1,1,0]
[1,1,1,0,1,1,1]
[0,1,1,1,1,1,0]
[0,0,1,1,1,0,0]
[0,0,0,1,0,0,0]

Interesting settings:
FORMAT: [KERNEL_RADIUS], [INCLUDE_MIDDLE], [SURVIVAL_RANGE], [BIRTH_RANGE], [KERNEL_TYPE]
GameOfLife: R1, M0, S2..3,    B3..3, NM   (start with the 50/50 density)
Bugs:       R5, M1, S34..58,  B34..45, NM (start with the 25% alive)
Majority:   R4, M1, S41..81,  B41..81,NM  (start with the 50/50 density)
'''

ARR_W = 250
ARR_W_SQ = ARR_W**2
PIXEL_WIDTH = 2
CANVAS_W = ARR_W*PIXEL_WIDTH
MAX_FRAME_PER_SEC = 6
RANGE_FOR_SURVIVAL = [0, ARR_W]
RANGE_FOR_BIRTH = [0, ARR_W]
SEED_DIGITS = 9
seed = 0
aliveAdjustDenominator = 2
universeArr = None
canvas: Canvas = None
canvasThread = None
playThread = None
photoVar = None
canvasImgVar = None
kernel = None
paused = True
rRange = [1,ARR_W-1]
surRange = [-1, -1]
birthRange = [-1, -1]
btnsList = None

def initArrVal():
  global universeArr

  np.random.seed(seed)
  universeArr = np.zeros((ARR_W_SQ), dtype=np.int8)
  universeArr[np.random.choice(ARR_W_SQ, int(ARR_W_SQ/aliveAdjustDenominator), replace=False)] = 1
  universeArr = np.reshape(universeArr,( ARR_W, ARR_W))

def displayWindow():
  global canvas
  global btnsList

  root = tk.Tk()
  root.title("Larger Than Life")

  s = ttk.Style()
  s.configure('My.TFrame', background='dark gray')

  frm = ttk.Frame(root, style='My.TFrame')
  frm.grid(padx=10, pady=10)

  kernelMenuLabel = ttk.Label(frm, text="Choose kernel type:", background='dark gray')
  kernelMenuLabel.grid(column=0, row=0, sticky="sw")
  kernelChosen = StringVar(frm)
  kernelChosen.set("Moore")
  kernelMenu = OptionMenu(frm, kernelChosen, "Moore", "von Neumann", "circular")
  kernelMenu.grid(column=0, row=1, sticky="nw")

  kernelRLabel = ttk.Label(frm, text="Choose kernel radius:", background='dark gray')
  kernelRLabel.grid(column=0, row=2, sticky="sw")
  rVal = StringVar(frm)
  rVal.set("3")
  kernelR = ttk.Spinbox(frm, from_=rRange[0], to=rRange[1], textvariable=rVal)
  kernelR.grid(column=0, row=3, sticky="nw")

  mLabel = ttk.Label(frm, text="Include middle:", background='dark gray')
  mLabel.grid(column=0, row=4, sticky="sw")
  mVal = StringVar(frm)
  mVal.set("No")
  mOPtion = OptionMenu(frm, mVal, "Yes", "No")
  mOPtion.grid(column=0, row=5, sticky="nw")

  minSurLabel = ttk.Label(frm, text="Min neighbors to survive:", background='dark gray')
  minSurLabel.grid(column=0, row=6, sticky="sw")
  minSurVal = StringVar(frm)
  minSurVal.set("3")
  minSurW = ttk.Spinbox(frm, from_=RANGE_FOR_SURVIVAL[0], to=RANGE_FOR_SURVIVAL[1], textvariable=minSurVal)
  minSurW.grid(column=0, row=7, sticky="nw")

  maxSurLabel = ttk.Label(frm, text="Max neighbors to survive:", background='dark gray')
  maxSurLabel.grid(column=0, row=8, sticky="sw")
  maxSurVal = StringVar(frm)
  maxSurVal.set("3")
  maxSurW = ttk.Spinbox(frm, from_=RANGE_FOR_SURVIVAL[0], to=RANGE_FOR_SURVIVAL[1], textvariable=maxSurVal)
  maxSurW.grid(column=0, row=9, sticky="nw")

  minBirLabel = ttk.Label(frm, text="Min neighbors to be born:", background='dark gray')
  minBirLabel.grid(column=0, row=10, sticky="sw")
  minBirVal = StringVar(frm)
  minBirVal.set("3")
  minBirW = ttk.Spinbox(frm, from_=RANGE_FOR_BIRTH[0], to=RANGE_FOR_BIRTH[1], textvariable=minBirVal)
  minBirW.grid(column=0, row=11, sticky="nw")

  maxBirLabel = ttk.Label(frm, text="Max neighbors to be born:", background='dark gray')
  maxBirLabel.grid(column=0, row=12, sticky="sw")
  maxBirVal = StringVar(frm)
  maxBirVal.set("3")
  maxBirW = ttk.Spinbox(frm, from_=RANGE_FOR_BIRTH[0], to=RANGE_FOR_BIRTH[1], textvariable=maxBirVal)
  maxBirW.grid(column=0, row=13, sticky="nw")

  vcmdForSeed = frm.register(seedValidator)
  seedLabel = ttk.Label(frm, text="Seed:", background='dark gray')
  seedLabel.grid(column=0, row=14, sticky="sw")
  seedText = StringVar(frm)
  seedText.set("0")
  seedEntry = ttk.Entry(frm, validate='key' , validatecommand =(vcmdForSeed,"%P"), textvariable=seedText)
  seedEntry.grid(column=0, row=15, sticky="nw")

  aliveLabel = ttk.Label(frm, text="Denominator value for alive ratio:", background='dark gray')
  aliveLabel.grid(column=0, row=16, sticky="sw")
  aliveVal = StringVar(frm)
  aliveVal.set("2")
  aliveW = ttk.Spinbox(frm, from_=0, to=ARR_W_SQ, textvariable=aliveVal)
  aliveW.configure(command= lambda: changeAliveDenominator(aliveVal.get()))
  aliveW.bind("<KeyRelease>", lambda e: changeAliveDenominator(aliveVal.get()))
  aliveW.grid(column=0, row=17, sticky="nw")

  completeSettingBtn = ttk.Button(frm, text="set", command=None)
  completeSettingBtn.grid(column=0, row=18)

  canvas = tk.Canvas(frm, borderwidth=0, highlightthickness=0, height=CANVAS_W, width=CANVAS_W)
  canvas.grid(column=1, row=0, columnspan=3, rowspan=18, padx=(10,0))
  canvasThread.start()

  playPauseBtn =  ttk.Button(frm, text="Play/Pause", command=setPlay)
  playPauseBtn.grid(column=1, row=18, pady=10)
  playPauseBtn["state"] = "disabled"

  nextFrameBtn = ttk.Button(frm, text="Next Frame", command=nextFrame)
  nextFrameBtn.grid(column=2, row=18, pady=10)
  nextFrameBtn["state"] = "disabled"
  
  resetBtn = ttk.Button(frm, text="Reset", command=reset)
  resetBtn.grid(column=3, row=18, pady=10)
  resetBtn["state"] = "disabled"

  btnsList = [kernelMenu, kernelR, mOPtion, minSurW, maxSurW, minBirW, maxBirW, seedEntry, aliveW, completeSettingBtn, playPauseBtn, nextFrameBtn, resetBtn]
  completeSettingBtn.config(command=lambda: setkernel(kernelChosen.get(), mVal.get(), rVal.get(), minBirVal.get(), maxBirVal.get(), minSurVal.get(), maxSurVal.get(), aliveVal.get()))

  root.protocol("WM_DELETE_WINDOW",os.abort)
  root.configure(background='dark gray')
  root.mainloop()

def setCanvasThread():
  global photoVar
  global canvasImgVar

  intermediateArr = np.repeat(np.logical_not(universeArr), PIXEL_WIDTH, axis=1).reshape(ARR_W, CANVAS_W)
  largeArr = np.repeat(intermediateArr, PIXEL_WIDTH, axis=0).reshape(CANVAS_W, CANVAS_W)
  newPhoto =  ImageTk.PhotoImage(image=Image.fromarray(largeArr*255))
  if(canvasImgVar == None):
    canvasImgVar = canvas.create_image(0,0, anchor="nw", image=newPhoto)
  else:
    canvas.itemconfig(canvasImgVar, image=newPhoto)
  photoVar = newPhoto

def changeAliveDenominator(aliveVal: str):
  global aliveAdjustDenominator

  if(aliveVal == ""):
    aliveVal = 1
  fltVal = float(aliveVal)
  aliveAdjustDenominator = 1 if fltVal <= 1 else fltVal
  initArrVal()
  setCanvasThread()

def setkernel(kType: str, m: str, r: str, minb: str, maxb: str, mins: str, maxs: str, aliveVal: str):
  global kernel
  global surRange
  global birthRange

  try:
    r = int(r)
    minb = int(minb)
    maxb = int(maxb)
    mins = int(mins)
    maxs = int(maxs)
    aliveVal = float(aliveVal)
  except:
    print("Error trying to convert input values")
    return None

  if(mins > maxs):
    print("Minimum survival value is larger than maximum")
    return None
  elif(mins < RANGE_FOR_SURVIVAL[0] or maxs > RANGE_FOR_SURVIVAL[1]):
    print(f"Survival range is {RANGE_FOR_SURVIVAL[0]} - {RANGE_FOR_SURVIVAL[1]}")
    return None
  else:
    surRange = [mins, maxs]
  if(minb > maxb):
    print("Minimum birth value is larger than maximum")
    return None
  elif(minb < RANGE_FOR_BIRTH[0] or maxb > RANGE_FOR_BIRTH[1]):
    print(f"Birth range is {RANGE_FOR_BIRTH[0]} - {RANGE_FOR_BIRTH[1]}")
    return None
  else:
    birthRange = [minb, maxb]

  if(r < rRange[0] or r>rRange[1]):
    print(f"Kernel radius range is {rRange[0]} - {rRange[1]}")
    return None
  
  if(aliveAdjustDenominator > ARR_W_SQ):
    print(f"alive denominator needs to be less than {ARR_W_SQ}")
    return None

  for btn in btnsList[:10]:  
    btn["state"] = "disabled"
  for btn in btnsList[10:]:
    btn["state"] = "enabled"

  if(kType == "Moore"):
    kernel = np.ones((2*r+1, 2*r+1))
  elif (kType == "circular"):
    tempArr = (np.arange(-r,r+1))**2
    kernel = ((tempArr[:,None] + tempArr)<=(r**2)).astype(int)
  else:
    a = np.arange(2*r+1)
    b = np.minimum(a,a[::-1])
    kernel = (b[:,None]+b >= (2*r-1)/2).astype(np.int8)
  kernel[r, r] = 1 if m == "yes" else 0
  print(kernel)

  return None

def seedValidator(P):
  global seed
  
  if P == "":
    P = "0"
  if str.isdigit(P) and len(P) < SEED_DIGITS:
    seed = int(P)
    initArrVal()
    setCanvasThread()
    return True
  else:
    return False

def nextFrame():
  global paused
  global universeArr
  global canvasThread

  paused = True
  if(playThread != None):
    playThread.join()
  startTime = time.time()
  universeArr = getNextTimestep()
  canvasThread = threading.Thread(target=setCanvasThread)
  canvasThread.start()
  print("Time to generate last frame:", time.time() - startTime)

def setPlay():
  global paused
  global playThread

  if paused:
    paused = False
    playThread = threading.Thread(target=playLoop)
    playThread.start()
  else:
    paused = True

def reset():
  global paused
  global playThread
  global canvasThread

  paused = True
  if(playThread != None):
    playThread.join()
  for btn in btnsList[10:]:
    btn["state"] = "disabled"
  initArrVal()
  canvasThread = threading.Thread(target=setCanvasThread)
  canvasThread.start()
  for btn in btnsList[:10]:
    btn["state"] = "active" 

def playLoop():
  global universeArr
  global canvasThread

  while not paused:
    startTime = time.time()
    newArr = getNextTimestep()
    canvasThread.join()
    universeArr = newArr
    canvasThread = threading.Thread(target=setCanvasThread)
    canvasThread.start()
    endTime = time.time()
    while (endTime-startTime) < 1/MAX_FRAME_PER_SEC:
      endTime = time.time()
    print("Time to generate last frame:", time.time() - startTime)

def getNextTimestep():
  #print(universeArr[:11,:11])
  #print(universeArr[:11,:11].sum())
  neighboursArr = scipy.ndimage.correlate(universeArr, kernel, mode="wrap")
  nextTimestep = np.where(universeArr, np.logical_and(neighboursArr>=surRange[0], neighboursArr<=surRange[1]), np.logical_and(neighboursArr>=birthRange[0], neighboursArr<=birthRange[1]))
  #print(nextTimestep.astype(np.int8)[:11,:11])
  return nextTimestep.astype(np.int8)

if __name__ == "__main__":
  initArrVal()
  canvasThread = threading.Thread(target=setCanvasThread)
  displayWindow()
