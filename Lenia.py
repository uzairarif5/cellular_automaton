
import math
from tkinter import END, Canvas, StringVar, ttk
import tkinter as tk
import numpy as np
import threading
import time
import os
from PIL import ImageTk, Image
import scipy.ndimage

'''
Lenia is like Conway's Game of Life but with continuous states, time and space. read this article for more insight [https://hegl.mathi.uni-heidelberg.de/continuous-cellular-automata/].

The kernel is donut shaped made from the smooth gaussian function
  bell = lambda x, m, s: np.exp(-((x-m)/s)**2 / 2)

  tempArr = (np.arange(-size,size+1))**2
  tempArr2 = tempArr[:,None] + tempArr
  kernel = bell(tempArr2, ringR**2, (ringR**2)/2)
  kernel = kernel / np.sum(kernel)


On updates, a growth function is used, that, based on the current state of the cells, returns the amount by which the state of a cell changes. In the case of the Game of Life, this would either be -1 if the cell dies, 0 in case the state doesn't change, and 1 if it comes back to life. For Lenia, the growth function for a cell x is 2 * e^(0.5 * (((x-u)/s)^2)) -1, where u and s are parameters chosen by the user.

Lenia is suppose to have infinite states in the range [0, 1], which gets updated by the growth value in range [-1, 1]. The results (old value + growth value) gets clipped to [0, 1].

After evaluating the growth function, it is multiplied by 1/F (variable timeFrac is used for F) where F is the update frequency. By using larger values of F, we can simulate "continuous time." 

'''

ARR_W = 100
ARR_W_SQ = ARR_W**2
KERNEL_SIZE_RANGE = [1,ARR_W-1]
PIXEL_WIDTH = 4
CANVAS_W = ARR_W*PIXEL_WIDTH
MAX_FRAME_PER_SEC = 24
SEED_DIGITS = 9
seed = 0
universeArr = None
canvas: Canvas = None
canvasThread = None
playThread = None
photoVar = None
canvasImgVar = None
kernel = None
paused = True
btnsList = None
timeFrac = 10
growthMean = 0
growthStdDev = 1

def initArrVal():
  global universeArr

  np.random.seed(seed)
  universeArr = np.random.random((ARR_W,ARR_W))

def displayWindow():
  global canvas
  global btnsList

  root = tk.Tk()
  root.title("Lenia")

  s = ttk.Style()
  s.configure('My.TFrame', background='dark gray')

  frm = ttk.Frame(root, style='My.TFrame')
  frm.grid(padx=10, pady=10)

  kernelSLabel = ttk.Label(frm, text="Choose kernel size:", background='dark gray')
  kernelSLabel.grid(column=0, row=0, sticky="sw")
  kSize = StringVar(frm)
  kSize.set("10")
  kernelSizeW = ttk.Entry(frm, textvariable=kSize)
  kernelSizeW.grid(column=0, row=1, sticky="nw")

  growthMLabel = ttk.Label(frm, text="Choose growth mean:", background='dark gray')
  growthMLabel.grid(column=0, row=2, sticky="sw")
  growM = StringVar(frm)
  growM.set("0.15")
  growthMW = ttk.Entry(frm, textvariable=growM)
  growthMW.grid(column=0, row=3, sticky="nw")

  growthStdDevLabel = ttk.Label(frm, text="Choose growth s.d.:", background='dark gray')
  growthStdDevLabel.grid(column=0, row=4, sticky="sw")
  growthStdDev = StringVar(frm)
  growthStdDev.set("0.015")
  growthStdDevW = ttk.Entry(frm, textvariable=growthStdDev)
  growthStdDevW.grid(column=0, row=5, sticky="nw")

  timeLabel = ttk.Label(frm, text="Enter denominator value for time:", background='dark gray')
  timeLabel.grid(column=0, row=6, sticky="sw")
  timeVal = StringVar(frm)
  timeVal.set("50")
  timeW = ttk.Entry(frm, textvariable=timeVal)
  timeW.grid(column=0, row=7, sticky="nw")

  vcmdForSeed = frm.register(seedValidator)
  seedLabel = ttk.Label(frm, text="Seed:", background='dark gray')
  seedLabel.grid(column=0, row=8, sticky="sw")
  seedText = StringVar(frm)
  seedText.set("0")
  seedEntry = ttk.Entry(frm, validate='key' , validatecommand =(vcmdForSeed,"%P"), textvariable=seedText)
  seedEntry.grid(column=0, row=9, sticky="nw")

  completeSettingBtn = ttk.Button(frm, text="set", command=None)
  completeSettingBtn.grid(column=0, row=10)

  canvas = tk.Canvas(frm, borderwidth=0, highlightthickness=0, height=CANVAS_W, width=CANVAS_W)
  canvas.grid(column=1, row=0, columnspan=3, rowspan=10, padx=(10,0))
  canvasThread.start()

  playPauseBtn =  ttk.Button(frm, text="Play/Pause", command=setPlay)
  playPauseBtn.grid(column=1, row=10, pady=10)
  playPauseBtn["state"] = "disabled"

  nextFrameBtn = ttk.Button(frm, text="Next Frame", command=lambda: threading.Thread(target=nextFrame).start())
  nextFrameBtn.grid(column=2, row=10, pady=10)
  nextFrameBtn["state"] = "disabled"
  
  resetBtn = ttk.Button(frm, text="Reset", command=lambda: threading.Thread(target=reset).start())
  resetBtn.grid(column=3, row=10, pady=10)
  resetBtn["state"] = "disabled"

  btnsList = [kernelSizeW, growthMW, growthStdDevW, timeW, seedEntry, completeSettingBtn, playPauseBtn, nextFrameBtn, resetBtn]
  completeSettingBtn.config(command=lambda: setkernel(kSize.get(), growM.get(), growthStdDev.get(), timeVal.get()))

  root.protocol("WM_DELETE_WINDOW",os.abort)
  root.configure(background='dark gray')
  root.mainloop()

