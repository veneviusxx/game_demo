import pygame, sys


win_width = 1280
win_height = 720
    
grass_color = (102, 204, 0)
white = (255, 255, 255)

    
pygame.init()
fps_clock = pygame.time.Clock()
display = pygame.display.set_mode((win_width, win_height))

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, xsize, ysize):
        super().__init__()
        self.x = x
        self.y = y
        self.xsize = xsize
        self.ysize = ysize
        self.image = pygame.image.load('player.png')
        self.image = pygame.transform.scale(self.image, (xsize, ysize))
        self.rect = self.image.get_rect(center = (self.x, self.y))
        
        self.change_x = 0
        self.change_y = 0
        
    def draw(self, display):
        display.blit(self.image, self.rect)

    def getx(self):
        return self.rect.x
    
    def gety(self):
        return self.rect.y
    
    def change(self, x, y):
        self.change_x += x
        self.change_y += y
  
    def update(self):
        self.x += self.change_x
        self.y += self.change_y
        
    def stop(self):
        pass
        
        
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, xsize, ysize, enemy):
        super().__init__()
        self.enemy = enemy
        self.x = x
        self.y = y
        self.xsize = xsize
        self.ysize = ysize
        self.image = pygame.image.load('enemy.png')
        self.image = pygame.transform.scale(self.image, (xsize, ysize))
        self.rect = self.image.get_rect(center = (self.x, self.y))
    
        self.change_x = 0
        self.change_y = 0
        
    def getx(self):
        return self.rect.x
    
    def gety(self):
        return self.rect.y
    
    def draw(self, display):
        display.blit(self.image, self.rect)
        
    def change(self, x, y):
        self.change_x += x
        self.change_y += y
        
    def update(self):
        if self.enemy.rect.x > self.rect.x:
            self.rect.x += 1
        
        if self.enemy.rect.x < self.rect.x:
            self.rect.x -= 1
        
        if self.enemy.rect.y > self.rect.y:
            self.rect.y += 1
        
        if self.enemy.rect.y < self.rect.y:
            self.rect.y -= 1
            
        if self.enemy.rect.x == self.rect.x:
            pass
        
        if self.enemy.rect.y == self.rect.y:
            pass
        
    def stop(self):
        pass


class Win(pygame.sprite.Sprite):
    pass


class Lose(pygame.sprite.Sprite):
    pass
      

list = pygame.sprite.Group()
   
character = Player(120, 350, 100, 100)
enemy = Enemy(1100, 120, 100, 100, character)
list.add(character)
list.add(enemy)


running = True
while running:
    
    display.fill(grass_color)
    character.draw(display)
    enemy.draw(display)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
              
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                character.rect.x -= 110
    
            elif event.key == pygame.K_RIGHT:
                character.rect.x += 110
    
            elif event.key == pygame.K_UP:
                character.rect.y -= 110
    
            elif event.key == pygame.K_DOWN:
                character.rect.y += 110
    
    list.update()
    pygame.display.flip()
    pygame.display.update()        

     
pygame.quit()
sys.exit()

