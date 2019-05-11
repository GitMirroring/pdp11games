#!/usr/bin/python3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2016 Peter Cherepanov

import curses
import random
import sys
import os
import shutil  # get terminal size.
import operator

# A clone of XONIX.SAV rewritten in Python 3 using ncurses.
#
# Bugs / plans / differences:
#
# Test on different terminals -- works on xterm, cygwin, screen.
# Test on real terminals.
# Port to Windows. Windows has no curses but access to Windows console
# can be done using ctypes interface to the native DLLs.

sys.setrecursionlimit(1500)

xonix = [
"0.    0.  000.   0.    0. 000. 0.    0.",
" 0.  0.  0.  0.  00.   0.  0.   0.  0. ",
"  0.0.  0.    0. 0.0.  0.  0.    0.0.  ",
"   0.   0.    0. 0. 0. 0.  0.     0.   ",
"  0.0.  0.    0. 0.  0.0.  0.    0.0.  ",
" 0.  0.  0.  0.  0.   00.  0.   0.  0. ",
"0.    0.  000.   0.    0. 000. 0.    0."]

field = [80*[0] for i in range(23)]

scr = 0 # screen

def floodfill(x, y):
    if field[y][x] == ' ':
        field[y][x] = '1'
        floodfill(x, y+1)
        floodfill(x, y-1)
        floodfill(x+1, y)
        floodfill(x-1, y)

def invert():
    count = 0
    for i, row in enumerate(field):
        for j, char in enumerate(row):
            if char == '1':
                row[j] = ' '
            elif char == ' ':
                row[j] = "▉"
                count += 1
                scr.addstr(i, j, "▉")
    return count   

def init_field():
    for i in range(23):
        for j in range(80):
            field[i][j] = "▉" if i < 2 or i > 20 or j < 3 or j > 76 else " " 
    
class Pacman:  
    def __init__(self, x, y, gdir):
        self.x = x
        self.y = y
        self.prevx = x
        self.prevy = y
        self.startx = x
        self.starty = y
        self.gdir = gdir
        self.state = 0
        self.trail = []
        
    def step(self):
        self.prevx = self.x
        self.prevy = self.y
        if self.gdir == 1: # right
            if self.x < 79:
                self.x += 1
        elif self.gdir == 2: # left
            if self.x > 0:
                self.x -= 1
        elif self.gdir == 3: # up
            if self.y > 0:
                self.y -= 1
        elif self.gdir == 4: # down
            if self.y < 22:
                self.y += 1
        if self.state == 0:
            if field[self.y][self.x] == " ":
                self.state = 1;
                self.trail += [(self.x, self.y)]
                self.startx = self.prevx
                self.starty = self.prevy
        elif self.state == 1:
            if (self.x, self.y) in self.trail:
                self.trail = []
                self.x = self.startx
                self.y = self.starty
                self.gdir = 0
                return True
            if field[self.y][self.x] == " ":
                self.trail += [(self.x, self.y)]
            else:
                self.state = 0
                self.gdir = 0
        return False

    def draw(self, scr):
        if field[self.prevy][self.prevx] != ' ':
            scr.addstr(self.prevy, self.prevx, field[self.prevy][self.prevx])
        for x, y in self.trail:
            scr.addstr(y, x, "*")
        scr.addstr(self.y, self.x, "@")
        
    def back(self):
        self.x = self.startx
        self.y = self.starty
        self.gdir = 0
        self.state = 0
        self.trail = []
           
class Ghost:
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.prevx = x
        self.prevy = y
        self.dx = dx
        self.dy = dy
    
    def blocked(self, x, y):
        return x < 0 or x > 79 or y < 0 or y > 22 or field[y][x] == ' '
            
    def step(self):
        self.prevx = self.x
        self.prevy = self.y
        if self.blocked(self.x+self.dx, self.y+self.dy):
            if self.blocked(self.x+self.dx, self.y-self.dy):
                if self.blocked(self.x-self.dx, self.y+self.dy):
                    self.dx *= -1
                    self.dy *= -1
                else:
                    self.dx *= -1
            else:
                if self.blocked(self.x-self.dx, self.y+self.dy):
                    self.dy *= -1
                else:
                    # choice
                    self.dy *= -1
        self.x += self.dx
        self.y += self.dy   
   
    def draw(self):
        scr.addstr(self.prevy, self.prevx, field[self.prevy][self.prevx])
        scr.addstr(self.y, self.x, " ")

class Ball(Ghost):
    def __init__(self):
        x = random.randint(4, 72)
        y = random.randint(3, 17)
        dx, dy = ((1,1), (1,-1), (-1,1), (-1,-1))[random.randint(0, 3)] 
        self.x = x
        self.y = y
        self.prevx = x
        self.prevy = y
        self.dx = dx
        self.dy = dy

    def blocked(self, x, y):
        return field[y][x] != ' '

    def draw(self):
        scr.addstr(self.prevy, self.prevx, " ")
        scr.addstr(self.y, self.x, "o")

