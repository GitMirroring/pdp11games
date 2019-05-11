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
import bisect  # sorted list management

#
# Bugs / plans / etc:
# ???

# Test on different terminals -- works on xterm, cygwin, screen.
# Test on real terminals.
# Port to Windows. Windows has no curses but access to Windows console
# can be done using ctypes interface to the native DLLs.

# The following ascii art is often attributed to David Palmer
# but he denies his authorship.
art = r"""
                                          _____________
   Mars War                            __/_|_|_|_|_|_|_\__
                                      /                   \    .
                 .       ____________/  ____               \   :
                 :    __/_|_|_|_|_|_(  |    |               )  |
                 |   /               \ | () |()  ()  ()  ()/   *
                 *  /  ____           \|____|_____________/
    .              (  |    |            \_______________/
    :               \ | () |()  ()  ()    \___________/
    |                \|____|____________ /   \______/     .
    *                  \_______________/       \  /       :
          3         .    \___________/         (__)       |    .
            3       :       \______/           /  \       *    :
             3      |         \  /            /    \           |
              3     *         (__)           /      \          *
        ,,     3              /  \          /        \
      w`\v',___n___          /    \        /          \
      v\`|Y/      /\        /      \      /            \
      `-Y/-'_____/  \      /        \    /              \
       `|-'      |  |     /          \  /                \
________|_|______|__|____/____________\/__________________\__

"""[1:]

scr = 0 # screen

debug=False

def partial_draw(y, x, s):
    if x < 0:
        if -x < len(s):
            scr.addstr(y, 0, s[-x:])
    elif x + len(s) > 79:
        if x < 80:
            scr.addstr(y, x, s[0:80-x])
    else:
        scr.addstr(y, x, s)
    
    
class Martian:  
    ufo = ("       "," *<O>* "," ----- "," ***** "," ----- "," ***** "," ----- "," ***** ",
           " ----- "," ***** "," ----- ","  ***  ","* *   *","*   * *"," *   * ","   *   ","       ")
    
    def __init__(self, y, turnprob, maxperiod):
        self.x = 0
        self.y = y
        self.dx = 0
        self.state = 0
        self.maxperiod=maxperiod
        self.period = random.randint(2, self.maxperiod)
        self.turnprob=turnprob
        
    def step(self, bombs, tick, canSpawn, dropdiff):
        dropped=0
        if self.state == 0:
            if random.randint(0, 400) == 0 and canSpawn:
                self.state = 1
                self.period = random.randint(2, self.maxperiod)
                if random.randint(0, 1) == 0:
                    self.x = -1
                    self.dx = 1
                else:
                    self.x = 80
                    self.dx = -1
        elif self.state == 1:
            if tick % self.period:
              return dropped
            if random.randint(0, max(2,(100-max(0,dropdiff)*4))) == 0 and self.x > -1 and self.x < 80: #check for out-of-bounds bombs
                bisect.insort(bombs,Bomb(self.x, self.y))
                dropped+=1
            if debug:
                scr.addstr(25, 0, "Drop chance: "+str(max(2,(100-max(0,dropdiff)*4))))
            if random.randint(0, self.turnprob) == 0:
                self.dx*=-1
                if random.randint(0, 3) ==0:
                    self.period = random.randint(2, self.maxperiod)
            self.x += self.dx
            if self.x < -1 or self.x > 80:
                self.state = 0
        elif self.state < len(self.ufo) - 1:
            if tick % 5: #throttle animation speed
              return dropped
            self.state += 1
        else:
            if tick % 5:
              return dropped
            self.state = 0
        return dropped

    def draw(self):
            if self.state:
                partial_draw(self.y, self.x-3, self.ufo[self.state])
           
class Man:  
    #       0    1    2     3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20   21   22   23   24   25   26   27   28   29   30   31   32 
    m  =("  O    +    O    =    +    O    =    +    O    =    +    O    =    +    O    =    +                                          . . .. . .. . .. . .. . .. . .  +       "
        ," /V\ \ V /I V I/ V \--V--\ V /I V I/ V \--V--\ V /I V I/ V \--V--\ V /I V I/ V \       O                       ...  ...  ...  ...  ...  ...        I    I    I       "
        ," _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_  _M_ / V \ _-_  _-_   .    .    .    .    .    .             /~\  /~\  /~\  /~\  /~\      ")
     #    123451234512345123451234512345123451234512345123451234512345123451234512345123451234512345123451234512345123451234512345123451234512345123451234512345123451234512345
    
    def __init__(self, x):
        self.x = x
        self.timer = 3
        self.state = 0
        self.delay = 3
        
    def step(self):
        if self.state == 0 or self.state == 31:
            return
        if self.timer > 0:
            self.timer -= 1
        else:
            self.timer = self.delay
            self.state += 1
        
    def draw(self):
        scr.addstr(21, self.x-1,  self.m[0][self.state*5:self.state*5+5])
        scr.addstr(22, self.x-1,  self.m[1][self.state*5:self.state*5+5])
        scr.addstr(23, self.x-1,  self.m[2][self.state*5:self.state*5+5])

