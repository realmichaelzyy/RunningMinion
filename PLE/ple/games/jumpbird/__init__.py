import os
import sys
import numpy as np

import pygame
from pygame.constants import K_w
from pygame.locals import *
from .. import base

#MinionPlayer: the agent called Minion
class MinionPlayer(pygame.sprite.Sprite):

    def __init__(self, 
            SCREEN_WIDTH, SCREEN_HEIGHT, init_pos,
            image_assets, rng, color="red", scale=1.0):

        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT
        
        self.image_order = [0, 1, 2, 1]
        #done image stuff

        pygame.sprite.Sprite.__init__(self)
      
        self.image_assets = image_assets
       
        self.init(init_pos, color)
        
        self.height = self.image.get_height()
        self.scale = scale
        
        #all in terms of y
        self.vel = 0 
        self.FLAP_POWER = 18*self.scale
        self.MAX_DROP_SPEED = 10.0
        self.GRAVITY = 1.0*self.scale

        self.rng = rng

        self._oscillateStartPos() #makes the direction and position random
        self.rect.center = (self.pos_x, self.pos_y) #could be done better
    
    def init(self, init_pos, color):
        #set up the surface we draw the bird too
        self.flapped = False #start off w/ a flap
        self.current_image = 0
        self.color = color
        #self.image = self.image_assets[self.color][self.current_image]
        self.image = self.image_assets[self.current_image]
        self.rect = self.image.get_rect()
        self.thrust_time = 0.0 
        self.tick = 0
        self.pos_x = init_pos[0]
        #self.pos_y = init_pos[1]
        self.minion_ground = self.SCREEN_HEIGHT*0.615
        self.pos_y = self.minion_ground
        
    def _oscillateStartPos(self):
        offset = 8*np.sin( self.rng.rand() * np.pi )
        self.pos_y += offset

    def flap(self):
        if self.pos_y > -2.0*self.image.get_height() and self.pos_y>=self.minion_ground:
            self.vel = 0.0
            self.flapped = True

    def update(self, dt):
        self.tick += 1

        #image cycle
        if (self.tick + 1) % 5 == 0:
            self.current_image += 1

            if self.current_image >= 3:
                self.current_image = 0
           
            #set the image to draw with.
            #self.image = self.image_assets[self.color][self.current_image]
            self.image = self.image_assets[self.current_image]
            self.rect = self.image.get_rect()
      
        if self.vel < self.MAX_DROP_SPEED and self.thrust_time == 0.0:
            self.vel += self.GRAVITY

        #the whole point is to spread this out over the same time it takes in 30fps.
        if self.thrust_time+dt <= (1.0/30.0) and self.flapped and self.pos_y >= self.minion_ground:
            self.thrust_time += dt
            self.vel += -1.0*self.FLAP_POWER
        else:
            self.thrust_time = 0.0
            self.flapped = False

        self.pos_y += self.vel
        if self.pos_y < self.minion_ground:
            self.current_image = 3
            self.image = self.image_assets[self.current_image]
            self.rect = self.image.get_rect()

        if self.pos_y > self.minion_ground:
            self.pos_y = self.minion_ground
        self.rect.center = (self.pos_x, self.pos_y)

    def draw(self, screen):
        screen.blit(self.image, self.rect.center)

class Pipe(pygame.sprite.Sprite):
    
    def __init__(self, 
            SCREEN_WIDTH, SCREEN_HEIGHT, gap_start, gap_size, image_assets, scale,
            offset=0, color="green"):

        self.speed = 7.0*scale
        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT
        
        self.image_assets = image_assets
        self.obstacle = self.image_assets
        #done image stuff

        #self.width = self.image_assets["green"]["lower"].get_width()
        self.width = self.obstacle.get_width()
        pygame.sprite.Sprite.__init__(self)
        
        self.image = pygame.Surface((self.width, self.SCREEN_HEIGHT))
        self.image.set_colorkey((0,0,0))
        
        self.init(gap_start, gap_size, offset, color)

    def init(self, gap_start, gap_size, offset, color):
        self.image.fill((0,0,0))
        self.gap_start = gap_start
        self.x = self.SCREEN_WIDTH+self.width+offset
        
        #self.lower_pipe = self.image_assets[color]["lower"]
        #self.upper_pipe = self.image_assets[color]["upper"]
        
        #top_bottom = gap_start-self.upper_pipe.get_height()
        bottom_top = (gap_start+gap_size)*1.5
        self.y_top = bottom_top
        #self.image.blit(self.upper_pipe, (0, top_bottom ))
        #self.image.blit(self.lower_pipe, (0, bottom_top ))
        self.image.blit(self.obstacle,(0, bottom_top))
        
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.SCREEN_HEIGHT/2)

    def update(self, dt):
        self.x -= self.speed
        self.rect.center = (self.x, self.SCREEN_HEIGHT/2)

