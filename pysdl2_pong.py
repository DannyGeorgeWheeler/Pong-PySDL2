import sys
import sdl2
import sdl2.ext
import random

# Global Constants
FOREGROUND = sdl2.ext.Color(255, 255, 255)
BACKGROUND = sdl2.ext.Color(0,0,0,255)
GAME_WIDTH = 800
GAME_HEIGHT = 800
LAST_UPDATE = sdl2.SDL_GetTicks()
BALL_SPEED = 7
BASE_FORCE = 30

# number pixel values stored in hex for scoreboard
NUMBERS = {
    0: [0xF, 0x9, 0x9, 0x9, 0xF],
    1: [0x2, 0x6, 0x2, 0x2, 0x7],
    2: [0xF, 0x1, 0xF, 0x8, 0xF],
    3: [0xF, 0x1, 0xF, 0x1, 0xF],
    4: [0x9, 0x9, 0xF, 0x1, 0x1],
    5: [0xF, 0x8, 0xF, 0x1, 0xF],
    6: [0xF, 0x8, 0xF, 0x9, 0xF],
    7: [0xF, 0x1, 0x2, 0x4, 0x4],
    8: [0xF, 0x9, 0xF, 0x9, 0xF],
    9: [0xF, 0x9, 0xF, 0x1, 0xF],
}

# Renderer System
class SoftwareRenderer(sdl2.ext.SoftwareSpriteRenderSystem):
    def __init__(self, window):
        self.match = None
        self.window = window
        super(SoftwareRenderer, self).__init__(window)

    # Modifies the default renderer to show a black screen
    def render(self, components):
        sdl2.ext.fill(self.surface, BACKGROUND)
        # sdl2.SDL_RenderDrawPoint
        # sdl2.ext.draw()

        for y in range(0, GAME_HEIGHT, 25):
            #sdl2.ext.line(self.surface, FOREGROUND, (400, y, 400, y + 15))
            sdl2.ext.fill(self.surface, FOREGROUND, (398, y, 4, 15))
        
        self.renderScore(0, self.match.score[1])
        self.renderScore(1, self.match.score[0])
                
        super(SoftwareRenderer, self).render(components)

    def renderScore(self, player2, number):
        pixels = sdl2.ext.pixels3d(self.surface)
        if player2: xmodifier = 340
        else: xmodifier = 420
        for row, byte in enumerate(NUMBERS[number]):
            bits = "{0:04b}".format(int(byte))
            for col, bit in enumerate(bits):
                x = (col * 10) + xmodifier
                y = (row * 10) + 50
                if bit == '1':
                    pixels[x:x+10,y:y+10] = FOREGROUND
                else:
                    pixels[x:x+10,y:y+10] = BACKGROUND



# Takes care of moving items around by applying velocity to their current position and
# manages the bounds of item's movement.
# An Applicator (enhanced System) loops through the components that are passed to it
# through the world.process() call (componentsets).
class MovementSystem(sdl2.ext.Applicator):
    def __init__(self, minx, miny, maxx, maxy):
        super(MovementSystem, self).__init__()
        self.componenttypes = Velocity, sdl2.ext.Sprite
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

    # Note- Only entities that contain all attributes (components) will be processed
    # In this case, the velocity attribute is required!
    def process(self, world, componentsets):
        for velocity, sprite in componentsets:
            swidth, sheight = sprite.size

            # Applies movement to the sprite based on the velocity attribute
            sprite.x += int(velocity.vx)
            sprite.y += int(velocity.vy)

            # Boundary Check
            # Ensure the sprite doesn't go beyond the left/top of the window
            sprite.x = max(self.minx, sprite.x)
            sprite.y = max(self.miny, sprite.y)
            # Ensure the sprite doesn't go beyond the right/bottom of the window
            pmaxx = sprite.x + swidth
            pmaxy = sprite.y + sheight
            if pmaxx > self.maxx:
                sprite.x = self.maxx - swidth
            if pmaxy > self.maxy:
                sprite.y = self.maxy - sheight