class Bomb:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.delay = 20
                
    def step(self, bombs, people, martians):
        if self.timer:
            self.timer -= 1
            return 0
        else:
            self.timer=self.delay

        hit=0
        if self.y < 23:
            self.y += 1
            if self.y == 21:
                for obj in people:
                    if obj.state < 32 and abs(self.x - (obj.x+1)) <= 1:
                        obj.state += 1
                        hit=2 if obj.state == 32 else 1
                        bombs.pop(bisect.bisect_left(bombs,self))
                        break
            for obj in martians:
                if obj.state == 1 and self.y == obj.y and abs(self.x - obj.x) <= 2:
                    obj.state = 2
                    hit=3
                    bombs.pop(bisect.bisect_left(bombs,self))
        else:
            bombs.pop(bisect.bisect_left(bombs,self))
        return hit

    def draw(self):
        try:
            scr.addstr(self.y, self.x, "O")
        except:
            pass

    def __lt__(self,other):
        return self.x<other.x if self.x!=other.x else self.y<other.y

class Rocket:
    def __init__(self, x):
        self.x = x
        self.y = 20
        self.state = 0
 
    def step(self, martians,bombs):
        if self.state == 0:
            return 0
        hit = 0
        for obj in martians:
            if obj.state == 1 and self.y == obj.y and abs(self.x - obj.x) <= 2:
                obj.state = 2
                self.y = -1
                hit = 1
                break
        for obj in bombs:
            if self.x == obj.x and self.y == obj.y:
                bombs.pop(bisect.bisect_left(bombs,obj))
                self.y = -1
                hit = 2
                break

        if self.y > 0:
            self.y -= 1
        else:
            self.state = 0
            self.y = 20
        return hit
 
    def draw(self):
        if self.y > 0 and self.state:
            scr.addstr(self.y, self.x, "!")

class Launcher:
    def __init__(self, x, dx, rocketcap):
        self.x = x
        self.dx = dx
        self.inactive= 0
        self.rocketcap = rocketcap
        self.rocketnum = self.rocketcap
        self.rocketregentimer=10
        self.assisttime=0

    def step(self, bombs):
        hit=0
        if self.x < 4:
            self.dx = 1
        elif self.x > 76:
            self.dx = -1
        if self.inactive > 0:
            self.inactive-=1
        if self.rocketregentimer > 0 and self.rocketnum < self.rocketcap:
            self.rocketregentimer-=1
        if self.rocketregentimer == 0 and self.rocketnum < self.rocketcap:
            self.rocketnum+=1
            self.rocketregentimer=10
        if self.assisttime > 0:
            self.assisttime-=1
        self.x += self.dx
        for obj in bombs:
            if obj.y==20 and abs(self.x - obj.x) <= 2:
                bombs.pop(bisect.bisect_left(bombs,obj))
                hit+=1
                self.inactive=60
        return hit
    def draw(self):
        appearance=" {0}={1}={0} ".format("$" if self.assisttime else "=", "O" if self.inactive else ("!" if self.rocketnum else "#"))
        scr.addstr(20, self.x-3, appearance)
        if debug:
            scr.addstr(24, 0, "Regen timer: "+str(self.rocketregentimer))

def ask_and_move(s):
    scr.insstr(s)
    cpos = scr.getyx()
    scr.move(cpos[0], len(s))
    return cpos

