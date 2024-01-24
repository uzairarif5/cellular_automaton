from tkinter import Canvas, ttk
import numpy as np
import tkinter as tk
import threading
import os
from PIL import Image, ImageTk

'''
Rules:
Although the universe is suppose to be infinite, I will be using an [ARRAY_WIDTH] x [ARRAY_WIDTH] looped array. Every cell interacts with its eight neighbours, which are the cells that are horizontally, vertically, or diagonally adjacent. At each step in time, the following transitions occur:
  - Any live cell with fewer than two live neighbours dies, as if by underpopulation.
  - Any live cell with two or three live neighbours lives on to the next generation.
  - Any live cell with more than three live neighbours dies, as if by overpopulation.
  - Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
'''

ARR_W = 100
ARR_W_SQ = ARR_W**2
PIXEL_WIDTH = 4
CANVAS_W = ARR_W*PIXEL_WIDTH
threadEvent = threading.Event()
playThread = None
universeArr = None
canvas: Canvas = None

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
  canvas = tk.Canvas(frm, borderwidth=0, highlightthickness=0, height=CANVAS_W, width=CANVAS_W, background="white")
  canvas.grid(column=0, row=0, columnspan=2)
  setCanvas()
  ttk.Button(frm, text="Play/Pause", command=setPlay).grid(column=0, row=1, pady=10)
  ttk.Button(frm, text="Next Frame", command=nextFrameWrapper).grid(column=1, row=1, pady=10)
  root.protocol("WM_DELETE_WINDOW",os.abort)
  root.configure(background='dark gray')
  root.mainloop()

def setCanvas():
  canvas.create_rectangle(-1, -1, CANVAS_W, CANVAS_W, fill="white")
  for (y, x) in np.argwhere(universeArr==1):
    curX = x*4
    curY = y*4
    canvas.create_rectangle(curX, curY, curX+PIXEL_WIDTH, curY+PIXEL_WIDTH, fill="black")

def setPlay():
  if(threadEvent.is_set()):
    threadEvent.clear()
  else:
    threadEvent.set()

def playLoop(e: threading.Event):
  while True:
    e.wait()
    t = threading.Timer(0.5, nextFrame)
    t.start()
    t.join()
    del t

def nextFrame():
  global universeArr

  nextStepV = np.vectorize(nextStep, signature="()->(n)")
  nextTimeSet = nextStepV(np.arange(ARR_W))
  universeArr = nextTimeSet
  setCanvas()

def nextFrameWrapper():
  threadEvent.clear()
  nextFrame()

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
    return 1 if (neighborsAlive==3 or neighborsAlive==2) else 0
  else: #cell dead
    return 1 if (neighborsAlive==3) else 0

if __name__ == "__main__":
  initArrVal()
  playThread = threading.Thread(target=playLoop, args=(threadEvent,))
  playThread.start()
  displayWindow()