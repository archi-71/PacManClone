# Import modules and libraries
import pygame, time, random, sys, math
from pygame.locals import *

if sys.platform == "win32":
    import ctypes
    cytypes.windll.user32.SetProcessDPIAware()

WINDOW_WIDTH = 672
WINDOW_HEIGHT = 828

SCREEN_WIDTH = 672
SCREEN_HEIGHT = 864

# Initialise pygame, setup game clock, create game window
pygame.init()
clock = pygame.time.Clock()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF)
screen = pygame.surface.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man")

# Load sprites
titleImage = pygame.image.load("pacmanResources/pacmanTitle.png").convert_alpha()
titleImage = pygame.transform.scale(titleImage, (613, 190))

pacmanSpriteSheet = []
RpacmanImage = pygame.image.load("pacmanResources/pacman.png").convert_alpha()
LpacmanImage = pygame.transform.flip(RpacmanImage, True, False)
UpacmanImage = pygame.transform.rotate(RpacmanImage, 90)
DpacmanImage = pygame.transform.flip(UpacmanImage, False, True)
for rot in range(2):
    pacmanSpriteSheet.append([Rect((i * 39)*math.cos(math.radians(90*rot)), (i * 39)*math.sin(math.radians(90*rot)), 39, 39) for i in range(13)])

ghostImages = [pygame.image.load("pacmanResources/blinky.png").convert_alpha(), pygame.image.load("pacmanResources/pinky.png").convert_alpha(), pygame.image.load("pacmanResources/inky.png").convert_alpha(),pygame.image.load("pacmanResources/clyde.png").convert_alpha()]
ghostSpriteSheet = [[Rect((i * 84) + (j * 42), 0, 42, 42) for j in range(2)] for i in range(4)]

dizzyGhostImage = pygame.image.load("pacmanResources/dizzyGhost.png").convert_alpha()
dizzyGhostSpriteSheet = [[Rect((i * 84) + (j * 42), 0, 42, 42) for j in range(2)] for i in range(2)]

eatenGhostImage = pygame.image.load("pacmanResources/eatenGhost.png").convert_alpha()
eatenGhostSpriteSheet = [Rect(i * 42, 0, 42, 42) for i in range(4)]

