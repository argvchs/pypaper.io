import os, sys

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["SDL_VIDEO_CENTERED"] = "1"
import pygame
import pygame.gfxdraw
from pygame.locals import *
import math, decimal
import random
from decimal import Decimal
import pyclipper
from functools import *
import socket, threading
import base64, gzip

pygame.init()
pygame.display.set_caption("Papar.IO")
screen = pygame.display.set_mode((1200, 750))
screenalpha = screen.convert_alpha()
RW, RH = RSIZE = screen.get_size()
W, H = SIZE = 2400, 2400
SW = SH = SSIZE = 120, 120
COLORS = pygame.color.THECOLORS
COLORLIST = [i for i in COLORS.values() if i != COLORS["black"]]
USEDCOLOR = []
POSAREA = 100
POSLIST = [
    (i, j) for i in range(POSAREA, W, POSAREA) for j in range(POSAREA, H, POSAREA)
]
USEDPOS = []
INF = Decimal("inf")
SPEED = 10
MAXDIST = 6
RADIUS = 10
HITBUFFER = 4
INITEDGE = 32
INITRADIUS = 50
IP, PORT = "localhost", 10002
FILESIZE = 1048576
BASES = []
IDKEY = os.urandom(16)


def autotry(fx):
    def inner(*args, **kwargs):
        try:
            return fx(*args, **kwargs)
        except:
            ...

    return inner


class attrdict(dict):
    __slots__ = ()
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


