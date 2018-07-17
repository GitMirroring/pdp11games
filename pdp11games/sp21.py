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
# Copyright 2015 Peter Cherepanov

import curses
import random
import sys
import os
import shutil  # get terminal size.

# A clone of SP21.SAV Pac-man rewritten in Python 3 using ncurses.
#
# Bugs / plans / differences:
# No display of the bonus for eaten ghosts.
# In the original game the bonus value depends on the score only.
# In the original game Pac-man get trapped in the wrap passage sometimes. We don't need this.
# Pac-man animation freezes for one frame when using tunnel.
# Object-orient some more of the code, potentially.
# The ghost/pacman graphics are currently a hybrid of the original and the Russian version.
# Ghosts stay too long in the house.

# Test on different terminals -- works on xterm, cygwin, screen.
# Test on real terminals.
# Port to Windows. Windows has no curses but access to Windows console
# can be done using ctypes interface to the native DLLs.

mazes = [[
         "+-----------------------------------------------------------------------------+ ",
         "! .  .  .  .  .  .  .  .  .  .  .   . ! ! .   .  .  .  .  .  .  .  .  .  .  . ! ",
         "! . +-------+ . +-----------------+ . ! ! . +-----------------+ . +-------+ . ! ",
         "! @ !       ! . !                 ! . ! ! . !                 ! . !       ! @ ! ",
         "! . +-------+ . +-----------------+ . +-+ . +-----------------+ . +-------+ . ! ",
         "! .  .  .  .  .  .  .  .  .  .  .   .  .  .   .  .  .  .  .  .  .  .  .  .  . ! ",
         "! . +-------+ . +-------+ . +---------------------+ . +-------+ . +-------+ . ! ",
         "! . !       ! . !       ! .  .  .   . ! ! .   .  .  . !       ! . !       ! . ! ",
         "! . !       ! . !       +---------+ . +-+ . +---------+       ! . +-------+ . ! ",
         "! . +-------+ . !             !                 !             ! .  .  .  .  . ! ",
         "! .  .  .  .  . !             !   +--+ + +--+   +-------------+ . +-----------+-",
         "+-----------+ . +-------------+   !         !                   .               ",
         "              .                   !         !   +-------------+ . +-----------+-",
         "+-----------+ . +-------------+   +---------+   !             ! .  .  . +-----! ",
         "! .  .  .  .  . !             !                 !             ! . +-+ .  .  . ! ",
         "! . +-------+ . +-------------+   ===========   +-------------+ . ! !-----+ . ! ",
         "! @  .  . ! ! .  .  .  .  .  .  .   .     .   .  .  .  .  .  .  . ! ! .  .  @ ! ",
         "!-----+ . +-+ . +-------+ . +---------------------+ . +-------+ . +-+ . +-----! ",
         "! .  .  .  .  . !       ! . !                     ! . !       ! .  .  .  .  . ! ",
         "! . +-----------+       ! . +---------! !---------+ . !       +-----------+ . ! ",
         "! . !                   ! .  .  .   . ! ! .   .  .  . !                   ! . ! ",
         "! . +-----------------------------+ . +-+ . +-----------------------------+ . ! ",
         "! .  .  .  .  .  .  .  .  .  .  .   .  .  .   .  .  .  .  .  .  .  .  .  .  . ! ",
         "+-----------------------------------------------------------------------------+"],  
# the lower right corner is clipped because of a glitch where the cursor went out of bounds
        [
         "+-----------------------------------------------------------------------------+ ",
         "! .  .  .  .  .  .  .  .  .  .  .   .  .  .   .  .  . ! ! .  .  .  .  .  .  . ! ",
         "! . +-+ . +-----------------------+ . +-+ . +-----+ . +-+ . +-+ . +-------+ . ! ",
         "! . ! ! . !                       ! .  .  . !     ! .  .  . ! ! . !       ! . ! ",
         "! . +-+ . +-----------------+     +---------+     +--+ . +--+ ! . +-------+ . ! ",
         "! @  .  .  .  .  .  .  .  . !                        ! . !    ! .  .  .  .  . ! ",
         "! . +-+ . +-------------+ . +---------+ +------------+ . +--+ !-----+ . +-+ . ! ",
         "! . ! ! .  .  .  .  . ! ! .  .  .   . ! ! .   .  .  .  .  . ! ! .  .  . ! ! . ! ",
         "! . ! +-----------+ . ! +---------+ . +-+ . +-----------+ . ! ! . +-------+ . ! ",
         "! . +-------------+ . !       !                 !       ! . ! ! @  .  .  .  . ! ",
         "! .  .  .  .  .  .  . !       !   +--+ + +--+   +-------+ . +-------------+ . +-",
         "+-----------------+ . +-------+   !         !             .                     ",
         "                    .             !         !   +-------+ . +-----------------+-",
         "+ . +-------------+ . +-------+   +---------+   !       ! .  .  .  .  .  .  . ! ",
         "! .  .  .  .  @ ! ! . !       !                 !       ! . +-------------+ . ! ",
         "! . +-------+ . ! ! . +-------+   ===========   +-----+ ! . +-----------+ ! . ! ",
         "! . ! ! .  .  . ! ! .  .  .  .  .   .     .   .  .  . ! ! .  .  .  .  . ! ! . ! ",
         "! . +-+ . +-----! +--+ . +------------------------+ . +-------------+ . +-+ . ! ",
         "! .  .  .  .  . !    ! . !                        ! .  .  .  .  .  .  .  .  @ ! ",
         "! . +-------+ . ! +--+ . +--+     +---------+     +-----------------+ . +-+ . ! ",
         "! . !       ! . ! ! .  .  . !     ! .  .  . !                       ! . ! ! . ! ",
         "! . +-------+ . +-+ . +-+ . +-----+ . +-+ . +-----------------------+ . +-+ . ! ",
         "! .  .  .  .  .  .  . ! ! .  .  .   .  .  .   .  .  .  .  .  .  .  .  .  .  . ! ",
         "+-----------------------------------------------------------------------------+"],
        [
         "+-----------------------------------------------------------------------------+ ",
         "! .  .  .  .  .  .  .  .  .  .  .   . ! ! .   .  .  .  .  .  .  .  .  .  .  . ! ",
         "! . +-+ . +-+ . +-----------------+ . ! ! . +-----+ . +-------+ . +-------+ . ! ",
         "! @ ! ! . ! ! . !                 ! . ! ! . !     ! . !       ! . !       ! @ ! ",
         "! . +-+ . +-+ . +-----------------+ . +-+ . +-----+ . +-------+ . +-------+ . ! ",
         "! .  .  .  .  .  .  .  .  .  .  .   .  .  .   .  .  .  .  .  .  .  .  .  .  . ! ",
         "! . +-------+ . +---------------------------------+ . +---+ . +-----------+ . ! ",
         "! .  .  .  .  . ! .  .  . .  .  .   . ! ! .   .  .  . !   ! . ! .  .  . . ! . ! ",
         "! . +-------+ . ! . +-------------+ . +-+ . +---------+---+ . ! . +---+ . + . ! ",
         "! . +-------+ . ! . ! . . . . !                  .  .  .  . . ! .  .  .  .  . ! ",
         "! .  .  .  .  . ! .   . +-+ . !   +--+ + +--+   +-------------+ . +-----------+-",
         "+-----------+ . +-------+-+ . !   !         !                   .               ",
         "                            . !   !         !   +-------+-+ . + . +-----------+-",
         "+-------+   +-------------+ . !   +---------+   ! . . . +-+ . ! .  .  . +-----! ",
         "! .  .  .  .  . !   .  .  . . !                 ! . + .   . . ! . +-+ .  .  . ! ",
         "! . +-------+ . +-------------+   ===========   + . +---------+ . ! !-----+ . ! ",
         "! @  .  . ! ! .  .  .  .  .  .  .   .     .   .  .  .  .  .  .  . ! ! .  .  @ ! ",
         "!-----+ . +-+ . +-------+ . +---------------------+ . +---+ . +---+-+ . +-----! ",
         "! .  .  .  .  . !       ! . !                     ! . !   ! . ! .  .  .  .  . ! ",
         "! . +-------+ . +-------+ . +---------! !---------+ . !   ! . +-----------+ . ! ",
         "! . !       ! .  .  .  .  .  .  .   . ! ! .   .  .  . !   ! .   .  .  .  .  . ! ",
         "! . +-------+ . +-----------------+ . +-+ . +-------------+---------------+ . ! ",
         "! .  .  .  .  .  .  .  .  .  .  .   .  .  .   .  .  .  .  .  .  .  .  .  .  . ! ",
         "+-----------------------------------------------------------------------------+"]]