wallImage = pygame.image.load("pacmanResources/walls.png").convert_alpha()
wallImage2 = pygame.image.load("pacmanResources/walls2.png").convert_alpha()
wallSpriteSheet = [Rect(i % 10 * 24, i // 10 * 24, 24, 24) for i in range(29)]

dotImage = pygame.image.load("pacmanResources/dot.png").convert_alpha()
powerPelletImage = pygame.image.load("pacmanResources/powerPellet.png").convert_alpha()
fruitImage = pygame.image.load("pacmanResources/fruit.png").convert_alpha()

# Load fonts
largeText = pygame.font.Font("pacmanResources/joystix monospace.ttf", 36)
smallText = pygame.font.Font("pacmanResources/joystix monospace.ttf", 24)

# Create and set timer events
timer1 = pygame.USEREVENT + 1
timer2 = pygame.USEREVENT + 2
timer3 = pygame.USEREVENT + 3
pygame.time.set_timer(timer1, 300)
pygame.time.set_timer(timer2, 100)
pygame.time.set_timer(timer3, 150)

phaseLengths = [7000, 27000, 34000, 54000, 59000, 79000, 84000, 999999999999]


# Helper function to find linear distance between 2 points
def distance(point1, point2):
    return ((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2) ** 0.5

class Level:
    
    def __init__(self):
        
        # Initialise game objects and establish global variables
        self.walls = []
        self.dots = []
        self.powerPellets = []
        self.ghosts = [Blinky(), Pinky(), Inky(), Clyde()]
        self.fruit = None
        self.freeze = True
        self.dizzyTimer = None
        self.fruitCount = 0
        self.phase = 0
        self.globalState = "scatter"
        self.levelStart = pygame.time.get_ticks()
        self.lives = 2
        self.score = 0
        self.won = None
        self.gameOver = None
        
        # Setup level from memory and initialise required objects
        with open('pacmanResources/pacmanLevel.txt', 'r') as file:
            grid = [[ID for ID in row.split(" ")] for row in file.read().split("\n")]
            for row in range(len(grid)):
                for column in range(len(grid[row])):
                    if grid[row][column].isnumeric():
                        self.walls.append(Wall(int(grid[row][column]), 24*column, 72 + 24*row))
                    elif grid[row][column] == ".":
                        self.dots.append(Dot(24*column, 72 + 24*row))
                    elif grid[row][column] == "*":
                        self.powerPellets.append(PowerPellet(24*column, 72 + 24*row))
   
    # Reset level (if pacman dies)
    def reset(self):
        self.won = None
        self.freeze = False
        self.dizzyTimer = None
        self.fruit = None
        self.phase = 0
        self.globalState = "scatter"
        self.levelStart = pygame.time.get_ticks()
        for ghost in self.ghosts:
            ghost.__init__()
    
    # Draw game objects each frame
    def draw(self):
        for wall in self.walls:
            wall.draw(self)
        for dot in self.dots:
            dot.draw()
        for pellet in self.powerPellets:
            if pellet.animFrame == 0:
                pellet.draw()
        for i in range(len(self.ghosts)):
            self.ghosts[i].draw(ghostImages[i], self)

class Pacman:
    
    def __init__(self):
        self.x = 315
        self.y = 615
        self.speed = 3
        self.moveState = None
        self.animFrame = 0
        self.direction = "R"
        self.dead = False
        self.streak = 0
    
    # Animate pacman based on timer
    def animate(self, level, ui, game):
        
        # Open/close mouth animation
        if not self.dead:
            if self.moveState:
                self.animFrame = (self.animFrame + 1) % 3
            else:
                self.animFrame = 1
        else:
            
            # Death animation
            if self.animFrame < 12:
                self.animFrame += 1
            else:
                
                # Trigger game over if no lives are left
                if level.lives == 0:
                    if not level.gameOver:
                        level.gameOver = pygame.time.get_ticks()
                        level.freeze = True
                else:
                    
                    # Reset game if pacman dies
                    level.lives -= 1
                    ui.reset()
                    self.reset()
                    level.reset()
                    level.draw()
                    self.draw(level)
                    ui.drawUI(level, game, True)
                    pygame.display.update()
                    pygame.time.wait(2000)
                    level.reset()
    
    # Move pacman
    def move(self, pressed_keys, level):
        
        # Change move state based on available tiles and user input
        options = self.calculateMoveOptions(level)
        if (pressed_keys[K_LEFT] or pressed_keys[K_a]) and "L" in options:
            self.moveState = self.direction = "L"
        elif (pressed_keys[K_RIGHT] or pressed_keys[K_d]) and "R" in options:
            self.moveState = self.direction = "R"
        elif (pressed_keys[K_UP] or pressed_keys[K_w]) and "U" in options:
            self.moveState = self.direction = "U"
        elif (pressed_keys[K_DOWN] or pressed_keys[K_s]) and "D" in options:
            self.moveState = self.direction = "D"
        else:
            if self.moveState not in options:
                self.moveState = None
        
        # Move pacman as dictated by current move state
        if self.moveState == "U":
            self.y -= self.speed
        elif self.moveState == "D":
            self.y += self.speed
        elif self.moveState == "L":
            self.x -= self.speed
        elif self.moveState == "R":
            self.x += self.speed
        
        # Check if pacman leaves screen, if so, move him to the other side
        if self.x <= -21:
            self.x = 651
        elif self.x >= 651:
            self.x = -21
    
    # Helper method to find valid tiles to move to
    def calculateMoveOptions(self, level):
        
        # Initially consider all 4 movements
        options = ["R", "L", "U", "D"]
        
        for wall in level.walls:
            
            # Eliminate invalid move options by checking for wall obstructions
            collider = pygame.Rect(wall.x,wall.y,24,24)
            if "U" in options and (collider.collidepoint((self.x+10,self.y+7)) or collider.collidepoint((self.x+32,self.y+7))):
                options.remove("U")
            if "D" in options and (collider.collidepoint((self.x+10,self.y+34)) or collider.collidepoint((self.x+32,self.y+34))):
                options.remove("D")
            if "L" in options and (collider.collidepoint((self.x+7,self.y+10)) or collider.collidepoint((self.x+7,self.y+32))):
                options.remove("L")
            if "R" in options and (collider.collidepoint((self.x+34,self.y+10)) or collider.collidepoint((self.x+34,self.y+32))):
                options.remove("R") 
        return options
    
    # Reset self (if dead)
    def reset(self):
        self.__init__()
    
    # Draw self with correct sprite based on current direction and animation frame
    def draw(self, level):
        if not level.gameOver:
            if self.direction == "R":
                screen.blit(RpacmanImage, (self.x, self.y), pacmanSpriteSheet[0][self.animFrame])
            elif self.direction == "L":
                screen.blit(LpacmanImage, (self.x, self.y), pacmanSpriteSheet[0][::-1][self.animFrame])
            elif self.direction == "D":
                screen.blit(DpacmanImage, (self.x, self.y), pacmanSpriteSheet[1][self.animFrame])
            elif self.direction == "U":
                screen.blit(UpacmanImage, (self.x, self.y), pacmanSpriteSheet[1][::-1][self.animFrame])

class UI:

    def __init__(self):
        self.textShow = 1000;
        self.points = []
        self.flash = True
    
    # Draw major UI elements
    def drawUI(self, level, game, ready):
        if game:
            
            # Draw "READY!" to screen when preparing to begin
            if ready:
                screen.blit(largeText.render("Ready!", True, (255,255,0)), (260,470))
                
            # Draw "YOU WIN!" to screen if won
            if level.won:
                screen.blit(largeText.render("You win!", True, (255,255,0)), (220,470))
                
            # Draw "GAME OVER" to screen if all lives lost
            if level.gameOver:
                screen.blit(largeText.render("Game Over", True, (255,255,0)), (202,470))
                
            # Draw current score to screen
            screen.blit(largeText.render("Score", True, (255,255,255)), (260,-5))
            screen.blit(largeText.render(str(level.score), True, (255,255,255)), (336 - 18 * len(str(level.score)),30))
            
            # Draw each remaining life to screen
            for i in range(level.lives):
                screen.blit(LpacmanImage, ((39 * (i+1)) + (10 * i), 820), pacmanSpriteSheet[0][::-1][1])
                
            # Remove point tooltip after 1 second has passed
            p = 0
            while p < len(self.points):
                screen.blit(smallText.render(str(self.points[p][0]), True, (255,255,255)), self.points[p][1])
                if self.points[p][2] + self.textShow < pygame.time.get_ticks():
                    self.points.remove(self.points[p])
                    p -= 1
                p += 1
        else:
            
            # Draw title and "Press any key to start" text on title screen
            screen.blit(titleImage, (30, 100))
            screen.blit(largeText.render("Press any key", True, (255,255,255)), (132,600))
            screen.blit(largeText.render("to start", True, (255,255,255)), (207,640))
            
            # Draw dashes based on continually alternating boolean to create blinking effect
            if self.flash:
                screen.blit(largeText.render("-", True, (255,255,255)), (67,620))
                screen.blit(largeText.render("-", True, (255,255,255)), (557,620))
    
    # Draw point-gain tooltip when ghost or fruit eaten
    def drawPoints(self, score, position):
        self.points.append((score, position, pygame.time.get_ticks()))
    
    # Reset UI if pacman dies
    def reset(self):
        self.points = []

# Base ghost class (common behaviour among all 4 ghosts)
class Ghost:
    
    # Animate ghost based on timer
    def animate(self):
        self.animFrame = (self.animFrame + 1) % 2
    
    # Initially wait in the ghost house (for Inky and Clyde)
    def wait(self, level):
        for wall in level.walls:
            collider = pygame.Rect(wall.x,wall.y,24,24)
            
            # Move up and down in the ghost house
            if self.direction == "U":
                if not collider.collidepoint((self.x+10,self.y-2)) or collider.collidepoint((self.x+32,self.y-2)):
                    self.y -= 0.002
                else:
                    self.direction = "D"
            elif self.direction == "D":
                if not collider.collidepoint((self.x+10,self.y+44)) or collider.collidepoint((self.x+32,self.y+44)):
                    self.y += 0.002
                else:
                    self.direction = "U"
    
    # Leave the ghost house at start of the game or after a retreat
    def leave(self):
        
        # Move to centre (for Inky and Clyde)
        if self.x > 315:
            self.direction = "L"
            self.x -= 1
        elif self.x < 315:
            self.direction = "R"
            self.x += 1
            
        # Move up (out of the ghost house)
        elif self.y > 327:
            self.direction = "U"
            self.y -= 1
        else:
            self.y = int(self.y)
            self.ghostHouse = False
            self.movement = 12
    
    # Enter ghost house during retreat after being eaten
    def enter(self, level):
        
        # Move down (into the ghost house)
        if self.y < 398:
            self.direction = "D"
            self.y += self.speed
            
        # Move left or right to initial starting positions (for Inky and Clyde)
        elif self.startX > 315 and self.x < self.startX:
            self.direction = "R"
            self.x += self.speed
        elif self.startX < 315 and self.x > self.startX:
            self.direction = "L"
            self.x -= self.speed
            
        # Respawn
        else:
            self.state = level.globalState
            self.speed = 2
            
    # Move ghost between tiles
    def move(self, target, level):
        if self.ghostHouse:
            
            # Enter ghost house
            if self.state == "eaten":
                self.enter(level)
                
            # Leave ghost house or wait inside
            else:
                if level.levelStart + self.waitTime > pygame.time.get_ticks():
                    self.wait(level)
                else:
                    self.leave()
        else:
            
            # If new tile not yet reached, continue moving in current direction
            if self.movement < 12:
                if self.direction == "R":
                    self.x += self.speed
                elif self.direction == "D":
                    self.y += self.speed
                elif self.direction == "U":
                    self.y -= self.speed
                elif self.direction == "L":
                    self.x -= self.speed
                self.movement += self.speed
            else:
                self.movement = 0
                
                # Check if ghost leaves screen, if so, move to the other side
                if self.x <= -21:
                    self.x = 651
                elif self.x >= 651:
                    self.x = -21
                else:
                    
                    # Get list of valid move options
                    options = self.calculateMoveOptions(level)
                    
                    # If dizzy, randomly choose a valid move
                    if self.state == "dizzy":
                        self.direction = random.choice(list(options))
                        
                    # If eaten, choose closest tile to the ghost house
                    elif self.state == "eaten":
                        self.speed = 6
                        self.calculateMove(options, (315, 327))
                        if self.x >= 312 and self.x <= 318 and self.y >= 324 and self.y <= 330:
                            self.ghostHouse = True
                            
                    # If only one move option, obviously choose that one
                    elif len(options) == 1:
                        self.direction = list(options)[0]
                        
                    # Otherwise, calculate optimum move to current target
                    else:
                        self.calculateMove(options, target)
    
    # Helper method to find valid tiles to move to
    def calculateMoveOptions(self, level):
        
        # Initially consider all 4 movements
        options = {"R": (self.x + 12, self.y), "L": (self.x - 12, self.y), "U": (self.x, self.y - 12), "D": (self.x, self.y + 12)}
        
        # Eliminate a move in the opposite direction (ghosts cannot move backwards)
        if self.direction == "L":
            options.pop("R")
        elif self.direction == "R":
            options.pop("L")
        elif self.direction == "U":
            options.pop("D")
        else:
            options.pop("U")
        for wall in level.walls:
            collider = pygame.Rect(wall.x,wall.y,24,24)
            
            # Eliminate invalid move options by checking for wall obstructions
            if "U" in options and (collider.collidepoint((self.x+10,self.y-2)) or collider.collidepoint((self.x+32,self.y-2))):
                options.pop("U")
            if "D" in options and (collider.collidepoint((self.x+10,self.y+44)) or collider.collidepoint((self.x+32,self.y+44))):
                options.pop("D")
            if "L" in options and (collider.collidepoint((self.x-2,self.y+10)) or collider.collidepoint((self.x-2,self.y+32))):
                options.pop("L")
            if "R" in options and (collider.collidepoint((self.x+44,self.y+10)) or collider.collidepoint((self.x+44,self.y+32))):
                options.pop("R")
        return options
    
    # Calculate the optimum move to reach a target location
    def calculateMove(self, options, target):
        shortest = 9999999999
        shortestRoutes = []
        for option in options:
            
            # If distance between target and a move option is the new lowest, store this move and update 'shortest'
            d = distance((options[option][0], options[option][1]), target)
            if d < shortest:
                shortest = d
                shortestRoutes = [{option: options[option]}]
            elif d == shortest:
                shortestRoutes.append({option: options[option]})
                
        # If there was one best move, take that one
        if len(shortestRoutes) == 1:
            self.direction = list(shortestRoutes[0])[0]
            
        # Otherwise, choose move based on the following the priorities: Up -> Left -> Down -> Right
        else:
            routes = [list(route)[0] for route in shortestRoutes]
            if "U" in routes:
                self.direction = "U"
            elif "L" in routes:
                self.direction = "L"
            elif "D" in routes:
                self.direction = "D"
            else:
                self.direction = "R"
    
    # Check for collision with pacman
    def hit(self, level, pacman, ui):
        if pygame.Rect(pacman.x, pacman.y, 39, 39).collidepoint((self.x+21,self.y+21)):
            
            # If dizzy, become eaten and add points based on pacman's current streak
            if self.state == "dizzy":
                pacman.streak += 1
                points = (2 ** pacman.streak) * 100
                level.score += points
                ui.drawPoints(points, (self.x, self.y))
                self.state = "eaten"
                
            # Otherwise, kill pacman
            elif self.state != "eaten":
                if not pacman.dead:
                    pacman.dead = True
                    level.freeze = True
    
    # Draw ghost with correct sprite based on current direction, animation frame and state
    def draw(self, image, level):
        if self.state == "dizzy":
            if level.dizzyTimer + 6000 < pygame.time.get_ticks() and self.flash:
                screen.blit(dizzyGhostImage, (self.x, self.y), dizzyGhostSpriteSheet[1][self.animFrame])
            else:
                screen.blit(dizzyGhostImage, (self.x, self.y), dizzyGhostSpriteSheet[0][self.animFrame])
        elif self.state == "eaten":
            if self.direction == "R":
                screen.blit(eatenGhostImage, (self.x, self.y), eatenGhostSpriteSheet[0])
            elif self.direction == "D":
                screen.blit(eatenGhostImage, (self.x, self.y), eatenGhostSpriteSheet[1])
            elif self.direction == "U":
                screen.blit(eatenGhostImage, (self.x, self.y), eatenGhostSpriteSheet[2])
            elif self.direction == "L":
                screen.blit(eatenGhostImage, (self.x, self.y), eatenGhostSpriteSheet[3])
        else:
            if self.direction == "R":
                screen.blit(image, (self.x, self.y), ghostSpriteSheet[0][self.animFrame])
            elif self.direction == "D":
                screen.blit(image, (self.x, self.y), ghostSpriteSheet[1][self.animFrame])
            elif self.direction == "U":
                screen.blit(image, (self.x, self.y), ghostSpriteSheet[2][self.animFrame])
            elif self.direction == "L":
                screen.blit(image, (self.x, self.y), ghostSpriteSheet[3][self.animFrame])

# Blinky (Red) inherits from ghost class
class Blinky(Ghost):
    def __init__(self):
        self.startX = self.x = 315
        self.startY = 398
        self.y = 327
        self.direction = "L"
        self.animFrame = 1
        self.state = "scatter"
        self.movement = 12
        self.ghostHouse = False
        self.waitTime = 0
        self.speed = 2
        self.flash = False
    
    # Controls move state and determines targets
    def moveController(self, level, pacman):
        
        # Inherit global state (scatter / chase) if not dizzy nor eaten
        if self.state != "dizzy" and self.state != "eaten":
            
            # Blinky has special case where he permanently chases if <= 20 dots remain
            if len(level.dots) <= 20:
                self.state = "chase"
            else:
                self.state = level.globalState
        if self.state == "chase":
            
            # Blinky targets pacman's current location when in chase mode
            self.move((pacman.x, pacman.y), level)
        else:
            
            # Blinky targets top-right corner when in scatter mode
            self.move((672, 0), level)
            
# Pinky (pink) inherits from ghost class                  
class Pinky(Ghost):
    def __init__(self):
        self.startX = self.x = 315
        self.startY = self.y = 398
        self.direction = "D"
        self.animFrame = 1
        self.state = "scatter"
        self.movement = 12
        self.ghostHouse = True
        self.waitTime = 0
        self.speed = 2
        self.flash = False
    
    # Controls move state and determines targets
    def moveController(self, level, pacman):
        
        # Inherit global state (scatter / chase) if not dizzy nor eaten
        if self.state != "dizzy" and self.state != "eaten":
            self.state = level.globalState
            
        # Pinky targets location 4 tiles in front of pacman when in chase mode
        if self.state == "chase":
            if pacman.direction == "L":
                self.move((pacman.x - 96, pacman.y), level)
            elif pacman.direction == "R":
                self.move((pacman.x + 96, pacman.y), level)
            elif pacman.direction == "U":
                self.move((pacman.x, pacman.y - 96), level)
            elif pacman.direction == "D":
                self.move((pacman.x, pacman.y + 96), level)
                
        # Pinky targets top-left corner when in scatter mode
        else:
            self.move((0, 0), level)

# Inky (cyan) inherits from ghost class
class Inky(Ghost):
    def __init__(self):
        self.startX = self.x = 268
        self.startY = self.y = 398
        self.direction = "U"
        self.animFrame = 1
        self.state = "scatter"
        self.movement = 12
        self.ghostHouse = True
        self.waitTime = 4000
        self.speed = 2
        self.flash = False
    
    # Controls move state and determines targets
    def moveController(self, level, pacman):
        
        # Inherit global state (scatter / chase) if not dizzy nor eaten
        if self.state != "dizzy" and self.state != "eaten":
            self.state = level.globalState
            
        # Calcualtes position 2 tiles in front of pacman
        if self.state == "chase":
            if pacman.direction == "L":
                pivot = (pacman.x - 48, pacman.y)
            elif pacman.direction == "R":
                pivot = (pacman.x + 48, pacman.y)
            elif pacman.direction == "U":
                pivot = (pacman.x, pacman.y - 48)
            elif pacman.direction == "D":
                pivot = (pacman.x, pacman.y + 48)
                
            # Inky targets location obtained by taking the vector between the intermediary position
            # (just calculated) and Blinky's position, and rotating it 180 degrees when in chase mode
            self.move((2 * pivot[0] - level.ghosts[0].x, 2 * pivot[1] - level.ghosts[0].y), level)
            
        # Inky targets bottom-right corner when in scatter mode
        else:
            self.move((672, 864), level)

# Clyde (orange) inherits from ghost class
class Clyde(Ghost):
    def __init__(self):
        self.startX = self.x = 364
        self.startY = self.y = 398
        self.direction = "U"
        self.animFrame = 1
        self.state = "scatter"
        self.movement = 12
        self.ghostHouse = True
        self.waitTime = 13000
        self.speed = 2
        self.flash = False
    
    # Controls move state and determines targets
    def moveController(self, level, pacman):
        
        # Inherit global state (scatter / chase) if not dizzy nor eaten
        if self.state != "dizzy" and self.state != "eaten":
            self.state = level.globalState
        
        # Clyde targets pacman's current location when in chase mode, BUT only when
        # he's more than 8 tiles from pacman, otherwise he retreats to bottom-left corner
        if self.state == "chase" and distance((self.x, self.y), (pacman.x, pacman.y)) > 192:
            self.move((pacman.x, pacman.y), level)
            
        # Clyde targets bottom-left corner when in scatter mode
        else:
            self.move((0, 864), level)

class Wall:
    def __init__(self, ID, x, y):
        self.x = x
        self.y = y
        self.ID = ID
        self.flash = False
    
    # Draw wall each frame
    def draw(self, level):
        
        # Draw wall2 (white walls) if won for flash effect
        if not(self.ID == 20 and level.won):
            if self.flash:
                screen.blit(wallImage2, (self.x, self.y), wallSpriteSheet[self.ID])
            else:
                screen.blit(wallImage, (self.x, self.y), wallSpriteSheet[self.ID])
        
class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    #  Check if eaten and increase score
    def eaten(self, level, pacman):
        if pygame.Rect(pacman.x,pacman.y,39,39).collidepoint((self.x+12,self.y+12)):
            level.score += 10
            return True
    
    # Draw dot each frame
    def draw(self):
        screen.blit(dotImage, (self.x, self.y))
        
class PowerPellet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.animFrame = 0
    
    # Animate pellet
    def animate(self):
        self.animFrame = (self.animFrame + 1) % 2
    
    #  Check if eaten, increase score and remove pacman's kill streak
    def eaten(self, level, pacman):
        if pygame.Rect(pacman.x,pacman.y,39,39).collidepoint((self.x+12,self.y+12)):
            pacman.streak = 0
            level.score += 50
            return True
    
    # Draw pellet each frame
    def draw(self):
        screen.blit(powerPelletImage, (self.x, self.y))
        
class Fruit:
    def __init__(self):
        self.x = 318
        self.y = 474
        self.spawnTime = pygame.time.get_ticks()
    
    # Check for collision with pacman and increase score 
    def hit(self, level, pacman, ui):
        if pygame.Rect(pacman.x,pacman.y,39,39).collidepoint((self.x+18,self.y+18)):
            level.score += 100
            ui.drawPoints(100, (self.x-10, self.y))
            return True
    
    # Draw fruit each frame
    def draw(self):
        screen.blit(fruitImage, (self.x, self.y))


# Title function - loop for when in title screen
def title(ui, level, game):
    screen.fill((0,0,0))
    
    # Check for quit and timer events
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()
        if event.type == timer1:
            ui.flash = not ui.flash

    ui.drawUI(level, game, False)
    
    # If a key is pressed, start game
    if 1 in pygame.key.get_pressed():
        return True
    
    window.blit(pygame.transform.scale(screen, window.get_rect().size), (0,0))
    pygame.display.update()

# Play function - loop for when playing game
def play(level, pacman, ui, game):
    screen.fill((0,0,0))
    clock.tick(60)
    
    # Check for quit and timer events
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()
        if event.type == timer1 and level.won:
            for wall in level.walls:
                    wall.flash = not wall.flash
        if event.type == timer2:
            if not level.won:
                pacman.animate(level, ui, game)
                for ghost in level.ghosts:
                    ghost.flash = not ghost.flash
                    ghost.animate()
        if event.type == timer3:
            for pellet in level.powerPellets:
                pellet.animate()
            
    pressed_keys = pygame.key.get_pressed()
    level.draw()
    pacman.draw(level)
    ui.drawUI(level, game, False)
    if not level.freeze:
        pacman.move(pressed_keys, level)
        
        # Delete eaten dots
        d = 0
        while d < len(level.dots):
            if level.dots[d].eaten(level, pacman):
                del level.dots[d]
                d -= 1
            d += 1
            
        # Delete eaten pellets
        p = 0
        while p < len(level.powerPellets):
            if level.powerPellets[p].eaten(level, pacman):
                del level.powerPellets[p]
                p -= 1
                for ghost in level.ghosts:
                    
                    # Activate dizzy mode for all ghosts (unless already eaten)
                    if ghost.state != "eaten":
                        ghost.state = "dizzy"
                        ghost.speed = 1
                    level.dizzyTimer = pygame.time.get_ticks()
            p += 1
            
        if level.dizzyTimer:
            
            # Go back to normal states if ghosts have been dizzy for 8 seconds
           if level.dizzyTimer + 8000 < pygame.time.get_ticks():
                pacman.streak = 0
                level.dizzyTimer = None
                for ghost in level.ghosts:
                    if ghost.state == "dizzy":
                        
                        # Safety measure - adjust ghost position to avoid glitches due to switching speeds
                        if (ghost.movement % 2) == 1:
                            if ghost.direction == "R":
                                ghost.x += 1
                            elif ghost.direction == "D":
                                ghost.y += 1
                            elif ghost.direction == "U":
                                ghost.y -= 1
                            elif ghost.direction == "L":
                                ghost.x -= 1
                            ghost.movement += 1
                        
                        ghost.speed = 2
                        ghost.state = level.globalState
        
        # Update global state from chase to scatter or vice-versa as dictated by phaseLengths list
        if pygame.time.get_ticks() - level.levelStart > phaseLengths[level.phase]:
            level.phase += 1
            if level.globalState == "chase":
                level.globalState = "scatter"
            else:
                level.globalState = "chase"       
        
        # Move each ghost and check for collisions
        for ghost in level.ghosts:
            ghost.moveController(level, pacman)
            ghost.hit(level, pacman, ui)
        
        # Spawn bonus fruit when 70 or 170 dots have been eaten
        if (len(level.dots) == 170 and level.fruitCount == 0) or (len(level.dots) == 70 and level.fruitCount == 1):
            level.fruit = Fruit()
            level.fruitCount += 1
        
        if level.fruit:
            
            # Delete bonus fruit if it has existed for 10 seconds
            if level.fruit.spawnTime + 10000 < pygame.time.get_ticks():
                level.fruit = None
            else:
                if level.fruit.hit(level, pacman, ui):
                    level.fruit = None
                else:
                    level.fruit.draw()
    
    # Wait 5 seconds after game over before returning to title screen
    if level.gameOver:
        if level.gameOver + 5000 < pygame.time.get_ticks():
            main()
    
    # Check if won by checking if all dots/pellets have been eaten
    if level.dots == [] and level.powerPellets == []:
        if not level.won:
            level.ghosts = []
            pacman.animFrame = 1
            level.won = pygame.time.get_ticks()
            level.freeze = True
            
        # Wait 5 seconds after winning before returning to title screen
        elif level.won + 5000 < pygame.time.get_ticks():
            main()

    window.blit(pygame.transform.scale(screen, window.get_rect().size), (0,0))       
    pygame.display.update()

# Main game function
def main():
    screen.fill((0,0,0))
    game = False
    ui = UI()
    level = Level()
    
    # Call title screen function until game has started
    while not game:
        game = title(ui, level, game)

    screen.fill((0,0,0))
    
    pacman = Pacman()
    level.draw()
    pacman.draw(level)
    ui.drawUI(level, game, True)
    
    # Wait 2 seconds after loading level before actually beginning
    pygame.display.update()
    pygame.time.wait(2000)
    level.reset()
    
    # Call play function 
    while True:
        play(level, pacman, ui, game)

# Initially run game
main()