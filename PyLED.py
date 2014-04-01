#!/usr/bin/python

#####################################
# PyVDF.py                          #
# Author: noriah            #
# For controlling LED Strips        #
# Copyright (c) 2014 noriah #
#####################################

import time
import threading
from threading import Thread
from random import randint
from colors import *

class Strip(threading.Thread):
    def __init__(self, num = 80, fname = '/dev/spidev0.0', sleeptime = 0.0005, pixel_size = 3):
        threading.Thread.__init__(self)
        self.num_leds = num
        self.leds_left = num
        self.pixel_size = pixel_size
        self.streams = list()
        self.sleeptime = sleeptime
        self.data = self.newstream(num, False)
        self.stripstream = False
        self.strip = file(fname, "wb")
        self.name = "Strip Scheduling Thread"
        self.dorun = True

    def __getitem__(self, key):
        return self.streams[key]

    def __setitem__(self, key, value):
        self.streams[key] = value

    def __delitem__(self, key):
        del self.streams[key]
        
    def newstream(self, num_leds, subLEDS = True):
        if subLEDS:
            
            if num_leds > self.leds_left:
                raise RuntimeError('Not Enough LEDS Left')


            self.streams.append(Stream(num_leds, self, self.pixel_size))
            self.leds_left -= num_leds
            return self.streams[-1]

        else:
            return Stream(num_leds, self, self.pixel_size)


    def clear(self):
        self.strip.write(bytearray(self.num_leds * self.pixel_size))
        self.strip.flush()
        return


    def run(self):
        while self.dorun:
            updated = False
            for stream in self.streams:
                if stream.hasAnimation():
                    updated = True
                    anim = stream.getAnimation()
                    if anim.isFirstRun():
                        anim.start()
                    else:
                        anim._run()
                    if anim.isFinished():
                        stream.removeAnim(anim)

            if updated: self.show()
            time.sleep(self.sleeptime)

    def stop(self):
        self.dorun = False

    def restart(self):
        self.dorun = True
        self.start()

    def show(self):
            self.strip.write(sum(self.streams))
            self.strip.flush()
            #print(sum(self.streams))
            return

class Stream:
    def __init__(self, num, parent, pixel_size = 3):
        self.num_leds = num
        self.pixel_size = pixel_size
        self.pixnum = num * self.pixel_size
        self.data = bytearray(self.pixnum)
        self.temps = self.data
        self.parent = parent
        self.animqueue = list()

    def __add__(self, other):
        return self.data + other

    def __radd__(self, other):
        if isinstance(other, int):
            return self.data
        else:
            return other + self.data

    def __len__(self):
        return len(self.data) / self.pixel_size

    def __getitem__(self, key):
        return self.getLED(key)

    def __setitem__(self, key, value):
        self.setLED(key, value)

    def __delitem__(self, key):
        self.setLED(key, BLACK)

    def animate(self, animation):
        animation.setParent(self)
        self.animqueue.append(animation)

    def hasAnimation(self):
        return len(self.animqueue) > 0

    def getAnimation(self):
        if self.hasAnimation():
            return self.animqueue[0]
        else:
            return None

    def removeAnim(self, animation):
        self.animqueue.remove(animation)

    def getStream(self):
        return self.data

    def getLED(self, led):
        return self.data[n * self.pixel_size:(n * self.pixel_size) + self.pixel_size]
    
    def getNumLEDS(self):
        return self.num_leds

    def setStream(self, data):
        self.data = data

    def setLED(self, led, data):
        #print(int(data[0]), int(data[1]), int(data[2]))
        self.data[led * self.pixel_size:(led * self.pixel_size) + self.pixel_size] = data[:]
    
    def fill(self, colors):
        if not isinstance(colors, list):
            colors = [colors]
        b = bytearray()
        nc = len(colors)
        d = (self.num_leds % nc)
        d = d if d != 0 else 1
        perc = (self.num_leds / nc) + (nc / d)
        for x in xrange(nc):
            b += (colors[x] * perc)

        self.data = b[:self.pixnum]

    def pattern(self, pattern):
        if not isinstance(pattern, list):
            pattern = [pattern]

        a = bytearray()
        a += pattern[0]
        for b in pattern[1:]:
            a += b
        a = a * self.num_leds
        self.data = a[:self.pixnum]

    def off(self):
        self.temps = self.data
        self.data = bytearray(self.pixnum)

    def on(self):
        self.data = self.temps