def setCanvasThread():
  global photoVar
  global canvasImgVar

  intermediateArr = np.repeat(universeArr, PIXEL_WIDTH, axis=1).reshape(ARR_W, CANVAS_W)
  largeArr = np.repeat(intermediateArr, PIXEL_WIDTH, axis=0).reshape(CANVAS_W, CANVAS_W)
  newPhoto =  ImageTk.PhotoImage(image=Image.fromarray((largeArr*255).astype(np.uint8)))
  if(canvasImgVar == None):
    canvasImgVar = canvas.create_image(0,0, anchor="nw", image=newPhoto)
  else:
    canvas.itemconfig(canvasImgVar, image=newPhoto)
  photoVar = newPhoto

def setkernel(size: str, growM: str, growthSd: str, timeVal:str):
  global kernel
  global timeFrac
  global growthMean
  global growthStdDev

  try:
    size = int(size)
    timeFrac = int(timeVal)
    growthMean = float(growM)
    growthStdDev = float(growthSd)
  except:
    print("Error trying to convert input values")
    return None

  if(size < KERNEL_SIZE_RANGE[0] or size > KERNEL_SIZE_RANGE[1]):
    print(f"Kernel radius range is {KERNEL_SIZE_RANGE[0]} - {KERNEL_SIZE_RANGE[1]}")
    return None
  
  for btn in btnsList[:6]:  
    btn["state"] = "disabled"
  for btn in btnsList[6:]:
    btn["state"] = "enabled"

  ringR = math.floor(size * 0.75)
  bell = lambda x, m, s: np.exp(-((x-m)/s)**2 / 2)
  tempArr = (np.arange(-size,size+1))**2
  tempArr2 = tempArr[:,None] + tempArr
  kernel = bell(tempArr2, ringR**2, (ringR**2)/2)
  kernel = kernel/np.sum(kernel)

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
  for btn in btnsList[6:]:
    btn["state"] = "disabled"
  if(playThread != None and playThread.is_alive()):
    playThread.join()
  initArrVal()
  canvasThread = threading.Thread(target=setCanvasThread)
  canvasThread.start()
  for btn in btnsList[:6]:
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

def growth(arr):
  return 2 * np.exp(-0.5 * (((arr-growthMean)/growthStdDev)**2)) -1

def getNextTimestep():
  nextTimestep = scipy.ndimage.correlate(universeArr, kernel, mode="wrap")
  return np.clip(universeArr + (1/timeFrac * growth(nextTimestep)), 0, 1)

if __name__ == "__main__":
  initArrVal()
  canvasThread = threading.Thread(target=setCanvasThread)
  displayWindow()
