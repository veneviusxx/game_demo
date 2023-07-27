import pygame, sys, random, math

   
win_width = 1280
win_height = 720
    
grass_color = (102, 204, 0)

    
pygame.init()
fps_clock = pygame.time.Clock()
display = pygame.display.set_mode((win_width, win_height))

class Player(pygame.sprite.Sprite):
    def __init__(self, xpos, ypos, xsize, ysize):
        self.xpos = xpos
        self.ypos = ypos
        self.xsize = xsize
        self.ysize = ysize
        self.image = pygame.image.load('player.png')
        self.image = pygame.transform.scale(self.image, (xsize, ysize))
        self.rect = self.image.get_rect(center = (self.xpos, self.ypos))
        
    def draw(self, display):
        display.blit(self.image, self.rect)

    def getx(self):
        return self.rect.x
    
    def gety(self):
        return self.rect.y
    
    
image_tree = pygame.image.load('tree.png')
image_tree = pygame.transform.scale(image_tree, (80, 80))
image_stone = pygame.image.load('stone.png').convert_alpha()
image_stone = pygame.transform.scale(image_stone, (30, 30))
image_grass = pygame.image.load('grass.png').convert_alpha()
image_grass = pygame.transform.scale(image_grass, (50, 50))
    
static_images = [image_tree, image_stone, image_grass]

pos_x = 0
pos_y = 0


def RandomPos(pos_x, pos_y, width, height):
    cam_rect = pygame.Rect(pos_x, pos_y, win_width, win_height)
    
    while True:
        x = random.randint(pos_x - win_width, pos_x + (2*win_width))
        y = random.randint(pos_y - win_height, pos_y + (2*win_height))
        
        z = pygame.Rect(x, y, width, height)
        if not z.colliderect(cam_rect):
            return x, y


def ArrangeStatic(pos_x, pos_y):
    static_dict = dict()
    static_dict['image'] = random.randint(0, len(static_images)-1)
    static_dict['width'] = static_images[0].get_width()
    static_dict['height'] = static_images[0].get_height()
    static_dict['x'], static_dict['y'] = RandomPos(pos_x, pos_y, static_dict['width'], static_dict['height'])
    static_dict['rect'] = pygame.Rect((static_dict['x'], static_dict['y'], static_dict['width'], static_dict['height']))
    return static_dict
        
static = []
for i in range(20):
    static.append(ArrangeStatic(pos_x, pos_y))
    static[i]['x'] = random.randint(0, win_width)
    static[i]['y'] = random.randint(0, win_height)  

character = Player(640, 360, 60, 60)


running = True
while running:
    
    display.fill(grass_color)
    character.draw(display)

    
    for i in static:
        q = pygame.Rect((i['x'] - pos_x, i['y'] - pos_y, i['width'], i['height']))
        display.blit(static_images[i['image']], q)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
              
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                character.rect.x -= 100
    
            elif event.key == pygame.K_RIGHT:
                character.rect.x += 100
    
            elif event.key == pygame.K_UP:
                character.rect.y -= 100
    
            elif event.key == pygame.K_DOWN:
                character.rect.y += 100
    
    pygame.display.update()        

     
pygame.quit()
sys.exit()