gamma = bytearray(256)
for i in range(256):
    gamma[i] = i#int(pow(float(i) / 255.0, 1.5) * 255.0)

def filter_pixel(input_pixel, brightness):
    output_pixel = bytearray(3)
    input_pixel[0] = int(brightness * input_pixel[0])
    input_pixel[1] = int(brightness * input_pixel[1])
    input_pixel[2] = int(brightness * input_pixel[2])
    output_pixel[0] = gamma[input_pixel[0]]
    output_pixel[1] = gamma[input_pixel[1]]
    output_pixel[2] = gamma[input_pixel[2]]
    return output_pixel


class Animation:
    def __init__(self):
        self.__initialized = False
        self.__running = False
        self.__finished = False
        self.__parent = None
        self.__timer = 0

    def setParent(self, parent):
        self.__parent = parent

    def getStream(self):
        if self.__parent != None:
            return self.__parent.getStream()
        else:
            return bytearray(15)

    def getLED(self, led):
        if self.__parent != None:
            return self.__parent.getLED(led)
        else:
            return bytearray(3)

    def getNumLEDS(self):
        if self.__parent != None:
            return self.__parent.getNumLEDS()
        else:
            return 5

    def setStream(self, data):
        if self.__parent != None:
            self.__parent.setStream(data)
   
    def setLED(self, led, data):
        if self.__parent != None:
            self.__parent.setLED(led, data)
    
    def fill(self, colors):
        if self.__parent != None:
            self.__parent.fill(colors)
   
    def pattern(self, pattern):
        if self.__parent != None:
            self.__parent.pattern(pattern)

    def _init(self):
        self.init()
        self.__initialized = True

    def init(self):
        return
    
    # def __runloop(self):
    #     if self.__looper != None:
    #         try:
    #             self.loopvalue = self.__looper.next()
    #             self.loopnum += 1
    #         except StopIteration:
    #             self.finished()

    # def useLoop(self, data):
    #     self.__looper = iter(data)

    # def loop(loop_over):
    #     def wrap(run_func):
    #         wrap.loop = enumerate(iter(loop_over))
    #         def loopedRun(self):
    #             try:
    #                 a, b = self.loop_over.next()
    #                 run_func(self, a, b)
    #             except StopIteration:
    #                 self.finished()

            
    #     self.__runloop()
    #     return run_func(self.loopvalue, self.loopnum)



    def _run(self):
        if self.__timer - 1 > -1:
            self.__timer -= 1
            return
        self.run()
        #self.__runloop()

    def run(self):
        self.finished()

    #def __bootstrap(self):
        #self._init()
        #self.__runloop()
        #self._run()


    def start(self):
        #self.__bootstrap()
        self._init()
        self._run()

    def reset(self):
        self.__initialized = False
        self.__running = False
        self.__finished = False
        self.__timer = 0
        return

    def isFirstRun(self):
        return not self.__initialized

    def finished(self):
        self.__finished = True

    def isFinished(self):
        return self.__finished

    def isRunning(self):
        return self.__running

    def sleep(self, cycles):
        self.__timer = cycles

