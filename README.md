# Cellular automaton

A <b>cellular automaton</b> consists of a regular grid of cells, each in one of a finite number of states, such as on and off. The grid can be in any finite number of dimensions. For each cell, a set of cells called its <b>neighborhood</b> is defined relative to the specified cell.

An initial state (time $t = 0$) is selected by assigning a state for each cell. A new generation is created (advancing $t$ by 1), according to some fixed rule that determines the new state of each cell in terms of the current state of the cell and the states of the cells in its neighborhood.

### Project Summary
- `Conways_game_of_life_tkinter.py`: Implements Conway's Game of Life. Although, Conway's Game of Life uses an infinite array, I will be using a 1024 x 1024 array. The rules are mentioned in the start of the file and the GUI is from the `tkinter` module.
- `Conways_game_of_life_dearpygui.py`: Like `Conways_game_of_life_tkinter.py` but uses the `dearpygui` module instead of `tkinter`.