class Pacman:

    def __init__(self, x, y, gdir, timer):
        self.x = x
        self.y = y
        self.prevx = x
        self.prevy = y
        self.gdir = gdir
        self.timer = timer
        self.alive = True

    def pic(self):
        global t
        # the on-death script changes t every ghost munching frame 
        return ("<$>", ">$<")[(self.x + self.y) % 2] if self.alive else ("+$+" if t % 2 == 0 else "$+$") 

    def touching(self, x, y):
        return self.x == x and self.y == y

    def lookdown(self):
        global maze
        return maze[self.y][self.x - 1:self.x + 2]

    def draw(self):
        global a
        p = self.pic()
        if self.x == 79:  # handle tunnels
            a.addstr(self.y, 78, p[:2])
            a.addstr(self.y + 1, 0, p[2:])
        elif self.x == 0:
            a.addstr(self.y, 0, p[1:])
            a.addstr(self.y - 1, 79, p[:1])
        else:
            a.addstr(self.y, self.x - 1, p)

    def move(self, x, y):
        self.prevx = self.x
        self.prevy = self.y
        self.x = x
        self.y = y 
        

class Ghost(Pacman):

    def pic(self):  # ghosts look different from pacman but share most of their code
        return "---" if not self.alive else "=0=" if self.timer == 0 else "<->"

    def step(self):  #ghost pathfinding algorithm
        gposs = []
        global maze, walls, combo, pac
        self.prevx = self.x
        self.prevy = self.y
        if self.x == 39 and self.y == 10:
            self.alive = True
            self.timer = 0
        if (maze[self.y + 1][self.x] not in walls and maze[self.y + 1][self.x - 1] not in walls and maze[self.y + 1][self.x + 1] not in walls and self.gdir != 1) or (maze[self.y + 1][self.x] == "+" and maze[self.y + 1][self.x + 1] == " " and maze[self.y + 1][self.x - 1] == " " and not self.alive):
            gposs.append(0)
        if (maze[self.y - 1][self.x] not in walls and maze[self.y - 1][self.x - 1] not in walls and maze[self.y - 1][self.x + 1] not in walls and self.gdir != 0) or (maze[self.y - 1][self.x] == "+" and maze[self.y - 1][self.x + 1] == " " and maze[self.y - 1][self.x - 1] == " "):
            gposs.append(1)
        if self.x >= 2 and (self.gdir != 3 and maze[self.y][self.x - 2] not in walls):
            gposs.append(2)
        if self.x <= 77 and (self.gdir != 2 and maze[self.y][self.x + 2] not in walls):
            gposs.append(3)
        if pac.gdir in gposs: # minor preference for going in the direction pacman does
            gposs.append(pac.gdir)
        if len(gposs) > 0:
            self.gdir = wrand(
                gposs, self.x, self.y, 2 if not self.alive else 0 if self.timer == 0 else 1)
        if self.x == 79 and self.gdir == 3:
            self.x = -1  # fencepost error
            self.y = 12
        if self.x == 0 and self.gdir == 2:
            self.x = 80  # also fencepost error
            self.y = 11
        self.x += (0, 0, -1, 1)[self.gdir]
        self.y += (1, -1, 0, 0)[self.gdir]
        if self.timer > 0:
            self.timer -= 1
            if self.timer == 0:
                self.gdir = -1

    def ghosttouch(self, target):  # what happens when pacman touches a ghost?
        global score, combo
        if ((self.x == target.x or (target.prevx == self.x and target.x == self.prevx)) and
            (self.y == target.y or (target.prevy == self.y and target.y == self.prevy)) and self.alive):
            if self.timer > 0:
                self.alive = False
                combo += 20
                score += combo
            else:
                target.alive = False