def query(scores):
    scr.nodelay(0)
    curses.echo()
    ans=[]
    temp=""
    while temp not in list("nokswNOKSW"):
        cpos = ask_and_move("Choose your game type [N,O,K,S,W]: ")
        temp = chr(scr.getch())
        if cpos[0]>=23:
            scr.move(0,0)
            scr.deleteln()
            scr.move(cpos[0],0)
        else:
            scr.move(cpos[0]+1,0)
    ans.append(temp.upper())
    invalid=True
    while invalid:
        cpos = ask_and_move("Enter your name: ")
        temp = scr.getstr().decode()
        if cpos[0]>=23:
            scr.move(0,0)
            scr.deleteln()
            scr.move(cpos[0],0)
        else:
            scr.move(cpos[0]+1,0)
        if temp=="":
            sys.exit(0)
        if temp not in scores.keys():
                temp2=""
                while temp2 not in list("ynYN"):
                    cpos = ask_and_move("Are you a new player? [Y/N] ")
                    temp2 = chr(scr.getch())
                    if cpos[0]>=23:
                        scr.move(0,0)
                        scr.deleteln()
                        scr.move(cpos[0],0)
                    else:
                        scr.move(cpos[0]+1,0)
                if temp2 in list("yY"):
                    invalid = False
                    scores[temp]=[0,0,0,0,0,0]
                else:
                    invalid = True
        else:
            invalid=False
    ans.append(temp)
    temp=""
    while temp not in list("012345"):
        cpos = ask_and_move("Choose your level [0-5]:")
        temp = chr(scr.getch())
        if cpos[0]>=20:
            scr.move(0,0)
            scr.deleteln()
            scr.move(cpos[0],0)
        else:
            scr.move(cpos[0]+1,0)
    ans.append(int(temp))
    scr.nodelay(1)
    curses.noecho()
    return ans
    

