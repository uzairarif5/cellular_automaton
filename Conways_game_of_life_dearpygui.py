import time
import dearpygui.dearpygui as dpg
import numpy as np
import threading
import os

'''
Rules:
Although the universe is suppose to be infinite, I will be using an [ARR_W] x [ARR_W] looped array. Every cell interacts with its eight neighbours, which are the cells that are horizontally, vertically, or diagonally adjacent. At each step in time, the following transitions occur:
  - Any live cell with fewer than two live neighbours dies, as if by underpopulation.
  - Any live cell with two or three live neighbours lives on to the next generation.
  - Any live cell with more than three live neighbours dies, as if by overpopulation.
  - Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
The module `dearpygui` store a pixel as with four values, I will represent [1,1,1,0] (transparent) as a dead cell, while [1,1,1,1] (white) would be a living cell
'''

ARR_W = 100
ARR_W_SQ = ARR_W**2
PIXEL_WIDTH = 4
CANVAS_W = ARR_W*PIXEL_WIDTH
threadEvent = threading.Event()
playThread = None
universeArr = None

def initArrVal():
  global universeArr

  universeArr = np.ones((ARR_W_SQ, 4), dtype=np.int8)
  universeArr[np.random.choice(ARR_W_SQ, ARR_W_SQ//10, replace=False),3] = 0
  universeArr = np.reshape(universeArr,( ARR_W, ARR_W, 4))

def enlargeArrByPixWth(inpArr):
  intermediateArr = np.repeat(inpArr, PIXEL_WIDTH, axis=1).reshape(ARR_W, CANVAS_W, 4)
  return np.repeat(intermediateArr, PIXEL_WIDTH, axis=0).reshape(CANVAS_W, CANVAS_W,4)

def displayWindow():
  dpg.create_context()

  with dpg.texture_registry():
    dpg.add_dynamic_texture(CANVAS_W, CANVAS_W, enlargeArrByPixWth(universeArr), tag="main_canvas")

  with dpg.window(tag="Primary Window"):
    with dpg.drawlist(width=CANVAS_W, height=CANVAS_W):
      dpg.draw_image('main_canvas', (0, 0), (CANVAS_W, CANVAS_W))
    dpg.add_button(label="Play/Pause", callback=setPlay)
    dpg.add_button(label="Next Frame", callback=nextFrameWrapper)

  dpg.create_viewport(title='Conway\'s Game of Life',width=CANVAS_W+200,height=CANVAS_W+200)
  dpg.setup_dearpygui()
  dpg.show_viewport()
  dpg.set_primary_window("Primary Window", True)
  dpg.start_dearpygui()
  dpg.destroy_context()
  os.abort()

def setPlay():
  if(threadEvent.is_set()):
    threadEvent.clear()
  else:
    threadEvent.set()

def playLoop(e: threading.Event):
  while True:
    e.wait()
    startTime = time.time()
    t = threading.Thread(target=nextFrame)
    t.start()
    t.join()
    endTime = time.time()
    while ((endTime-startTime) < 1/12):
      endTime = time.time()
    print("Time to generate last frame:", endTime - startTime)

def nextFrame():
  global universeArr

  getNextTimeStepVec = np.vectorize(nextStep, signature="()->(m,n)")
  universeArr = getNextTimeStepVec(np.arange(ARR_W))
  dpg.set_value("main_canvas", enlargeArrByPixWth(universeArr))

def nextFrameWrapper():
  threadEvent.clear()
  nextFrame()

def nextStep(curRow):
  nextStepForRowV = np.vectorize(nextStepForRow, signature="(),()->(k)")
  return nextStepForRowV(curRow, np.arange(ARR_W))

def nextStepForRow(curRow, x):
  a = universeArr
  outputArr = np.array([1,1,1,1])
  neighborsAlive = 8 - ( \
    a[curRow-1,x-1,3] + a[curRow-1,x,3] + a[curRow-1,(x+1)%ARR_W,3] + \
    a[curRow,x-1,3] + a[curRow,(x+1)%ARR_W,3] + \
    a[(curRow+1)%ARR_W, x-1,3] + a[(curRow+1)%ARR_W, x,3] + a[(curRow+1)%ARR_W, (x+1)%ARR_W,3] \
  )
  if universeArr[curRow,x,3]: #cell dead
    if (neighborsAlive==3):
      outputArr[3] = 0
  else: #cell alive
    if (neighborsAlive==3 or neighborsAlive==2):
      outputArr[3] = 0
  return outputArr

if __name__ == "__main__":
  initArrVal()
  playThread = threading.Thread(target=playLoop, args=(threadEvent,))
  playThread.start()
  displayWindow()