listmap = lambda *args, **kwargs: [*map(*args, **kwargs)]
tmap = lambda *args, **kwargs: (*map(*args, **kwargs),)
acround = lambda x: int(
    Decimal(x).quantize(Decimal("1"), rounding=decimal.ROUND_HALF_UP)
)
vadd = lambda a, b: (a[0] + b[0], a[1] + b[1])
vsub = lambda a, b: (a[0] - b[0], a[1] - b[1])
vmul = lambda a, b: (a[0] * b, a[1] * b)
vdiv = lambda a, b: (a[0] / b, a[1] / b)
vint = lambda x: tmap(int, x)
vdec = lambda x: tmap(Decimal, x)
vdecint = lambda x: vdec(vint(x))
vpint = lambda p: listmap(vint, p)
vpdec = lambda p: listmap(vdec, p)
vpdecint = lambda p: listmap(vdecint, p)
getdist = lambda a, b: Decimal((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2).sqrt()
ratio = lambda x, k: (Decimal(x[0] ** 2 + x[1] ** 2) / Decimal(k)).sqrt()
getvector = lambda x, k: vdiv(vdec(x), ratio(x, k))
moveto = lambda a, b, s: vadd(a, getvector(vsub(b, a), s))
additem = lambda a, x: (a.append(x), x)[1]
getcolor = lambda: additem(
    USEDCOLOR, random.choice([i for i in COLORLIST if not i in USEDCOLOR])
)
delcolor = autotry(lambda x: USEDCOLOR.remove(x))
getpos = lambda: additem(
    USEDPOS, random.choice([i for i in POSLIST if not i in USEDPOS])
)
isinarea = lambda x, a, r: a[0] - r <= x[0] <= a[0] + r and a[1] - r <= x[1] <= a[1] + r
usepos = lambda x: USEDPOS.extend(
    [i for i in POSLIST if isinarea(x, i, POSAREA) and not i in USEDPOS]
)
delpos = lambda x: [USEDPOS.remove(i) for i in USEDPOS if isinarea(x, i, POSAREA)]
vrange = lambda x, s, e: (
    s[0] if x[0] < s[0] else e[0] if x[0] > e[0] else x[0],
    s[1] if x[1] < s[1] else e[1] if x[1] > e[1] else x[1],
)
exports = lambda x: [exec(f"global {i};{i}=(None,)") for i in x]
decodemsg = lambda x: attrdict(
    [(i.split("=")[0], eval(i.split("=")[1])) for i in x.split("&")]
)
decodemsgs = lambda x: [
    decodemsg(i) for i in x[:-1].split("$")
]
encodemsg = lambda x: "&".join([f"{k}={v!r}" for k, v in x.items()]) + "$"
zip = lambda s: base64.b64encode(gzip.compress(bytes(s, "utf-8")))
unzip = lambda s: gzip.decompress(base64.b64decode(s)).decode()
pc = pyclipper.Pyclipper()
pco = pyclipper.PyclipperOffset()


def fps(_fps):
    def decorator(fx):
        pre = pygame.time.get_ticks()

        @wraps(fx)
        def inner(*args, **kwargs):
            nonlocal pre
            if pygame.time.get_ticks() - pre >= _fps:
                pre = pygame.time.get_ticks()
                return fx(*args, **kwargs)

        return inner

    return decorator


def pointinpolygon(x, p):
    cnt = 0
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        if a[1] == b[1]:
            continue
        if x[1] < min(a[1], b[1]):
            continue
        if x[1] >= max(a[1], b[1]):
            continue
        if (x[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) + a[0] > x[0]:
            cnt += 1
    return (cnt % 2) == 1


def circleinpolygon(x, p, r):
    if pointinpolygon(x, p):
        return True
    for i in range(len(p)):
        if lineincircle(p[i], p[(i + 1) % len(p)], x, r):
            return True
    return False


def lineincircle(x, y, o, r):
    if getdist(x, o) <= r or getdist(y, o) <= r:
        return True
    if x[0] == y[0]:
        a, b, c = 1, 0, -x[0]
    elif x[1] == y[1]:
        a, b, c = 0, 1, -x[1]
    else:
        a, b, c = x[1] - y[1], y[0] - x[0], x[0] * y[1] - x[1] * y[0]
    dis1 = (a * o[0] + b * o[1] + c) ** 2
    dis2 = (a * a + b * b) * r * r
    if dis1 > dis2:
        return False
    angle1 = (o[0] - x[0]) * (y[0] - x[0]) + (o[1] - x[1]) * (y[1] - x[1])
    angle2 = (o[0] - y[0]) * (x[0] - y[0]) + (o[1] - y[1]) * (x[1] - y[1])
    return angle1 > 0 and angle2 > 0


def getnearest(x, p):
    res, dist = None, INF
    for i in p:
        if getdist(i, x) <= dist:
            dist, res = getdist(i, x), i
    return res


def unionpolygon(*p):
    pc.AddPath(p[0], pyclipper.PT_CLIP, True)
    pc.AddPaths(p[1:], pyclipper.PT_SUBJECT, True)
    res = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    pc.Clear()
    return vpdec(res[0])


def diffpolygon(*p):
    pc.AddPath(p[0], pyclipper.PT_CLIP, True)
    pc.AddPaths(p[1:], pyclipper.PT_SUBJECT, True)
    res = pc.Execute(
        pyclipper.CT_DIFFERENCE, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO
    )
    pc.Clear()
    return listmap(vpdec, res)


def zoompolygon(p, x):
    pco.MiterLimit = 10
    pco.AddPath(p, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
    res = pco.Execute(x)
    pco.Clear()
    return vpdec(res[0])


class VObject:
    def __init__(self):
        self.destroyed = False

    def update(self):
        if self.destroyed:
            self.destroy()

    def destroy(self):
        self.destroyed = True
        self.update = lambda: ...


class Event(VObject):
    def __init__(self):
        super().__init__()
        self.KEYS = self.MOUSE = {}
        self.PREPOS = self.POS = pygame.mouse.get_pos()
        self.RELPOS = (0, 0)

    def update(self):
        for i in self.KEYS:
            if self.KEYS[i] == 2:
                self.KEYS[i] = 0
        for i in self.MOUSE:
            if self.MOUSE[i] == 2:
                self.MOUSE[i] == 0
        self.PREPOS = self.POS
        self.POS = pygame.mouse.get_pos()
        self.RELPOS = (self.PREPOS[0] - self.POS[0], self.PREPOS[1] - self.POS[1])
        for e in pygame.event.get():
            if e.type == KEYDOWN:
                self.KEYS[e.key] = 1
            if e.type == KEYUP:
                self.KEYS[e.key] = 2
            if e.type == MOUSEBUTTONDOWN:
                self.MOUSE[e.button] = 1
            if e.type == MOUSEBUTTONUP:
                self.MOUSE[e.button] = 2
            if e.type == QUIT:
                self.destroy()

    def key(self, x, k=1):
        try:
            if self.KEYS[x] == k:
                return True
            return False
        except:
            self.KEYS[x] = 0
            if not k:
                return True
            return False

    def mouse(self, x, k=1):
        try:
            if self.MOUSE[x] == k:
                return True
            return False
        except:
            self.MOUSE[x] = 0
            if not k:
                return True
            return False

    def pos(self):
        return self.POS

    def relpos(self):
        return self.RELPOS


class GObject(VObject):
    def __init__(self, pos, screen=screen):
        super().__init__()
        self.pos = pos
        self.screen = screen
        self.snapshot = pygame.Surface(SIZE, SRCALPHA)
        self.snapshot.fill((0,) * 4)
        self.snaps = {}
        self.showed = []
        self.layers = []
        self.maxlayer = 0

    def setpos(self, pos):
        self.pos = pos

    def setscreen(self, screen):
        self.screen = screen

    def clearsnap(self):
        self.snapshot = pygame.Surface(SIZE, SRCALPHA)
        self.snapshot.fill((0,) * 4)
        self.showed.clear()

    def updatesnap(self):
        for t, fx in self.snaps.items():
            if not t in self.showed:
                self.showed.append(t)
                fx()

    def addsnap(self, t, fx):
        try:
            self.showed.remove(t)
            self.clearsnap()
        except:
            ...
        self.snaps[t] = fx

    def removesnaps(self):
        self.snaps.clear()

    def update(self):
        super().update()
        self.updatesnap()

    def addlayer(self, x):
        self.layers.append(x)
        self.maxlayer += 1

    def addlayers(self, *x):
        self.layers.extend(x)
        self.maxlayer += len(x)

    def insertlayer(self, k, x):
        self.layers.insert(k, x)
        self.maxlayer += 1

    @autotry
    def paintlayer(self, x):
        self.layers[x]()

    def paint(self):
        for i in range(self.maxlayer):
            self.paintlayer(i)

    def destroy(self):
        super().destroy()
        self.updatesnap = lambda: ...
        self.paintlayer = lambda x: ...
        self.paint = lambda: ...
        self.maxlayer = 0
        self.removesnaps()
        self.clearsnap()
        self.layers.clear()


class GameMap(GObject):
    def __init__(self, pos=(0, 0)):
        super().__init__(pos, screen)
        self.display = pygame.Surface(SIZE)
        self.display.fill(COLORS["white"])
        self.objects = []
        self.maxlayer = 0

    def addobject(self, x):
        x.setscreen(self.display)
        self.objects.append(x)
        self.maxlayer = max(self.maxlayer, x.maxlayer)

    def update(self):
        self.display.fill(COLORS["white"])
        for i in self.objects:
            i.update()
        for i in self.objects:
            if i.destroyed:
                self.objects.remove(i)

    def paintlayer(self, x):
        for i in self.objects:
            i.paintlayer(x)

    def paint(self):
        for i in range(self.maxlayer):
            self.paintlayer(i)
        pygame.draw.rect(self.display, COLORS["red"], (0, 0, W, H), 1)
        smallmap = pygame.transform.smoothscale(self.display, SSIZE)
        self.screen.blit(self.display, self.pos)
        self.screen.blit(smallmap, vsub(RSIZE, SSIZE))
        pygame.draw.rect(self.screen, COLORS["black"], (*vsub(RSIZE, SSIZE), *SSIZE), 1)


class Base(GObject):
    def __init__(self, color, pos, screen=screen):
        super().__init__(pos, screen)
        BASES.append(self)
        self.pos = vdec(pos)
        self.nextpos = self.prepos = self.rnextpos = self.lastside = self.pos
        self.color = color
        self.points = []
        self.polygon = []
        for i in range(INITEDGE):
            self.polygon.append(
                vadd(
                    vdecint(
                        (
                            INITRADIUS * math.cos(2 * math.pi * i / INITEDGE),
                            INITRADIUS * math.sin(2 * math.pi * i / INITEDGE),
                        )
                    ),
                    self.pos,
                )
            )
        self.start = ()
        self.outside = self.outsideret = False
        self.outsidediffs = []
        self.addlayers(
            lambda: (
                pygame.gfxdraw.filled_polygon(self.screen, self.polygon, self.color),
                pygame.gfxdraw.aapolygon(self.screen, self.polygon, COLORS["black"]),
            ),
            lambda: (
                self.screen.blit(self.snapshot, (0, 0)),
                pygame.draw.aaline(self.screen, COLORS["black"], self.prepos, self.pos),
            ),
            lambda: (
                pygame.gfxdraw.filled_circle(
                    self.screen, *vint(self.pos), RADIUS, self.color
                ),
                pygame.gfxdraw.aacircle(
                    self.screen, *vint(self.pos), RADIUS, COLORS["black"]
                ),
            ),
        )

    def setpos(self, pos):
        self.nextpos = vdec(pos)
        self.rnextpos = vrange(self.nextpos, (0, 0), SIZE)

    def update(self):
        if getdist(self.pos, self.rnextpos) > SPEED // 2:
            self.pos = vrange(moveto(self.pos, self.nextpos, SPEED), (0, 0), SIZE)
        self.outsideret, self.outsidediffs = False, []
        outside = not circleinpolygon(self.prepos, self.polygon, HITBUFFER)
        if not outside:
            self.lastside = self.prepos
        if outside:
            if self.outside:
                if getdist(self.pos, self.prepos) > MAXDIST:
                    self.points.append(self.pos)
                    usepos(self.pos)
                    temp, self.points = self.points, []
                    [self.points.append(i) for i in temp if not i in self.points]
            else:
                self.start = getnearest(self.pos, self.polygon)
                self.points.append(self.start)
        elif self.outside:
            for i in self.points[1:]:
                if pointinpolygon(i, self.polygon):
                    self.points.remove(i)
            end = getnearest(self.pos, self.polygon)
            s, e = self.polygon.index(self.start), self.polygon.index(end)
            a = self.polygon[: s + 1] + self.points + self.polygon[e:]
            self.points.reverse()
            d = self.polygon[: e + 1] + self.points + self.polygon[s:]
            tmp = self.polygon
            self.polygon = unionpolygon(a, d)
            self.points.clear()
            self.removesnaps()
            self.clearsnap()
            self.outsideret = True
            self.outsidediffs = diffpolygon(tmp, self.polygon)
        self.outside = outside
        for b in BASES:
            if b != self and b.outsideret:
                for i in b.outsidediffs:
                    if len(i) > 2:
                        diffs = diffpolygon(i, self.polygon)
                        self.polygon = []
                        for j in diffs:
                            if pointinpolygon(vdecint(self.lastside), j):
                                self.polygon = j
                                break
                        else:
                            self.destroy()
        if getdist(self.pos, self.prepos) > MAXDIST:
            self.prepos = self.pos
            for b in BASES:
                for i in range(len(self.points) - 1):
                    if b is self and i >= len(self.points) - 2:
                        break
                    if lineincircle(
                        self.points[i], self.points[i + 1], b.prepos, HITBUFFER
                    ):
                        self.destroy()
                        return
        for i in range(len(self.points) - 1):
            if not (self.points[i], self.points[i + 1]) in self.snaps:
                self.addsnap(
                    (self.points[i], self.points[i + 1]),
                    lambda: pygame.draw.aaline(
                        self.snapshot,
                        COLORS["black"],
                        self.points[i],
                        self.points[i + 1],
                    ),
                )
        self.updatesnap()

    def destroy(self):
        for i in self.polygon:
            delpos(i)
        for i in self.points:
            delpos(i)
        super().destroy()
        BASES.remove(self)
        delcolor(self.color)


class Player(Base):
    def __init__(self):
        super().__init__(getcolor(), getpos())
        self.idkey = IDKEY
        self.areapos = self.pos
        self.pprepos = self.prepos
        self.nearpos = self.nextnearpos = (0, 0)
        self.preoutside = False
        self.insertlayer(
            2,
            lambda: (
                (
                    lambda: (
                        pygame.gfxdraw.aacircle(
                            self.screen, *vint(self.nearpos), 5, COLORS["darkgray"]
                        ),
                        pygame.draw.aaline(
                            self.screen, COLORS["gray"], self.nearpos, self.areapos
                        ),
                    )
                )()
                if self.preoutside
                else ...,
                pygame.gfxdraw.filled_circle(
                    self.screen, *vint(self.areapos), MAXDIST, (*self.color[:3], 128)
                ),
                pygame.gfxdraw.aacircle(
                    self.screen, *vint(self.areapos), MAXDIST, COLORS["black"]
                ),
            ),
        )

    def update(self):
        if self.outside:
            if not self.preoutside:
                self.nearpos = self.nextnearpos = self.pos
            if self.prepos != self.pprepos:
                self.nextnearpos = getnearest(self.prepos, self.polygon)
            if (dist := getdist(self.nearpos, self.nextnearpos)) > SPEED // 2:
                self.nearpos = moveto(self.nearpos, self.nextnearpos, dist)
        if getdist(self.areapos, self.prepos) > SPEED // 2:
            self.areapos = moveto(self.areapos, self.prepos, SPEED)
        self.pprepos = self.prepos
        self.preoutside = self.outside
        super().update()
        self.message = attrdict(
            idkey=self.idkey,
            color=self.color,
            polygon=self.polygon,
            points=self.points,
            pos=self.pos,
            prepos=self.prepos,
            outsideret=self.outsideret,
            outsidediffs=self.outsidediffs,
            destroyed=self.destroyed,
        )


class AI(Base):
    def __init__(self):
        super().__init__(getcolor(), getpos())
        self.poses = [self.pos]
        self.state = 0
        self.zoom = zoompolygon(self.polygon, 20)

    def update(self):
        self.setpos(self.poses[0])
        if getdist(self.pos, self.poses[0]) <= SPEED // 2:
            self.poses.pop(0)
            a = b = 0
            while b - a < 2:
                a = random.randint(0, len(self.polygon) - 1)
                b = random.randint(0, len(self.polygon) - 1)
            x = self.polygon[random.randint(a + 1, b - 1)]
            dist, point = INF, None
            for i in self.zoom:
                if getdist(i, x) <= dist:
                    dist = getdist(i, x)
                    point = i
            self.poses.extend([self.polygon[a], point, self.polygon[b]])
            self.zoom = zoompolygon(self.polygon, 200)
        super().update()


class Enemy(Base):
    def __init__(self, data):
        super().__init__(data.color, data.pos)
        self.idkey = IDKEY
        self.setdata(data)

    def setdata(self, data):
        self.idkey = data.idkey
        self.color = data.color
        self.polygon = data.polygon
        self.points = data.points
        self.pos = data.pos
        self.prepos = data.prepos
        self.outsideret = data.outsideret
        self.outsidediffs = data.outsidediffs
        self.destryed = data.destroyed

    def update(self):
        if self.destroyed:
            self.destroy()


class Network(VObject):
    def __init__(self, ip=IP, port=PORT):
        super().__init__()
        self.ip, self.port = ip, port
        self.idkeys = []
        self.sender = None
        self.lastmessage = None
        self.readers = {}
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.ip, self.port))
        except:
            self.destroy()

    def setsender(self, x):
        self.sender = x

    def startreceive(self):
        self.receiver = threading.Thread(target=self.receive)
        self.receiver.start()

    def update(self):
        if self.sender and not self.sender.destroyed:
            if self.lastmessage != (message := encodemsg(self.sender.message)):
                self.lastmessage = message
                self.client.send(zip(message))

    def receive(self):
        while 1:
            try:
                print("STATE: START")
                data = self.client.recv(FILESIZE)
                # print("STATE: GET DATA (", data, ")")
                msgs = decodemsgs(unzip(data))
                # data = decodemsg(self.client.recv(FILESIZE))
                for msg in msgs:
                    print("STATE: DECODE DATA (", msg, ")")
                    if msg.idkey == self.sender.idkey:
                        continue
                    print("STATE: CHECKSELF")
                    if not msg.idkey in self.idkeys:
                        self.readers.update({msg.idkey: Enemy(msg)})
                    else:
                        self.readers[msg.idkey].setdata(msg)
                    print("STATE: UPDATE")
                    if msg.destroyed:
                        self.readers.pop(msg.idkey)
                    print("STATE: SUCCESS")
            except Exception as err:
                print("ERR:", err)
                break
        print("DESTROYED")
        self.destroy()

    def destroy(self):
        super().destroy()
        self.readers.clear()
        self.client.close()


def main():
    @fps(10)
    def movemap():
        gmap.setpos(vint(vadd(vmul(player.pos, -1), (RW // 2, RH // 2))))
        player.setpos(vsub(event.pos(), gmap.pos))

    event = Event()
    clock = pygame.time.Clock()
    gmap = GameMap()
    player = Player()
    gmap.addobject(player)
    network = Network()
    network.setsender(player)
    network.startreceive()
    while 1:
        screen.fill(COLORS["skyblue"])
        event.update()
        if event.destroyed:
            break
        gmap.update()
        network.update()
        for i in gmap.objects:
            if not i in network.readers.values() and not i is player:
                gmap.objects.remove(i)
        for i in network.readers.values():
            if not i in gmap.objects:
                gmap.addobject(i)
        movemap()
        gmap.paint()
        pygame.display.update()
        clock.tick(90)
    gmap.destroy()
    network.destroy()
    pygame.quit()
    sys.exit()


main()