class AnimationGroup(Animation):
    def __init__(self):
        Animation.__init__(self)
        self.animations = list()
        self.__size = 0
        self.__repeat = -1
        self.__repeats = -1
        self.__infinite_repeat = False

        return

    def __len__(self):
        return self.__size
    
    def add(self, animation):
        animation.setParent(self)
        self.__size += 1
        self.animations.append(animation)

    def remove(self, animation):
        self.animations.remove(animation)
        self.__size -= 1

    def clearAnimations(self):
        self.animations = list()
        self.__size = 0

    def reset(self):
        Animation.reset(self)
        self.__repeats = 0
        self.repeatReset()

    def repeatReset(self):
        self.__current_index = 0
        for x in self.animations:
            x.reset()

    def repeat(self, cycles = 1, infinite = False):
        self.__repeat = cycles
        self.__repeats = 0
        self.__infinite_repeat = infinite

    def haveAnimations(self):
        #print(self.__size)
        return self.__current_index < self.__size

    def getAnimation(self):
        return self.animations[self.__current_index]

    def init(self):
        self.__current_index = 0
        self.noanim = True

    def run(self):
        if self.haveAnimations():
            if self.noanim:
                self.canim = self.getAnimation()
                self.noanim = False
                if self.canim.isFirstRun():
                    self.canim.start()
            else:
                self.canim._run()
                
        if self.canim.isFinished():
            self.__current_index += 1
            self.noanim = True
            if not self.haveAnimations():
                if self.__infinite_repeat:
                    self.repeatReset()
                elif self.__repeats < self.__repeat:
                    self.__repeats += 1
                    self.repeatReset()
                else:
                    self.finished()
        return

class fill(Animation):
    def __init__(self, colors):
        Animation.__init__(self)
        self.colors = colors
        return

    def run(self):
        self.fill(self.colors)
        self.finished()
        return

class pattern(Animation):
    def __init__(self, colors):
        Animation.__init__(self)
        self.colors = colors
        return

    def run(self):
        self.pattern(self.colors)
        self.finished()
        return

class pulse(Animation):
    def __init__(self, cycles = 1, steps = 15, wait = 0):
        Animation.__init__(self)

        self.maxcycles = cycles
        self.maxsteps = steps
        self.wait = wait
        return

    def init(self):
        self.cycles = iter(xrange(self.maxcycles))
        self.c = self.getStream()
        self.state = 0
        self.step = 1.0/float(self.maxsteps)
        self.r = [(q * 3) for q in xrange(len(self.c)/3)]
        return

    def run(self):

        if self.state == 0:
            self.z = iter(xrange(self.maxsteps))
            self.b = bytearray(len(self.c))
            self.state = 1

        if self.state == 1:
            y = self.z.next()
            for i in self.r:
                self.b[i:i + 3] = filter_pixel(self.c[i:i + 3], 1 - ((y + 1) * self.step))
            self.setStream(self.b)

            if y + 1 == self.maxsteps:
                self.z = iter(xrange(self.maxsteps))
                self.state = 2

        elif self.state == 2:
            y = self.z.next()
            for i in self.r:
                self.b[i:i + 3] = filter_pixel(self.c[i:i + 3], (y + 1) * self.step)
            self.setStream(self.b)

            if y + 1 == self.maxsteps:
                #self.setStream(self.c)
                #self.z = iter(xrange(self.maxsteps))
                self.state = 3

        if self.state == 3:
            if self.cycles.next() + 1 == self.maxcycles:
                self.finished()
            else:
                self.state = 0
        self.sleep(self.wait)
                
        return


class flash(Animation):
    def __init__(self, cycles = 1, wait = 10):
        Animation.__init__(self)
        self.maxcycles = cycles * 2
        self.wait = wait
        return

    def init(self):
        self.cycles = iter(xrange(self.maxcycles))
        self.c = self.getStream()
        self.clear = bytearray(len(self.c))
        self.state = 0
        return

    def run(self):
        s = self.cycles.next() + 1

        if self.state == 0:
            self.setStream(self.clear)
            self.state = 1

        elif self.state == 1:
            self.setStream(self.c)
            self.state = 0

        if s == self.maxcycles:
            self.finished()
        else:
            self.sleep(self.wait)

        return


