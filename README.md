# Cellular automaton

A <b>cellular automaton</b> consists of a regular grid of cells, each in one of a finite number of states, such as on and off. The grid can be in any finite number of dimensions. For each cell, a set of cells called its <b>neighborhood</b> is defined relative to the specified cell.

An initial state (time $t = 0$) is selected by assigning a state for each cell. A new generation is created (advancing $t$ by 1), according to some fixed rule that determines the new state of each cell in terms of the current state of the cell and the states of the cells in its neighborhood.

### Project Summary
- `Conways_game_of_life_tkinter.py`: Implements Conway's Game of Life. Although, Conway's Game of Life uses an infinite array, I will be using a 1024 x 1024 array. The rules are mentioned in the start of the file and the GUI is from the `tkinter` module.
- `Conways_game_of_life_dearpygui.py`: Like `Conways_game_of_life_tkinter.py` but uses the `dearpygui` module instead of `tkinter`.
- `maze_tkinter.py`: Implements Maze (see [https://conwaylife.com/wiki/OCA:Maze](https://conwaylife.com/wiki/OCA:Maze)) which also has the option for mazectric (by setting the [MAZECTRIC] to True).
- `larger_than_life.py`: Like `Conways_game_of_life_tkinter.py` but with the option to choose the kernel size, kernel type, survival conditions and birth conditions. The kernel type can be either "Moore" or "Von Neumann". Though the `Larger In Life` algorithm allows you to change the number of states, I have it as a constant of 2. I will implement multiple states in `Lenia.py`.
- `Lenia.py`: Like `Conways_game_of_life_tkinter.py` but with continuous states, a ring kernel and a smooth growth function. This is not a perfect implementation of Lenia.
- `Particle_Life/particleLife.py`: This file implements Particle Life
- `Particle_Life/attractionMatrix.txt`: A matrix used by `particleLife.py`

### Updates

<b>update 4.1:</b> Added `particleLife.py`.

<b>update 3.1:</b> Added `larger_than_life.py` and `Lenia.py`.

<b>update 2.3:</b> `Conways_game_of_life_tkinter.py` and `maze_tkinter.py` now use `scipy.ndimage.convolve` when checking for alive neighbours.

<b>update 2.2:</b> In `Conways_game_of_life_tkinter.py` and `maze_tkinter.py`, the canvas now updates image, instead of creating a new image every frame.

<b>update 2.1:</b> Added `maze_tkinter.py`.

<b>update 1.2:</b> Added `Conways_game_of_life_dearpygui.py` and `Conways_game_of_life_tkinter.py` which replaces `Conways_game_of_life.py`.

<b>update 1.1:</b> Initial commit