def wrand(a, x, y, state):
    global pac
    if state == 0:
        if x > 33 and x < 45 and y > 9 and y < 14:  # if in ghost house:
            if random.randint(0, 2) != 0:
                return random.choice(a)
            elif y > 9 and 1 in a:
                return 1
            elif x > 39 and 2 in a:
                return 2
            elif x < 39 and 3 in a:
                return 3
            else:
                return random.choice(a)
        else:  # state: hungry, chasing pacman
            if random.randint(0, 3) == 0:
                return random.choice(a)
            elif pac.y > y and 0 in a:
                return 0
            elif pac.y < y and 1 in a:
                return 1
            elif pac.x < x and 2 in a:
                return 2
            elif pac.x > x and 3 in a:
                return 3
            else:
                return random.choice(a)
    elif state == 1:  # state: terrified of pacman, appetite suppressed
        if random.randint(0, 3) == 0:
            return random.choice(a)
        elif pac.y < y and 0 in a:
            return 0
        elif pac.y > y and 1 in a:
            return 1
        elif pac.x > x and 2 in a:
            return 2
        elif pac.x < x and 3 in a:
            return 3
        else:
            return random.choice(a)
    elif state == 2:  # state: dead, going home
        if random.randint(0, 4) == 0:
            return random.choice(a)
        elif y < 10 and 0 in a:
            return 0
        elif y > 10 and 1 in a:
            return 1
        elif x > 39 and 2 in a:
            return 2
        elif x < 39 and 3 in a:
            return 3
        elif y == 9 and x == 39:  # always enter ghost house
            return 0
        else:
            return random.choice(a)


