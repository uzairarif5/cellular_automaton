import time
from tkinter import Canvas, ttk
import numpy as np
import tkinter as tk
import threading
import os
from PIL import ImageTk, Image

'''
Rules:
Although the universe is suppose to be infinite, I will be using an [ARR_W] x [ARR_W] looped array. Every cell interacts with its eight neighbours, which are the cells that are horizontally, vertically, or diagonally adjacent. At each step in time, the following transitions occur:
  - Any live cell with 1 to 5 live neighbours lives on to the next generation, otherwise it dies.
  - Any dead cell with exactly three live neighbours becomes a live cell.
if [MAZECTRIC] is True, then cells don't survive if they have 5 neighbours.
'''

MAZECTRIC = False
ARR_W = 100
ARR_W_SQ = ARR_W**2
PIXEL_WIDTH = 4
CANVAS_W = ARR_W*PIXEL_WIDTH
MAX_FRAME_PER_SEC = 6
MAX_NEIGHBOURS = 4 if MAZECTRIC else 5
universeArr = None
canvas: Canvas = None
threadEvent = threading.Event()
playThread = None
canvasThread = None
photoVar = None
canvasImgVar = None

def initArrVal():
  global universeArr

  universeArr = np.zeros((ARR_W_SQ), dtype=np.int8)
  universeArr[np.random.choice(ARR_W_SQ, ARR_W_SQ//10, replace=False)] = 1
  universeArr = np.reshape(universeArr,( ARR_W, ARR_W))

def displayWindow():
  global canvas
  root = tk.Tk()
  root.title("Conway's Game of Life")
  s = ttk.Style()
  s.configure('My.TFrame', background='dark gray')
  frm = ttk.Frame(root, style='My.TFrame')
  frm.grid(padx=10, pady=10)
  canvas = tk.Canvas(frm, borderwidth=0, highlightthickness=0, height=CANVAS_W, width=CANVAS_W)
  canvas.grid(column=0, row=0, columnspan=2)
  canvasThread.start()
  ttk.Button(frm, text="Play/Pause", command=setPlay).grid(column=0, row=1, pady=10)
  ttk.Button(frm, text="Next Frame", command=nextFrame).grid(column=1, row=1, pady=10)
  root.protocol("WM_DELETE_WINDOW",os.abort)
  root.configure(background='dark gray')
  root.mainloop()

def setCanvasThread():
  global photoVar
  global canvasImgVar

  intermediateArr = np.repeat(universeArr, PIXEL_WIDTH, axis=1).reshape(ARR_W, CANVAS_W)
  largeArr = np.repeat(intermediateArr, PIXEL_WIDTH, axis=0).reshape(CANVAS_W, CANVAS_W)
  photoVar =  ImageTk.PhotoImage(image=Image.fromarray(np.logical_not(largeArr)*255))
  if(canvasImgVar == None):
    canvasImgVar = canvas.create_image(0,0, anchor="nw", image=photoVar)
  else:
    canvas.itemconfig(canvasImgVar, image=photoVar)

def nextFrame():
  threadEvent.clear()
  setNextTimestep()

def setPlay():
  if(threadEvent.is_set()):
    threadEvent.clear()
  else:
    threadEvent.set()

def playLoop(e: threading.Event):
  while True:
    e.wait()
    startTime = time.time()
    t = threading.Thread(target=setNextTimestep)
    t.start()
    t.join()
    endTime = time.time()
    while ((endTime-startTime) < 1/MAX_FRAME_PER_SEC):
      endTime = time.time()
    #print("Time to generate last frame:", endTime - startTime)

def setNextTimestep():
  global universeArr
  global canvasThread

  nextStepV = np.vectorize(nextStep, signature="()->(n)")
  nextTimestep = nextStepV(np.arange(ARR_W))
  canvasThread.join()
  universeArr = nextTimestep
  canvasThread = threading.Thread(target=setCanvasThread)
  canvasThread.start()

def nextStep(curRow):
  nextStepForRowV = np.vectorize(nextStepForRow)
  return nextStepForRowV(curRow, np.arange(ARR_W))

def nextStepForRow(curRow, x):
  a = universeArr
  neighborsAlive = ( \
    a[curRow-1,x-1] + a[curRow-1,x] + a[curRow-1,(x+1)%ARR_W] + \
    a[curRow,x-1] + a[curRow,(x+1)%ARR_W] + \
    a[(curRow+1)%ARR_W, x-1] + a[(curRow+1)%ARR_W, x] + a[(curRow+1)%ARR_W, (x+1)%ARR_W] \
  )
  if universeArr[curRow,x]: #cell alive
    return 1 if (neighborsAlive>=1 and neighborsAlive<=MAX_NEIGHBOURS) else 0
  else: #cell dead
    return 1 if (neighborsAlive==3) else 0

if __name__ == "__main__":
  initArrVal()
  playThread = threading.Thread(target=playLoop, args=(threadEvent,))
  playThread.start()
  canvasThread = threading.Thread(target=setCanvasThread)
  displayWindow()