# inspired by https://andrew.wang-hoyer.com/experiments/chaos-game

# requirements -- Matplotlib

FIG_SIZE = 10
DPI = 100
FILE_NAME, FILE_FORMAT = "chaos_game", "png"

from random import randint, random
import matplotlib.pyplot as plt
from math import sin, cos, pi 

def lcyc(N, n, k):
    return ((n >> (N-k)) | (n << k)) & ((1 << N) - 1)

class Transformation:
    def __init__(self, scale=0.5, rotation=0, prob=1):
        self.scale = scale
        self.rotation = rotation
        self.prob = prob

    def transform(self, p1, p2):
        p2n = (p2[0]-p1[0], p2[1]-p1[1])
        p2n = (self.scale*p2n[0], self.scale*p2n[1])
        p2n = (
            p2n[0]*cos(self.rotation) - p2n[1]*sin(self.rotation),
            p2n[0]*sin(self.rotation) + p2n[1]*cos(self.rotation)
        )
        p2n = (p2n[0]+p1[0], p2n[1]+p1[1])

        return p2n

class ChaosGame:

    def __init__(
        self, 
        *, 
        quality="rough", 
        num_targets=6,
        transformations=[
            Transformation(scale=0.5, rotation=0)   
        ],
        coloring=[(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    ):
        self.point_size = {
            "rough": 1,
            "low": 0.5,
            "medium": 0.2,
            "fine": 0.05
        }[quality] if type(quality) == str else quality
        self.num_targets = num_targets
        self.transformations = transformations
        self.coloring = coloring
        plt.ion() 
        self.fig, self.ax = plt.subplots(figsize=(FIG_SIZE, FIG_SIZE))
        self.ax.axis('off')
        self.ax.set_aspect('equal')
        self.fig.patch.set_facecolor('black')
        self.vertices = [(cos(2*pi/num_targets*i), sin(2*pi/num_targets*i)) for i in range(num_targets)] if num_targets % 2 == 0 else [(cos(pi/2 - 2*pi/num_targets*i), sin(pi/2 - 2*pi/num_targets*i)) for i in range(num_targets)]
        self.ax.scatter(*zip(*self.vertices), color='black', s=self.point_size, linewidths=0)
        self.points=[(0, 0)]
        self.colors=[]

    def choose_transform(self, *args):
        p = random()
        for i in range(len(self.transformations)):
            if p < self.transformations[i].prob:
                return self.transformations[i]
            p -= self.transformations[i].prob

    def choose_vertex(self):
        return randint(0, self.num_targets-1)

    def generate_points(self, n = 1000000, draw=True):
        self.points=self.points[-1:]
        self.colors=[]

        self.verts = [0, 0, 0]

        for _ in range(n):
            self.verts = self.verts[1:] + [self.choose_vertex()]
            last_vert = self.vertices[self.verts[-1]]
            trans = self.choose_transform(last_vert)
            self.points.append(trans.transform(self.points[-1], last_vert))

        for point in self.points:
            point = ((point[0]+1)/2, (point[1]+1)/2)
            color = [
                ((self.coloring[0][i] * (1 - point[1]) + self.coloring[1][i] * point[1]) * point[0] + 
                (self.coloring[2][i] * (1 - point[1]) + self.coloring[3][i] * point[1]) * (1 - point[0])) / 256
                for i in range(3)
            ]
            color=tuple(color)

            self.colors.append(color)

        self.ax.scatter(*zip(*self.points), c=self.colors, s=self.point_size, linewidths=0)
        if draw:
            plt.draw()
            plt.pause(0.01)

class ChaosGameHistExc(ChaosGame):

    def __init__(self, hist_len=1, excluded=[0,0,0,0,0,0], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.excluded = sum(2**i for i in excluded)
        self.hist_len = hist_len

    def choose_vertex(self):
        exc = 0
        for _ in self.verts[-self.hist_len:]:
            exc |= lcyc(self.num_targets, self.excluded, self.verts[-1])
        
        verts_avail = [i for i in range(self.num_targets) if not (exc & (1 << i))]

        return verts_avail[randint(0, len(verts_avail)-1)]
    
class ChaosGameHistExc2(ChaosGame):
    
    def __init__(self, excluded=[], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.excluded = sum(2**i for i in excluded) if len(excluded) > 0 else 0

    def choose_vertex(self):
        if self.verts[-1] == self.verts[-2]:
            exc = lcyc(self.num_targets, self.excluded, self.verts[-1]) 
            verts_avail = [i for i in range(self.num_targets) if not (exc & (1 << i))]
            return verts_avail[randint(0, len(verts_avail)-1)]
        
        return randint(0, self.num_targets-1)

class ChaosGameTargetTransform(ChaosGame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def choose_transform(self, vert):
        return self.transformations[vert]


cg = ChaosGameHistExc2( # OR ChaosGameHistExc OR ChaosGameTargetTransform
    quality='fine', # presets: ['rough', 'low', 'medium', 'fine'] or enter specific point size
    num_targets=6, # number of vertices, ideally 3-12
    transformations=[
        Transformation(scale=0.5, rotation=0, prob=0.5), # list of transformations
        Transformation(scale=0.6, rotation=pi/3, prob=0.5) # probabilities should sum to 1
    ], # if TargetTransform, num trans = num vertices 
    coloring=[(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)],
    # ^^ 4 cornered colors: [top-left, top-right, bottom-left, bottom-right] 
    excluded=[1, 3, 5] # list of excluded vertices [variations, based on history] (if applicable)
    # hist_len=1 # for ChaosGameHistExc, length of history to consider 
)

cg.generate_points(1500000) # 1000000 by default

while True:
    x = input("Add more points? (If so, enter number, else enter 'n'): ")
    if x == "n":
        break 
    if not x.isnumeric(): 
        continue 
    cg.generate_points(int(x))
    
# plt.savefig(f"{FILE_NAME}.{FILE_FORMAT}", dpi=DPI, format=FILE_FORMAT)
input()
    