def reset():
    global pac, q, g1, g2, g3, g4, stillalive
    pac = Pacman(39, 16, 0, 0)
    g1 = Ghost(38, 11, 0, 0)
    g2 = Ghost(40, 11, 1, 0)
    g3 = Ghost(39, 11, 2, 0)
    g4 = Ghost(39, 12, 3, 0)
    q = None

def show_lives(x):
    # in Roman numerals x10 without subtraction rule
    line = 0
    while(x):
        if x >= 100:
            c = "M"
            x -= 100
        elif x >= 50:
            c = "D"
            x -= 50
        elif x >= 10:
            c = "C"
            x -= 10
        elif x >= 5:
            c = "L"
            x -= 5
        else:
            c = "X"
            x -= 1
        a.addstr(line, 79, c)
        line += 1 if line != 9 else 4

def getwch(a):  # get wide char, for unicode support on scoreboard
    acc = []
    c = 256  # placeholder value
    while c > 255:  # while c is not a real character
        c = a.getch()
        if c == 263 or c == 127:  # handle enter press
            return chr(c)
    acc.append(c)
    cnt = 0
    if (c & 0xE0) == 0xC0:
        cnt = 1
    elif (c & 0xF0) == 0xE0:
        cnt = 2
    elif (c & 0xF8) == 0xF0:
        cnt = 3
    elif (c & 0xFC) == 0xF8:
        cnt = 4
    elif (c & 0xFE) == 0xFC:
        cnt = 5
    for i in range(cnt):
        acc.append(a.getch())
    return bytes(acc).decode("utf-8");  

def write_in(a, x, y, score):
    acc = ""
    a.addstr(y, 0, " " * 18)
    a.addstr(11, 40, "ENTER YOUR NAME")
    a.addstr(y, 20 - len(str(score)), str(score))
    a.addstr(y, 0, format(y-1, "02d"))
    a.addstr(y,x,acc)
    a.refresh()
    while True:
        c = getwch(a)
        if ord(c) == 263 or ord(c) == 127:
            if len(acc):
                acc = acc[0:-1]
                a.addstr(y,x+len(acc)," ")
        elif ord(c) == 10:
            return acc
        else:
            acc = acc + c
        a.addstr(y, 0, " " * 18)
        a.addstr(11, 40, "ENTER YOUR NAME")
        a.addstr(y, 20 - len(str(score)), str(score))
        a.addstr(y, 0, format(y-1, "02d"))
        a.addstr(y,x,acc)
        a.refresh()
    return acc