def play(stdscr):
    global scr
    scr = stdscr
    curses.noecho()
    try:
        curses.curs_set(0)
    except:
        pass
    iterations=0
    for i, s in enumerate(art.split("\n")):   
        scr.addstr(i, 0, s)

    scorein = os.fdopen(os.open(os.path.expanduser("~/.marswar.txt"), os.O_RDWR | os.O_CREAT, mode=0o640), "r+")
    scores={i[0]:list(map(int,i[1:])) for i in map(lambda x: x.split(), scorein.readlines())}
    while True: 
        try:
            choices=query(scores)
        except KeyboardInterrupt:
            break
        scr.erase()

        scr.refresh()

        scr.nodelay(1)
        scr.keypad(1)

        iterations += 1 #end menu

        launcher = Launcher(40, 1, 8-choices[2])
        martians_count = [45,35,25,20,15,10][choices[2]]
        men = [Man(i*5 + 6) for i in range(14)]
        rockets = [Rocket(i) for i in range(80)]
        martiancoeffs={"N":[400, 9],"O":[200,8],"K":[50,7],"S":[30,6],"W":[10,5]}[choices[0]]
        martians = [Martian(*([i+2]+martiancoeffs)) for i in range(17)]
        bombs = []
        tick = 0
        deployed = 0 #for end menu
        deaths = 0 #see above
        assists = 0 # number of assists
        deadmen = 0
        desecration = 0
        dropped = 0
        deflect = 0
        damage = 0
        winning = 0
        try:
            while martians_count > 0 and any(map(lambda x: x.state==0, men)):
                n = scr.getch()

                if n in (97, 260):
                    launcher.dx = -1
                elif n in (100, 261):
                    launcher.dx = 1
                elif n in (119, 259, 115, 258):
                    launcher.dx = 0
                elif n == 32 and rockets[launcher.x].state==0 and launcher.inactive==0 and launcher.rocketnum>0:
                    rockets[launcher.x].state = 1            
                    launcher.rocketnum-=1
                    deployed+=1
                if launcher.assisttime and any(map(lambda x: launcher.x==x.x, bombs)) and rockets[launcher.x].state==0 and launcher.inactive==0 and launcher.rocketnum>0:
                    rockets[launcher.x].state = 1            
                    launcher.rocketnum-=1
                    deployed+=1
                    assists+=1
                scr.erase()
                scr.addstr(0, 0, "Number of martians: " + format(martians_count, "02d"))

                tick += 1
                damage += launcher.step(bombs)
                launcher.draw()
                for obj in martians:
                    dropped+=obj.step(bombs, tick, sum(list(map(lambda x: int(bool(x.state)),martians)))<martians_count, deployed-dropped)
                    obj.draw()
                if debug:
                    scr.addstr(27,0,str(sum(list(map(lambda x: int(bool(x.state)),martians))))+" "+str(list(map(lambda x: x.state,martians))))
                for obj in men:
                    obj.step()
                    obj.draw()
                for obj in rockets:
                    kill = obj.step(martians, bombs)
                    if kill==1:
                        deaths += 1
                        martians_count-=1
                    elif kill==2:
                        deflect+=1
                    obj.draw()
                for obj in bombs.copy():
                    boom=obj.step(bombs, men, martians)
                    if boom==1:
                        deadmen +=1
                        if choices[0]=="W":
                            launcher.assisttime=200
                    elif boom==2:
                        desecration += 1
                    elif boom==3:
                        martians_count-=1 #you don't get rewarded for martian incompetence
                    obj.draw()
                
                scr.refresh()
                curses.napms(50)
            if any(map(lambda x: x.state==0, men)):
                winning=0
            else:
                winning=1
        except KeyboardInterrupt:
            winning = 2
        coeffs={"time":-.125,
                "mart":100,
                "defl":10,
                "shot":-1,
                "hits":-40,
                "dead":-142,
                "bomb":1,
                "desc":-20,
                "winlose":(1028,-768,-10000),
                "chrg":-4}
        values={"time":tick,
                "mart":deaths,
                "defl":deflect,
                "shot":deployed,
                "hits":damage,
                "dead":deadmen,
                "bomb":dropped,
                "desc":desecration,
                "chrg":assists}
        total=sum([int(values[i]*coeffs[i]) for i in values.keys()]+[coeffs["winlose"][winning]])
        scores[choices[1]][choices[2]]=max(scores[choices[1]][choices[2]],total)
        winner=max(scores,key=lambda x: scores[x])
        winscore=scores[winner][choices[2]]
        bigstring="".join((
"Battle #:          {n: > 6}\n",
"Time spent:        {time[0]: > 6} {time[1]: > 6}\n" if values["time"]>0 else "",
"Martians defeated: {mart[0]: > 6} {mart[1]: > 6}\n" if values["mart"]>0 else "",
"Bombs deflected:   {defl[0]: > 6} {defl[1]: > 6}\n" if values["defl"]>0 else "",
"Rockets shot:      {shot[0]: > 6} {shot[1]: > 6}\n" if values["shot"]>0 else "",
"Launcher damage:   {hits[0]: > 6} {hits[1]: > 6}\n" if values["hits"]>0 else "",
"Assistance charge:        {chrg[1]: > 6}\n"         if values["chrg"]>0 else "",
"Personnel lost:    {dead[0]: > 6} {dead[1]: > 6}\n" if values["dead"]>0 else "",
"Bombs dropped:     {bomb[0]: > 6} {bomb[1]: > 6}\n" if values["bomb"]>0 else "",
"Graves desecrated: {desc[0]: > 6} {desc[1]: > 6}\n" if values["desc"]>0 else "",
"{winlose[0]: <18}        {winlose[1]: > 6}\n",
"--------------------------------\n",
"Total:                    {total: > 6}\n",
"\n",
"Your best result in this level is {highscore}\n",
"The absolute highest score was set by {winname}\n",
"with a score of {bestscore}\n","\n"))
        bigstring=bigstring.format(n=iterations,
                                   winlose=(("Victory bonus:", "Loss penalty:", "COWARDICE PENALTY:")[winning], coeffs["winlose"][winning]),
                                   total=total,
                                   highscore=scores[choices[1]][choices[2]],
                                   winname=winner,
                                   bestscore=winscore,
                                   **{i:(values[i], int(coeffs[i]*values[i])) for i in values.keys()})
                                   #^dictionary unpack, a neat python trick, quite useful sometimes
        scr.erase()
        scr.addstr(5,0,bigstring)
        scr.refresh()
    scorein.seek(0)
    scorein.truncate(0)
    for i in scores:
        scorein.write(i+" "+" ".join(map(str,scores[i]))+"\n")
    curses.endwin()
    return#sys.exit(0)



def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: marswar [OPTIONS]",
              "A quick game about fending off martians. The controls are arrow keys and space.",
              "",
              "-h, --help     Display this help page.",
              "-v, --version  Print the current version of the program.",
              "-d, --debug    Enable debug putstrs below the game field. Make sure your terminal",
              "               can fit them.", sep="\n")
        sys.exit(0)
    elif "--version" in sys.argv or "-v" in sys.argv:
        print("marswar 1.0")
        sys.exit(0)
        
    if any(map(operator.lt, tuple(shutil.get_terminal_size()), (80, 24))):
        # deal with people whose terminals are too small
        print ("Your screen size is too small. At least 80x24 is required");
        sys.exit(1)

    debug = "--debug" in sys.argv or "-d" in sys.argv
    curses.wrapper(play)
    #play(curses.initscr())

if __name__=="__main__":
    main()
