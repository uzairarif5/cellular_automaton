
from tkinter import Canvas, ttk
import tkinter as tk
import numpy as np
import threading
import time
import os
from PIL import ImageTk, Image
import scipy.ndimage

'''
Rules:
Although the universe is suppose to be infinite, I will be using an [ARR_W] x [ARR_W] looped array. Every cell interacts with its eight neighbours, which are the cells that are horizontally, vertically, or diagonally adjacent. At each step in time, the following transitions occur:
  - Any live cell with fewer than two live neighbours dies, as if by underpopulation.
  - Any live cell with two or three live neighbours lives on to the next generation.
  - Any live cell with more than three live neighbours dies, as if by overpopulation.
  - Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
'''

ARR_W = 150
ARR_W_SQ = ARR_W**2
PIXEL_WIDTH = 4
CANVAS_W = ARR_W*PIXEL_WIDTH
MAX_FRAME_PER_SEC = 6
THREAD_EVENT = threading.Event()
universeArr = None
canvas: Canvas = None
playThread = None
canvasThread = None
photoVar = None
canvasImgVar = None
kernel = np.ones((3,3))
kernel[1,1] = 0

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

  intermediateArr = np.repeat(np.logical_not(universeArr), PIXEL_WIDTH, axis=1).reshape(ARR_W, CANVAS_W)
  largeArr = np.repeat(intermediateArr, PIXEL_WIDTH, axis=0).reshape(CANVAS_W, CANVAS_W)
  newPhoto =  ImageTk.PhotoImage(image=Image.fromarray(largeArr*255))
  if(canvasImgVar == None):
    canvasImgVar = canvas.create_image(0,0, anchor="nw", image=newPhoto)
  else:
    canvas.itemconfig(canvasImgVar, image=newPhoto)
  photoVar = newPhoto

def nextFrame():
  THREAD_EVENT.clear()
  startTime = time.time()
  setNextTimestep()
  print("Time to generate last frame:", time.time() - startTime)

def setPlay():
  if(THREAD_EVENT.is_set()):
    THREAD_EVENT.clear()
  else:
    THREAD_EVENT.set()

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

  neighboursArr = scipy.ndimage.convolve(universeArr, kernel, mode="wrap")
  nextTimestep = np.where(neighboursArr == 2, universeArr, neighboursArr == 3)
  canvasThread.join()
  universeArr = nextTimestep
  canvasThread = threading.Thread(target=setCanvasThread)
  canvasThread.start()

if __name__ == "__main__":
  initArrVal()
  playThread = threading.Thread(target=playLoop, args=(THREAD_EVENT,))
  playThread.start()
  canvasThread = threading.Thread(target=setCanvasThread)
  displayWindow()