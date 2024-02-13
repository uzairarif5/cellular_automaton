
import numpy as np
import cv2 as cv
import scipy.ndimage

ARR_W = 200
ARR_H = 180
SIZE_EXTENSION_FOR_VIDEO = 4
W_CHANGE_ON_ONE_SIDE = 10
FOURCC = cv.VideoWriter_fourcc(*'XVID')
DURATION = 60
FPS = 6
FILENAME = 'output.avi'
DEAD_COLOR = np.array([187,227,255], dtype=np.uint8)
ALIVE_COLOR = [138,186,252]
ALIVE_DEAD_RATIO_AT_START = 0.3
KERNEL = [[1,1,1],[1,0,1],[1,1,1]]

universeArr = np.random.choice([0,1], (ARR_H, ARR_W), p=[1-ALIVE_DEAD_RATIO_AT_START,ALIVE_DEAD_RATIO_AT_START])
#uncomment if you want middle area to remain empty
#universeArr[:, W_CHANGE_ON_ONE_SIDE: -W_CHANGE_ON_ONE_SIDE] = 0

out = cv.VideoWriter(FILENAME, FOURCC, FPS, (ARR_W*SIZE_EXTENSION_FOR_VIDEO, ARR_H*SIZE_EXTENSION_FOR_VIDEO))

for _ in range(FPS*DURATION):
  neighoursCount = scipy.ndimage.convolve(universeArr, KERNEL, mode="wrap")
  universeArr = np.where(neighoursCount == 2, universeArr, neighoursCount == 3)
  onesPos = np.argwhere(universeArr)
  newArr = np.ones((ARR_H, ARR_W,3), dtype=np.uint8)
  newArr *= DEAD_COLOR
  if(len(onesPos)):
    newArr[onesPos[:,0],onesPos[:,1],:] = ALIVE_COLOR
  img = np.repeat(np.repeat(newArr, SIZE_EXTENSION_FOR_VIDEO, axis=1), SIZE_EXTENSION_FOR_VIDEO, axis=0)
  out.write(img)

out.release()