class Backdrop():

    def __init__(self, SCREEN_WIDTH, SCREEN_HEIGHT, image_background, image_base, scale):
        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT

        self.background_image =  image_background
        self.base_image = image_base

        self.x = 0
        self.speed = 4.0*scale 
        self.max_move = self.base_image.get_width() - self.background_image.get_width()
    
    def update_draw_base(self, screen, dt):
        #the extra is on the right
        if self.x > -1*self.max_move:
            self.x -= self.speed 
        else:
            self.x = 0
       
        screen.blit(self.base_image, (self.x, self.SCREEN_HEIGHT*0.81))

    def draw_background(self, screen):
        screen.blit(self.background_image, (0,0))

class RunningMinion(base.PyGameWrapper):
    """
    Used physics values from sourabhv's `clone`_.

    .. _clone: https://github.com/sourabhv/FlapPyBird


    Parameters
    ----------
    width : int (default: 288)
        Screen width. Consistent gameplay is not promised for different widths or heights, therefore the width and height should not be altered.

    height : inti (default: 512)
        Screen height.

    pipe_gap : int (default: 100)
        The gap in pixels left between the top and bottom pipes. 

    """
    
    def __init__(self, width=800, height=450, pipe_gap=100, gameMode="easy"):
        
        actions = {
            "up": K_w        
        }
       
        fps = 30
        
        base.PyGameWrapper.__init__(self, width, height, actions=actions)

        self.scale = 30.0/fps
    
        self.allowed_fps = 30 #restrict the fps
        self.gameMode=gameMode
        self.pipe_gap = 100
        self.pipe_color = "red"
        self.images = {}

        #so we can preload images
        pygame.display.set_mode((1,1), pygame.NOFRAME)
        pygame.display.set_caption("Running Minion")

        self.white  = 255,255,255
        self.red = 220,20,60
        pygame.font.init()
        self.myfont = pygame.font.Font(None, 60)

        self._dir_ = os.path.dirname(os.path.abspath(__file__))
        self._asset_dir = os.path.join( self._dir_, "assets/" )
        self._load_images()
        
        #self.pipe_width = self.images["pipes"]["green"]["lower"].get_width()
        #self.pipe_width = self.images["obstacle"].get_width()
        #self.pipe_offset_ratios = np.random.choice([1]+range(6, int(self.width/self.pipe_width)-3), 2, replace=False)
        #self.pipe_offsets = [0, self.pipe_width*self.pipe_offset_ratios[0], self.pipe_width*self.pipe_offset_ratios[1]]

        self.init_pos = (
                int( self.width * 0.2), 
                int( self.height / 2 )
        )

        # self.pipe_min = int(self.pipe_gap/4)  #25 Larger number indicates smaller pipe
        # self.pipe_max = int(self.height*0.79*0.6 - self.pipe_gap/2)#242 - 50

        self.pipe_min = self.height*0.18
        self.pipe_max = self.height*0.25

        self.backdrop = None
        self.player = None
        self.pipe_group = None
    
    def _load_images(self):
        #preload and convert all the images so its faster when we reset
        
        image_assets = [
            os.path.join( self._asset_dir, "minion-left.png"),
            os.path.join( self._asset_dir, "minion-mid.png"),
            os.path.join( self._asset_dir, "minion-right.png"),
            os.path.join( self._asset_dir, "minion-jump.png"),
        ]
        self.images["minion"]=[pygame.image.load(im).convert_alpha() for im in image_assets]
        
        
        self.images["background"] = {}
        for b in ["day", "night"]:
            path = os.path.join( self._asset_dir, "background-%s.jpg" % b )

            self.images["background"][b] = pygame.image.load(path).convert()
        
        
        self.images["obstacle"] = {}
        path = os.path.join(self._asset_dir, "obstacle.png")
        self.images["obstacle"]=pygame.image.load(path).convert_alpha()

        path = os.path.join( self._asset_dir, "base.jpg" )
        self.images["base"] = pygame.image.load(path).convert()

    def init(self):
        if self.backdrop is None:
            self.backdrop = Backdrop(
                    self.width,
                    self.height,
                    self.images["background"]["day"],
                    self.images["base"],
                    self.scale
                    )

        if self.player is None: 
            self.player = MinionPlayer(
                    self.width, 
                    self.height, 
                    self.init_pos, 
                    #self.images["player"],
                    self.images["minion"],
                    self.rng,
                    color="red",
                    scale=self.scale
                    )
        
        if self.pipe_group is None:
            self.pipe_group = pygame.sprite.Group([
                self._generatePipes(offset=-75),
                self._generatePipes(offset=-75+self.width/2),
                self._generatePipes(offset=-75+self.width*1),
                self._generatePipes(offset=-75+self.width*1.5),
                self._generatePipes(offset=-75+self.width*2)
            ])

        color = self.rng.choice(["day", "night"])
        self.backdrop.background_image = self.images["background"][color]
       
        #instead of recreating
        color = self.rng.choice(["red", "blue", "yellow"])
        self.player.init(self.init_pos, color)
    
        self.pipe_color = self.rng.choice(["red", "green"])
        #for i,p in enumerate(self.pipe_group):
        #    self._generatePipes(offset=self.pipe_offsets[i], pipe=p)
        
        
        self.pipe_width = self.images["obstacle"].get_width()
        #minimum ratio(number of pipe distance) between pipes
        self.min_dist_ratio = 4
        self.max_dist_ratio = int(self.width/self.pipe_width)+1
        self.avg_dist_ratio = 4
        
        if self.gameMode=="easy":
            self.pipe_offsets = [-75, -75+self.width*0.5,  -75+self.width*1.0,  -75+self.width*1.5,  -75+self.width*2]
        
        else:
            pipe_offset_ratios =[0] + sorted(np.random.choice(range(self.min_dist_ratio, self.max_dist_ratio), 2, replace=False))
            pipe_offset_ratios = pipe_offset_ratios + [np.random.choice([pipe_offset_ratios[2]+1] +[rr+max(pipe_offset_ratios[0]+self.max_dist_ratio, pipe_offset_ratios[2]+self.min_dist_ratio) for rr in range(0,self.avg_dist_ratio)])]
            pipe_offset_ratios = pipe_offset_ratios + [np.random.choice([pipe_offset_ratios[3]+1] +[rr+max(pipe_offset_ratios[1]+self.max_dist_ratio, pipe_offset_ratios[3]+self.min_dist_ratio) for rr in range(0,self.avg_dist_ratio)])]
        
            self.pipe_offset_ratios = pipe_offset_ratios
            self.pipe_offsets = [self.pipe_width*por for por in pipe_offset_ratios]
        
        
        for i,p in enumerate(self.pipe_group):
            self._generatePipes(offset=self.pipe_offsets[i], pipe=p)

        self.score = 0.0
        self.distance=0.0
        self.lives = 1
        self.tick = 0

    def getGameState(self):
       
        pipes = []
        #print len(self.pipe_group)
        #print 'new state'
        for p in self.pipe_group:
            #print p.x, self.player.pos_x
            if p.x > self.player.pos_x:
                pipes.append((p, p.x - self.player.pos_x))
              
        sorted(pipes, key=lambda p: p[1])

        next_pipe = pipes[0][0]
        #print len(pipes)
        if len(pipes)<2:
            next_next_pipe = next_pipe
        else:
            next_next_pipe = pipes[1][0]

        state = {
            "next_pipe_dist_to_player": next_pipe.x - self.player.pos_x,
            "next_pipe_top_y": next_pipe.gap_start,
            "next_pipe_bottom_y": next_pipe.gap_start+self.pipe_gap
        }
        #print state
        return state


    def getScore(self):
        return self.score

    def _generatePipes(self, offset=0, pipe=None):
        start_gap = self.rng.random_integers(    #decide y placement of pipe
                self.pipe_min,
                self.pipe_max
                #self.pipe_min*1.5
        )  

        if pipe == None:
            pipe = Pipe(
                        self.width, 
                        self.height,
                        start_gap, 
                        self.pipe_gap,
                        #self.images["pipes"],
                        self.images["obstacle"],
                        self.scale,
                        color=self.pipe_color,
                        offset=offset
                )
        
            return pipe
        else:
            pipe.init(start_gap, self.pipe_gap, offset, self.pipe_color)

    def _handle_player_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key
                if key == self.actions['up']:
                    self.player.flap()

    def game_over(self):
        return self.lives <= 0

    def step(self, dt):
        self.tick += 1
        dt = dt / 1000.0

        self.score += self.rewards["tick"]
        #handle player movement
        self._handle_player_events()
        #cc=0
        for p in self.pipe_group:
            # hit = pygame.sprite.spritecollide(self.player, self.pipe_group, False)
            # for h in hit:    #do check to see if its within the gap.
            #     top_pipe_check = ((self.player.pos_y - self.player.height/2) <= h.gap_start)
            #     bot_pipe_check = ((self.player.pos_y + self.player.height) > h.gap_start+self.pipe_gap)

            #     if top_pipe_check:
            #         self.lives = 1

            #     if bot_pipe_check:
            #         self.lives = 1

            #is it past the player?
            #p.x - 35 <=160< (p.x - 35 + )
            # if cc%3==0:
            #     print self.player.pos_y, p.y_top
            #     cc+=1
            if (p.x - p.width/2 -7) <= self.player.pos_x < (p.x - p.width/2 + 7):
                if self.player.pos_y + self.player.height/2 > p.y_top:
                    #print 'hit!!'
                    self.lives-=1
                    break
                self.score += 2*self.rewards["positive"]
                self.distance +=0.5

            #is out out of the screen?
            if p.x < -p.width:
                if self.gameMode=="easy":
                    self._generatePipes(offset=self.width*1.5, pipe=p)
                
                else:
                    #get the smallest and largest p in the rest of pipes
                    maxP = max(self.pipe_group, key=lambda p: p.x)
                    #print "maxP="+str(maxP.x)
                    minP = maxP
                    for pp in self.pipe_group:
                        if pp.x < minP.x and pp.x > p.x:
                            minP=pp
                    #print "minP="+str(minP.x)
                    #print "curretnP="+str(p.x)
                
                    new_offset=max(minP.x, maxP.x-self.width) + self.pipe_width * np.random.choice([0] + range(self.min_dist_ratio, self.min_dist_ratio+self.avg_dist_ratio))
                
                    self._generatePipes(offset=new_offset, pipe=p)
    
    

        # #fell on the ground
        # if self.player.pos_y >= 0.79*self.height - self.player.height:
        #     self.lives = 1

        # #went above the screen
        # if self.player.pos_y < -self.player.height:
        #     self.lives = 1

        self.player.update(dt)
        self.pipe_group.update(dt)

        if self.lives <= 0:
            self.score += self.rewards["loss"]
        if self.player.flapped==True:
            self.score += self.rewards["negative"]*0.2
        #draw part
        self.backdrop.draw_background(self.screen)
        self.pipe_group.draw(self.screen)
        self.backdrop.update_draw_base(self.screen, dt)
        self.player.draw(self.screen)
        #print_text(self.font1, 500, 0, "SCORE: " + str(self.score))
        self.textImage = self.myfont.render("SCORE: " + str(self.distance), True, self.red)
        self.screen.blit(self.textImage, (500,20))