class sweep(Animation):
    def __init__(self, colors, doubleBack = True, frm = 0, to = None, direction = 1, wait = 10):
        Animation.__init__(self)
        
        self.t = to
        self.f = frm
        self.db = doubleBack
        self.d = direction

        if not isinstance(colors, list):
            colors = [colors]

        self.colors = colors

        self.wait = wait

        self.first_run = True

        return

    def pre_run(self):
        self.t = self.t if self.t else self.getNumLEDS() - 1
        if self.f > self.t:
            a = self.t
            self.t = self.f
            self.f = a

        numLeds = self.t - self.f
        ledRange = range(numLeds)
        if self.db:
            self.x = ledRange[::2] + (ledRange[-2::-2] if numLeds%2 else ledRange[::-2])
        else:
            self.x = ledRange

        self.lenx = len(self.x)
        self.x = self.x[::self.d]

    def init(self):
        if self.first_run:
            self.pre_run()
            self.first_run = False

        k = -1
        a = []
        colors = self.colors
        clen = len(colors)
        for q in xrange(self.getNumLEDS()):
            k = k + 1 if k + 1 < clen else 0
            a.append(colors[k])
        self.a = a
        self._i = iter(self.x)
        
    def run(self):

        i = self._i.next()
        #print(self.colors[self.k][0], self.colors[self.k][1], self.colors[self.k][2])
        self.setLED(self.f + i, self.a[i])
        self.sleep(self.wait)

        if i +1 == self.lenx:
            self.finished()

        return

class centerSweep(Animation):
    def __init__(self, colors, reverse = False, wait = 2):
        Animation.__init__(self)
        if not isinstance(colors, list):
            colors = [colors]

        self.of = reverse
        self.wait = wait

        self.first_run = True

    def pre_run(self):
        a = []
        b = (self.getNumLEDS()%2)
        c = self.getNumLEDS()/2
        if b:
            a.append(c)
            a.append(c)
        for x in xrange(c):
            if self.of:
                a.append(c + x + b)
                a.append(c - x - 1)
            else:
                a.append(c - x - 1)
                a.append(c + x + b)

        self.a = a

    def init(self):
        if self.first_run:
            self.pre_run()
            self.first_run = False

        k = -1
        b = range(len(self.a/2) + (self.getNumLEDS()%2))
        colors = self.colors
        clen = len(colors)

        for d in xrange(len(b)):
            k = k + 1 if k + 1 < clen else 0
            b[d] = colors[k]

        self.lenx = len(self.a) - 1
        if self.of:
            self._i = reversed(self.a)
            self.b = b
        else:
            self._i = iter(self.a)
            self.b = b[::-1]

    def run(self):
        i = self._i.next()
        color = self.b[i]
        self.setLED(i, color)
        i = self._i.next()
        self.setLED(i, color)

        if i == self.lenx:
            self.finished()

        self.sleep(self.wait)

class shift(Animation):
    def __init__(self, step = 1, cycles = 1, wait = 0):
        Animation.__init__(self)
        self.step = -step
        self.maxcycles = cycles
        self.wait = wait

    def init(self):
        self.cycles = iter(xrange(self.maxcycles))
        self.d = self.getStream()
        return

    def run(self):
        s = self.cycles.next() + 1

        self.d = self.d[self.step * 3:] + self.d[:self.step * 3]
        self.setStream(self.d)

        if s == self.maxcycles:
            self.finished()
        else:
            self.sleep(self.wait)
        return

class colorfade(Animation):
    def __init__(self, colors, wait = 0):
        Animation.__init__(self)
        if not isinstance(colors, list):
            raise TypeError('First Argument must be a list of colors')

        self.colors = colors
        self.wait = wait
        return

    def init(self):
        self.d = bytearray(self.colors[0])
        self.colorcycle = enumerate(iter(self.colors))
        self.state = 0
        return

    def run(self):
        if self.state == 0:
            self.ncolor, self.ccolor = self.colorcycle.next()
            self.ncolor += 1
            self.rdif = abs(self.ccolor[0] - self.d[0])
            self.gdif = abs(self.ccolor[1] - self.d[1])
            self.bdif = abs(self.ccolor[2] - self.d[2])

            self.rd = 1 if (self.ccolor[0] > self.d[0]) else -1
            self.gd = 1 if (self.ccolor[1] > self.d[1]) else -1
            self.bd = 1 if (self.ccolor[2] > self.d[2]) else -1

            self.state = 1

        if self.state == 1:
            if self.rdif != 0 or self.gdif != 0 or self.bdif != 0:
                if self.rdif != 0:
                    self.d[0] += self.rd
                    self.rdif -= 1
                
                if self.gdif != 0:
                    self.d[1] += self.gd
                    self.gdif -= 1

                if self.bdif != 0:
                    self.d[2] += self.bd
                    self.bdif -= 1
            
            else:
                self.state = 0

            self.fill(self.d)



        if self.ncolor == len(self.colors):
            self.finished()
        else:
            self.sleep(self.wait)
        
        return