def pac_hall(score):
    global a
    scorein = os.fdopen(os.open(os.path.expanduser("~/.sp21.txt"), os.O_RDWR | os.O_CREAT, mode=0o640), "r+")  # if there is no file, make one
    scorelist = scorein.readlines()[:20]  # scoreboard only shows top 20. may as well be efficient
    minval = min(map(lambda x: int(x.split(" ", 1)[0]), scorelist)) if len(scorelist) else 0  # handle empty scoreboard
    winning = ((len(scorelist) < 20 and score != -1) or score > minval) and "--debug" not in sys.argv  # make this use debug variable latter
    if winning:
        scorelist.append(str(score) + " ")
        scorelist = sorted(
            scorelist, reverse=True, key=lambda x: int(x.split()[0]))

    a.addstr("      PAC-HALL\n--------------------\n")
    for i in range(len(scorelist)):
        j = scorelist[i].split(" ", 1)
        a.addstr(i + 2, 0, (format(i + 1, "02d") + " " + j[1])[:20])
        a.addstr(i + 2, 20 - len(j[0]), j[0])
    a.addstr(min(len(scorelist), 20) + 2, 0, "NN *********        ")
    pscore = scorelist[-1].split()[0] if score > minval else str(score if score != -1 else 0)
    a.addstr(min(len(scorelist), 20) + 2, 20-len(pscore), pscore)
    if winning:
        i = len(scorelist) - 1
        while score > int(scorelist[i].split()[0]):
            i -= 1
        a.nodelay(0)
        try:
            curses.curs_set(1)  # an exception is thrown if you cannot curs_set. so this ignores it
        except:
            pass
        a.keypad(1)
        name = write_in(a,3,i + 2,score)
        scorelist[i] = str(score) + " " + name + "\n"
        scorein.seek(0)
        scorein.truncate(0)
        for i in scorelist[:20]:
            scorein.write(i)
        a.addstr(11, 40, "               ") 
# ENTER YOUR NAME is longer than ONCE MORE ? so the above erases the former to make space for the latter
    a.addstr(11, 40, "BEGIN ?" if score == -1 else "ONCE MORE ?")
    scorein.close()
    a.nodelay(0)
    while True:
        ch = a.getch()
        if ch == 121 or ch == 89 or ch == 10:  # if you pressed y, Y, or enter:
            a.nodelay(1)
            return True
        if ch == 110 or ch == 78:  # if you pressed n or N:
            a.nodelay(1)
            return False