# System to detect the force change of an entity with momentum and calculate the velocity
class MomentumSystem(sdl2.ext.Applicator):
    def __init__(self):
        super(MomentumSystem, self).__init__()
        self.componenttypes = Velocity, Force
        self.lastUpdate = sdl2.SDL_GetTicks()
    
    def process(self, world, componentsets):
        # count the time since the last frame to use in
        # acceleration calculations
        current = sdl2.SDL_GetTicks()
        dT = (current - self.lastUpdate) / 1000
        # print(dT)
        self.lastUpdate = current
        # check for the state of the force attribute and apply
        # the acceleration calculation to the velocity
        for velocity, f in componentsets:
            if f.force < 0:
                if velocity.vy < velocity.min:
                    velocity.vy -= f.force * dT
                else:
                    velocity.vy += f.force * dT
            elif f.force > 0:
                if velocity.vy > velocity.max:
                    velocity.vy -= f.force * dT
                else:
                    velocity.vy += f.force * dT
            else:
                if velocity.vy > 0:
                    velocity.vy -= BASE_FORCE/2 * dT
                elif velocity.vy < 0:
                    velocity.vy += BASE_FORCE/2 * dT


# System to detect the collision of the ball with other entities
class CollisionSystem(sdl2.ext.Applicator):
    def __init__(self, minx, miny, maxx, maxy):
        super(CollisionSystem, self).__init__()
        self.componenttypes = Velocity, sdl2.ext.Sprite
        self.ball = None
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy

    # determine wether the item parameter is overlapping the ball    
    def _overlap(self, item):
        pos, sprite = item
        if sprite == self.ball.sprite:
            return False
        
        left, top, right, bottom = sprite.area
        bleft, btop, bright, bbottom = self.ball.sprite.area

        return (bleft < right and bright > left and
                btop < bottom and bbottom > top)

    # loops through the entities and checks whether they are overlapping with the ball,
    # if they are, the velocity of the ball is inverted so that it changes direction (bounces off entity)
    def process(self, world, componentsets):
        # checks if any entities (paddles) are overlapping with the ball
        collitems = [comp for comp in componentsets if self._overlap(comp)]
        if collitems:
            self.ball.velocity.vx = -self.ball.velocity.vx
            # calculate where the ball hit the paddle using their centers and change the rebound angle
            # appropriately. The outer edges of the paddle cause a more extreme angle of return for the ball.
            sprite = collitems[0][1]
            ballCenterY = self.ball.sprite.y + self.ball.sprite.size[1] // 2
            halfHeight = sprite.size[1] // 2
            stepSize = halfHeight // 10
            degrees = 0.7
            paddleCenterY = sprite.y + halfHeight
            if ballCenterY < paddleCenterY:
                factor = (paddleCenterY - ballCenterY) // stepSize
                self.ball.velocity.vy = -int(round(factor * degrees))
            elif ballCenterY > paddleCenterY:
                factor = (ballCenterY - paddleCenterY) // stepSize
                self.ball.velocity.vy = int(round(factor * degrees))
            else:
                self.ball.velocity.vy = - self.ball.velocity.vy
        # checks if the ball has reached the upper/lower bounds of the window and inverts the 
        # y velocity. (rebounds the ball off the top or bottom)
        if self.ball.sprite.y in (self.miny, self.maxy - self.ball.sprite.size[1]):
            self.ball.velocity.vy = - self.ball.velocity.vy
        # check if the ball gets passed a paddle.  SHOULD SCORE POINT AND RESET!        
        if self.ball.sprite.x in (self.minx, self.maxx - self.ball.sprite.size[0]):
            self.ball.sprite.position = (GAME_WIDTH // 2 - 20 // 2), (GAME_HEIGHT // 2 - 20 // 2)
            self.ball.velocity.vx = - self.ball.velocity.vx
            self.ball.velocity.vy = random.randint(-2, 2)


# A system that controls the AI player
class TrackingAIController(sdl2.ext.Applicator):
    def __init__(self, miny, maxy):
        super(TrackingAIController, self).__init__()
        self.componenttypes = PlayerData, Velocity, Force, sdl2.ext.Sprite
        self.miny = miny
        self.maxy = maxy
        self.ball = None
    
    def process(self, world, componentsets):
        for pdata, vel, f, sprite in componentsets:
            if not pdata.ai:
                continue
            
            ballX = self.ball.sprite.x
            ballY = self.ball.sprite.y + self.ball.sprite.size[1]
            ballVelX = self.ball.velocity.vx
            ballVelY = self.ball.velocity.vy
            paddleY = sprite.y + sprite.size[1] // 2
            XToBall = sprite.x - ballX

            if ballVelX < 0:
                # the ball is moving away from AI player
                # move towards the center of Y axis
                if paddleY < (self.maxy // 2) - 30:
                    f.force = BASE_FORCE
                elif paddleY > (self.maxy // 2) + 30:
                    f.force = - BASE_FORCE
                else:
                    f.force = 0

            else:
                # the ball is moving towards the AI player
                targetY = ((XToBall/ballVelX)*ballVelY)+ballY

                if XToBall < GAME_WIDTH * 0.75:     
                    # this conditional is to implement an AI delay #toogood
                    momentumAdjustment = 30

                    if targetY > GAME_HEIGHT:
                        targetY -= (abs(targetY) - GAME_HEIGHT) * random.uniform(1.5, 2.5)
                    elif targetY < 0:
                        targetY += abs(targetY) * random.uniform(1.3, 2.8)

                    if targetY > paddleY + momentumAdjustment:
                        f.force = BASE_FORCE
                    elif targetY < paddleY - momentumAdjustment:
                        f.force = - BASE_FORCE
                    else:
                        f.force = 0
                else:
                    f.force = 0
                
                # dash for out of reach balls
                # YToTarget = targetY - paddleY
                # if targetY < paddleY:

                #     if YToTarget > XToBall < GAME_WIDTH * 0.25:
                #         if YToTarget > 0:
                #             if 0 < vel.vy < vel.max:
                #                 vel.vy += 7
                #             print('dashed! DOWN')
                #         else:
                #             if 0 > vel.vy > vel.min:
                #                 vel.vy -= 7
                #                 print('dashed! UP')


# A system that keeps track of each players score
class ScoreTracker(sdl2.ext.Applicator):
    def __init__(self, minx, maxx):
        super(ScoreTracker, self).__init__()
        self.componenttypes = ()
        self.ball = None
        self.match = None
        self.scoreBoard = None
        self.minx = minx
        self.maxx = maxx
    
    def process(self, world, components):
        # check if the ball gets passed a paddle and a point is scored
        if self.ball.sprite.x == self.minx:
            self.match.score[1] += 1
        elif self.ball.sprite.x == self.maxx - self.ball.sprite.size[0]:
            self.match.score[0] += 1


# A simple 'data bag' that contains no logic (attribute/component)
# information to represent movement in a certain direction
# Enables an entity to be moveable by adding or removing a velocity attribute to them
class Velocity(object):
    def __init__(self):
        super(Velocity, self).__init__()
        self.vx = 0
        self.vy = 0
        self.max = 8
        self.min = -8     

class Force(object):
    def __init__(self):
        super(Force, self).__init__()
        self.force = 0  

# An object that tracks data about the player entity
class PlayerData(object):
    def __init__(self):
        super(PlayerData, self).__init__
        self.ai = False
        self.points = 0

# An object that tracks data about the current match
class MatchState(object):
    def __init__(self):
        super(MatchState, self).__init__
        self.score = [0, 0]
        self.rally = 0
        self.winCondition = 5

# Simple Entity component classes to represent the players and the ball
class Player(sdl2.ext.Entity):
    def __init__(self, world, sprite, posx=0, posy=0, ai=False):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()
        self.force = Force()
        self.playerdata = PlayerData()
        self.playerdata.ai = ai

class Ball(sdl2.ext.Entity):
    def __init__(self, world, sprite, posx=0, posy=0):
        self.sprite = sprite
        self.sprite.position = posx, posy
        self.velocity = Velocity()


# Run the game
def run():
    # create and show the window 
    sdl2.ext.init()
    window = sdl2.ext.Window("The Pong Game", size=(GAME_WIDTH, GAME_HEIGHT))
    window.show()

    # create the game world
    world = sdl2.ext.World()
    # create the world systems
    spriteRenderer = SoftwareRenderer(window)
    movement = MovementSystem(0, 0, GAME_WIDTH, GAME_HEIGHT)
    momentum = MomentumSystem()
    collision = CollisionSystem(0, 0, GAME_WIDTH, GAME_HEIGHT)
    aicontroller = TrackingAIController(0, GAME_HEIGHT)
    score = ScoreTracker(0, GAME_WIDTH)

    # add systems to the world
    world.add_system(spriteRenderer)
    world.add_system(movement)
    world.add_system(momentum)
    world.add_system(score)
    world.add_system(collision)
    world.add_system(aicontroller)

    # create the sprites to render
    factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
    sp_paddle1 = factory.from_color(FOREGROUND, size=(20, 100))
    sp_paddle2 = factory.from_color(FOREGROUND, size=(20, 100))
    sp_ball = factory.from_color(FOREGROUND, size=(20,20))    

    # create the entities
    player1 = Player(world, sp_paddle1, 20, (GAME_HEIGHT // 2 - sp_paddle1.size[1] // 2))
    player2 = Player(world, sp_paddle2, (GAME_WIDTH - sp_paddle2.size[0] - 20), (GAME_HEIGHT // 2 - sp_paddle1.size[1] // 2), True)
    ball = Ball(world, sp_ball, (GAME_WIDTH // 2 - sp_ball.size[1] // 2), (GAME_HEIGHT // 2 - sp_ball.size[0] // 2))

    # give the ball a starting velocity and pass it to the collision system
    ball.velocity.vx = BALL_SPEED
    ball.velocity.vy = random.randint(-2,2)
    collision.ball = ball
    aicontroller.ball = ball
    score.ball = ball

    # create a match and pass it to the score system and renderer
    match = MatchState()
    score.match = match
    spriteRenderer.match = match  

    sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER)

    gameController = sdl2.SDL_GameControllerOpen(0)
    print(gameController)



    # create the event loop and listen for events
    running = True
    # set an initial value for the frame time counter
    while running:
        if not gameController:
            keyStates = sdl2.SDL_GetKeyboardState(None)
            if keyStates[sdl2.SDL_SCANCODE_UP]:
                player1.force.force = - BASE_FORCE
            elif keyStates[sdl2.SDL_SCANCODE_DOWN]:
                player1.force.force = BASE_FORCE
            else:
                player1.force.force = 0
                pass

        # loop through the events
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                sdl2.SDL_GameControllerClose(gameController)
                break
            # if event.type == sdl2.SDL_KEYDOWN:
            #     if event.key.keysym.sym == sdl2.SDLK_SPACE:
            #         if keyStates[sdl2.SDL_SCANCODE_DOWN]:
            #             player1.velocity.vy += 8
            #         elif keyStates[sdl2.SDL_SCANCODE_UP]:
            #             player1.velocity.vy -= 8
            if event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                if event.cbutton.button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN or event.cbutton.button == sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK:
                    player1.force.force = BASE_FORCE
                    print('down down')
                elif event.cbutton.button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                    print('up down')
                    player1.force.force = - BASE_FORCE
            if event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                if event.cbutton.button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                    player1.force.force = 0
                elif event.cbutton.button == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                    print('up up')
                    player1.force.force = 0

        # A short delay is added to stop the game running at full processor speed.
        # So the game runs a bit slower and the overall load on the CPU is less.
        sdl2.SDL_Delay(10)
        world.process()
    return 0

if __name__ == "__main__":
    sys.exit(run())