class burstSweep(AnimationGroup):
    def __init__(self, colors, cycles = 1, direction = 1, wait = 5):
        AnimationGroup.__init__(self)

        if not isinstance(colors, list):
            colors = [colors]

        self.color = color
        self.direction = direction
        self.wait = wait
        self.repeat(cycles)

        self.first_run = True

    def init(self):
        AnimationGroup.init(self)
        self.clearAnimations()
       
        for c in self.colors:
            darkColor = filter_pixel(c, 0.7)
            self.add(LED.fill(colors = bytarray(c) + (darkColor * (self.getNumLEDS() - 2))))
            self.add(LED.shift(step = self.direction, cycles = self.getNumLEDS(), wait = self.wait))
            self.add(LED.shift(step = -1 * self.direction, cycles = self.getNumLEDS(), wait = self.wait))


class wave(AnimationGroup):
    def __init__(self, colors, cycles = 1, wait = 5):
        AnimationGroup.__init__(self)
        if not isinstance(colors, list):
            colors = [colors, colors]

        self.cycles = cycles
        self.colors = colors
        self.wait = wait

    def init(self):
        AnimationGroup.init(self)
        self.clearAnimations()

        if len(self.colors) > self.getNumLEDS():
            self.colors = self.colors[:self.getNumLEDS() - 1]

        steps = self.getNumLEDS() / len(self.colors)
        steps = [steps for _ in self.colors]
        steps[randint(0, len(steps)-1)] += (self.getNumLEDS() % len(self.colors))
        
        rd = []
        gd = []
        bd = []

        for i, c in enumerate(self.colors[:-1]):
            rdif = abs(c[0] - self.colors[i+1][0]) * 1.0
            gdif = abs(c[1] - self.colors[i+1][1]) * 1.0
            bdif = abs(c[2] - self.colors[i+1][2]) * 1.0
            rd.append(((1 if (c[0] < self.colors[i+1][0]) else -1) * rdif) / steps[i])
            gd.append(((1 if (c[1] < self.colors[i+1][1]) else -1) * gdif) / steps[i])
            bd.append(((1 if (c[2] < self.colors[i+1][2]) else -1) * bdif) / steps[i])

        rdif = abs(self.colors[-1][0] - self.colors[0][0]) * 1.0
        gdif = abs(self.colors[-1][1] - self.colors[0][1]) * 1.0
        bdif = abs(self.colors[-1][2] - self.colors[0][2]) * 1.0
        rd.append(((1 if (self.colors[-1][0] < self.colors[0][0]) else -1) * rdif) / steps[-1])
        gd.append(((1 if (self.colors[-1][1] < self.colors[0][1]) else -1) * gdif) / steps[-1])
        bd.append(((1 if (self.colors[-1][2] < self.colors[0][2]) else -1) * bdif) / steps[-1])

        colors = list()

        for x, c in enumerate(self.colors):
            colors += [[int(c[0] + rd[x] * i),
                        int(c[1] + gd[x] * i),
                        int(c[2] + bd[x] * i)] for i in xrange(steps[x])]

        start = randint(0, len(colors)-1)
        colors = colors[start:] + colors[:start]
        self.add(sweep(colors = colors, wait = self.wait))
        self.add(shift(cycles = self.cycles * self.getNumLEDS(), wait = self.wait))


class wait(Animation):
    def __init__(self, wait):
        Animation.__init__(self)
        self.wait = wait
    def init(self):
        self.sleep(self.wait)
    