def play():
    global scr
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: xonix [-OPTIONS]",
              "A port of the XONIX game for the PDP-11/RT-11.",
              "",
              "-h, --help     Display this help page.",
              "-v, --version  Print the current version of the program.", sep="\n")
        sys.exit(0)
    elif "--version" in sys.argv or "-v" in sys.argv:
        print("xonix 1.0")
        sys.exit(0)
        
    if any(map(operator.lt, tuple(shutil.get_terminal_size()), (80, 24))):
        # deal with people whose terminals are too small
        print ("Your screen size is too small. At least 80x24 is required");
        sys.exit(1)

    scr = curses.initscr()
    curses.noecho()
    try:
        curses.curs_set(0)
    except:
        pass

    best_result = 0
    your_result = 0
    game_result = 0
    time = 0
    
    while True: 
        scr.erase()
        for i, s in enumerate(xonix):
            scr.addstr(i + 8, 21, s)
        if your_result != 0:
            scr.addstr(1, 0,  "Your result: " + str(your_result))
        if best_result != 0:
            scr.addstr(1, 60, "Best result: " + str(best_result))
        
        scr.addstr(22, 0, "Exit:  Ctl-C")
        scr.addstr(23, 0, "Start: Enter")
        scr.addstr(22, 55, "Salt Lake City, UT - 2016")
        scr.refresh()

        scr.nodelay(0)
        scr.keypad(1)
        while True:
            n = scr.getch()
            if n in (78, 110, 10):
                break
        if n in (78, 110):
            break

        your_result = 0
        game_result = 0

        init_field()
        attempts = 10
        balls = [Ball(), Ball(), Ball()]
        pac = Pacman(40, 0, 0)

        while attempts:
            scr.erase()
            for i, s in enumerate(field):
                scr.addstr(i, 0, "".join(s))
            scr.addstr(23, 0, "Result: " + format(your_result, '8'))
            scr.addstr(23, 30, "G a m e: " + format(game_result, '8'))
            scr.addstr(23, 54, "Attempts:  " + format(attempts, '2'))
            scr.addstr(23, 69, "Time:")
        
            scr.refresh()
       
            pac.back()
            ghosts = [Ghost(40, 22, 1 ,1)]
            scr.nodelay(1)
            tick = 0 
            time = 60
            while True:
                n = scr.getch()

                # wasd --> arrows
                if n in (119, 259):   # w, up
                    pac.gdir = 3
                elif n in (97, 260):  # a, left
                    pac.gdir = 2
                elif n in (115, 258): # s, down
                    pac.gdir = 4
                elif n in (100, 261): # d, right
                    pac.gdir = 1
                eaten = pac.step()
                pac.draw(scr)
                for obj in balls:
                    obj.step()
                    obj.draw()
                    if (obj.x, obj.y) in pac.trail:
                        eaten = True
                        break 
                for obj in ghosts:
                    if tick % 2 == 0:
                        obj.step()
                        obj.draw() 
                    if pac.x == obj.x and pac.y == obj.y:
                        scr.addstr(obj.y,obj.x, "X")
                        field[obj.y][obj.x] = "X"
                        eaten = True
                        break
                if eaten:
                    attempts -= 1
                    curses.napms(700)
                    break
                if pac.state == 0 and len(pac.trail):
                    for obj in pac.trail:
                        scr.addstr(obj[1], obj[0], "▉")
                        field[obj[1]][obj[0]] = "▉"
                    for obj in balls:
                        floodfill(obj.x, obj.y);
                    cnt = invert() + len(pac.trail)
                    your_result += cnt
                    game_result += cnt
                    best_result = max(best_result, your_result)
                    
                    pac.trail = []
                    scr.addstr(23, 8, format(your_result, '8'))
                    scr.addstr(23, 39, format(game_result, '8'))
                    if game_result >= 1000:
                        game_result = 0
                        init_field()
                        for i, obj in enumerate(field):
                            scr.addstr(i, 0, "".join(obj))
                        balls += [Ball()]
                        ghosts = [Ghost(40, 22, 1 ,1)]
                        pac = Pacman(40, 0, 0)

                scr.refresh()
                curses.napms(50)
                if tick % 20 == 0:
                    time -= 1;
                    if time <= 0:
                        time = 60
                        ghosts += [Ghost(random.randint(30, 50), 22, 1 ,1)]
                    scr.addstr(23, 76, format(time,'2'))
                tick += 1
    curses.endwin()
    sys.exit(0)

def main():
    try:  # the entire program is in a try-except statement to handle keyboard interrupts by closing curses
        play()
    except KeyboardInterrupt:
        curses.endwin()

if __name__=="__main__":
    main()