def play():
    global a, maze, walls, score, combo, t, pac, g1, g2, g3, g4
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""Usage: sp21 [-OPTIONS]
A port of the Pacman game for the PDP-11/RT-11.

  -h, --help     Display this help page.
  -v, --version  Print the current version of the program.
      --debug    Enable the debug features. + and - double
                 and halve the time step length, 0 toggles
                 single-step mode, and ? bumps your score 
                 by 2001. Note: Score submission is 
                 disabled with debug mode on.""")
        sys.exit(0)
    elif "--version" in sys.argv or "-v" in sys.argv:
        print("sp21 1.0")
        sys.exit(0)
    debug = "--debug" in sys.argv
    timestep = 20
    onestep = False
    s = shutil.get_terminal_size()
    a = curses.initscr()
    curses.noecho()
    try:
        curses.curs_set(1)
    except:
        pass
    if not pac_hall(-1):  # placeholder score
        curses.endwin()
        sys.exit(0)
    while True:  # this loop is for the ONCE AGAIN ? prompt
        t = 0
        level = -1  # this is to get it to play the level load animation and recalculate the dots
        dcount = 0  # see above
        maze = []
        lives = 3
        score = 0
        lastscore = 0
        combo = 0
        bpower = 15
        bonus = False
        btime = -1
        tunnelpos = 0
        walls = "+!-="  # just in case we need to add more wall types later on
        try:
            curses.curs_set(0)
        except:
            pass
        curses.noecho()
        a.keypad(1)
        a.nodelay(1)
        pac = Pacman(39, 16, 0, 0)
        g1 = Ghost(39, 11, 0, 0)
        g2 = Ghost(39, 11, 1, 0)
        g3 = Ghost(39, 11, 2, 0)
        g4 = Ghost(39, 11, 3, 0)
        dots = 0
        q = None
        while True:  # this loop is the game internals
            s = shutil.get_terminal_size()
            if s[0] < 80 or s[1] < 24:  # deal with people whose terminals are too small
                while s[0] < 80 or s[1] < 24:
                    a.erase()
                    a.addstr(
                        0, 0, "Your screen is too small for this program"[:s[0]])
                    if s[1] > 2:
                        a.addstr(1, 0, "80x24 is the minimum screen size required"[
                                 :s[0]])  # this breaks with ludicrously small terminal sizes
                    a.refresh()
                    curses.napms(100)
                    s = shutil.get_terminal_size()
                else:
                    curses.endwin()
                    a = curses.initscr()

            while True:  # read all the queued button presses and parse them.
                         # this made more sense when the timestep wasn't 20ms
                n = a.getch()
                if n == -1:
                    break
                if debug:  # debug features!
                    if n == 61:  # if n is +:
                        timestep *= 2
                    if n == 45:  # if n is -:
                        timestep //= 2
                    if n == 48:  # if n is 0:
                        onestep = not onestep
                    if n == 63:  # if n is ?:
                        score += 2001

                # wasd --> arrows
                if n == 119:   # w
                    n = 259
                elif n == 97:  # a
                    n = 260
                elif n == 115: # s
                    n = 258
                elif n == 100: # d
                    n = 261

                if n in [258, 259, 260, 261]:  # if n is an arrow key
                    if n - 258 == 0 and (maze[pac.y + 1][pac.x] in walls or maze[pac.y + 1][pac.x - 1] in walls or maze[pac.y + 1][pac.x + 1] in walls):
                        q = 0  # if you cannot move in that direction, queue that movement
                    elif n - 258 == 1 and (maze[pac.y - 1][pac.x] in walls or maze[pac.y - 1][pac.x - 1] in walls or maze[pac.y - 1][pac.x + 1] in walls):
                        q = 1
                    elif n - 258 == 2 and (pac.x >= 2 and maze[pac.y][pac.x - 2] in walls):
                        q = 2
                    elif n - 258 == 3 and (pac.x <= 77 and maze[pac.y][pac.x + 2] in walls):
                        q = 3
                    else:
                        pac.gdir = n - 258  # but if you can, feel free to move in that direction

            t += 1

            if dots >= dcount:
                dots = 0
                level += 1
                maze = [i for i in mazes[level % 3]]
                reset()
                dcount = 0
                for i, m in enumerate(maze):
                    a.addstr(i, 0, m)
                    a.refresh()
                    dcount += m.count('.')
                    curses.napms(83)  # = 80 * 1000 / 960

            a.erase()
            for i in range(len(maze)):
                a.addstr(i, 0, maze[i])
            if score > 0:
                a.addstr(18, 42 - len(str(score)), str(score))
            if score - lastscore >= 500:
                lives += 1
                lastscore = score // 500 * 500
            show_lives(lives - 1)

            if t % 4 == 0:
                g1.step()
                g2.step()
                g3.step()
                g4.step()
            g1.ghosttouch(pac)
            g2.ghosttouch(pac)
            g3.ghosttouch(pac)
            g4.ghosttouch(pac)

            if not pac.alive:
                lives -= 1
                for i in range(15):
                    pac.draw()
                    a.refresh()
                    t += 1
                    curses.napms(100)
                    if i == 7: # purge final movements from the keyboard buffer
                        while a.getch() != -1:
                            pass
                if lives <= 0:
                    break
                reset()
            if bonus:
                a.addstr(14, 38, str(bpower)[0] + "*" + str(bpower)[1] if bpower < 100 else str(bpower))
                if btime == 0:
                    bonus = False
                    bpower = 15
                else:
                    btime -= 1
            elif random.randint(1, 2000) == 1:
                bonus = True
                btime = 400
            if bonus and pac.touching(39, 14):
                score += bpower
                if bpower < 90:
                    bpower += 15
                btime = -1
                bonus = False
            if "." in pac.lookdown():  # if there's a dot below me:
                maze[pac.y] = maze[pac.y][
                    :pac.x - 1] + "   " + maze[pac.y][pac.x + 2:]  # there is no longer a dot below me
                dots += 1
                score += 1
            elif "@" in pac.lookdown():  # see above but with power pellets
                maze[pac.y] = maze[pac.y][
                    :pac.x - 1] + "   " + maze[pac.y][pac.x + 2:]
                timer = 120 if score < 2500 else 60
                if score < 2000 or random.random() > 0.14: # after 2000 points, sometimes ghosts don't get affected by power pellets
                    g1.timer = timer  # individual timers because when eaten and respawned, a ghost's timer resets
                if score < 2000 or random.random() > 0.14:
                    g2.timer = timer
                if score < 2000 or random.random() > 0.14:
                    g3.timer = timer
                if score < 2000 or random.random() > 0.14:
                    g4.timer = timer
                pac.timer = timer  # this timer handles pacman's speed up
                g1.gdir = -1  # this lets the ghosts turn around
                g2.gdir = -1
                g3.gdir = -1
                g4.gdir = -1
                combo = 0  # eating a power pellet resets your ghosts-eaten combo point counter thing
                score += 5

            if not g1.alive:
                g1.draw()
            if not g2.alive:
                g2.draw()
            if not g3.alive:
                g3.draw()
            if not g4.alive:
                g4.draw()

            if g1.alive:
                g1.draw()
            if g2.alive:
                g2.draw()
            if g3.alive:
                g3.draw()
            if g4.alive:
                g4.draw()

            pac.draw()

            if (t % 3 == 0) if pac.timer > 0 else (t % 4 == 0):  # pacman is a bit faster when he has a power pellet
                if (pac.gdir == 0 and q == 1) or (pac.gdir == 1 and q == 0) or (pac.gdir == 2 and q == 3) or (pac.gdir == 3 and q == 2):
                    q = None # directional queueing. if your queued action is opposite of what direction you're moving, reset the queue 
                elif q == 0 and maze[pac.y + 1][pac.x] not in walls and maze[pac.y + 1][pac.x - 1] not in walls and maze[pac.y + 1][pac.x + 1] not in walls:
                    pac.gdir = 0
                    q = None 
                elif q == 1 and maze[pac.y - 1][pac.x] not in walls and maze[pac.y - 1][pac.x - 1] not in walls and maze[pac.y - 1][pac.x + 1] not in walls:
                    pac.gdir = 1
                    q = None
                elif q == 2 and maze[pac.y][pac.x - 2] not in walls:
                    pac.gdir = 2
                    q = None
                elif q == 3 and maze[pac.y][pac.x + 2] not in walls:
                    pac.gdir = 3
                    q = None

                if pac.x == 79 and pac.gdir == 3:
                    pac.move(-1, 12)  # see the corresponding code in the ghost pathing function
                if pac.x == 0 and pac.gdir == 2:
                    pac.move(80, 11)
                if pac.gdir == 0 and maze[pac.y + 1][pac.x] not in walls and maze[pac.y + 1][pac.x - 1] not in walls and maze[pac.y + 1][pac.x + 1] not in walls:
                    pac.move(pac.x, pac.y + 1)  # actually moving pacman
                elif pac.gdir == 1 and maze[pac.y - 1][pac.x] not in walls and maze[pac.y - 1][pac.x - 1] not in walls and maze[pac.y - 1][pac.x + 1] not in walls:
                    pac.move(pac.x, pac.y - 1)
                elif pac.gdir == 2 and (pac.x < 2 or maze[pac.y][pac.x - 2] not in walls):
                    pac.move(pac.x - 1, pac.y)
                elif pac.gdir == 3 and (pac.x > 77 or maze[pac.y][pac.x + 2] not in walls):
                    pac.move(pac.x + 1, pac.y)

            if pac.timer > 0 and t % 4 == 0:
                pac.timer -= 1

            if debug:
                a.addstr(25, 0, str((pac.x, pac.y)))  # i am not good with coordinates
                a.addstr(26, 0, str(q))
            a.addstr(23, 79, "")  # put the cursor in the corner, just in case curs_set failed
            a.refresh()

            if onestep:
                a.nodelay(0)
                char = a.getch()
                if char == 48:  # onestep mode eats all your button presses. this lets you exit it to maneuver
                    onestep = False
                a.nodelay(1)
            curses.napms(timestep)  # sticking the timestep into a variable is for debug and tweaking's sake
                                    # also: the timestep is a quarter of the time per ghost-move. this is so that power pelleted pacman can move at 3 steps per character
        a.erase()  # remember the loop which handled ONCE AGAIN ? This code runs once the main game loop is broken out of. if you agree to continue, the loop loops and a new game is started
        if not pac_hall(score):  # if player answered no to ONCE AGAIN ?
            curses.endwin()
            sys.exit(0)

def main():
    try:  # the entire program is in a try-except statement to handle keyboard interrupts by closing curses
        play()
    except KeyboardInterrupt:
        curses.endwin()

if __name__=="__main__":
    main()
