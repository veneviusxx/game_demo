import sys, os, pygame, math, random


SCRIPT_PATH=sys.path[0] #gdzie w komputerze znajduję się folder z grą
#start awapygame
pygame.init()

def load_png(filename: str, folder = "resources", alpha = True):
    """Funkcja ładująca pliki, domyślnie z folderu resources"""
    if alpha:
        return pygame.image.load(os.path.join(SCRIPT_PATH,folder,filename)).convert_alpha()
    else:
        return pygame.image.load(os.path.join(SCRIPT_PATH,folder,filename)).convert()
running = True
#Ekran 
res_x = 800
res_y = 450
origin = [res_x//2, res_y//2] #początkowy środek mapy, używany do ustalania pozycji gracza
screen = pygame.display.set_mode((res_x, res_y))
score = 0
icon = load_png("icon.png").convert()
pygame.display.set_icon(icon)

collidable = [] #obiekty które mogą wejść w kolizje

class graphics(pygame.sprite.LayeredUpdates):
    """
    Klasa dziedzicząca z klasy pygame.sprite.LayeredUpdates, 
    używana do przechowywania i segregowania obiektów graficznych.
    """
    def __init__(self) -> None:
        pygame.sprite.LayeredUpdates.__init__(self)

    def sort_layer(self, layer : int) -> None:
        "sortuje kolejność renderowania spritów na danym poziomie"
        sprites = self.remove_sprites_of_layer(layer)
        sprites.sort(key = lambda sprite : sprite.pos[1])             
        self.add(sprites)

obj_drawable = graphics() #obiekty do narysowania, 0 jest rysowany pierwszy (czyli jest na samym dole)
enemies = pygame.sprite.Group()
    
#Generacja mapy
class game_obj(pygame.sprite.Sprite):
    """
    klasa abstrakcyjna od której dziedziczą wszystkie obiekty które są częścią gry.
    wszystkie takie obiekty muszą mieć swoje koordynaty w grze, możliwośc ich przeliczenia na koordynaty na ekranie,
    poziom na którym są wyświetlane, oraz własny obrazek i rect 
    """
    def __init__(self) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.image = None
        self.rect = None
        self.pos = None
        self.screen_pos = None
        self.layer = None
        self.top = None

    def getscreenpos(self) -> list:
        """
        Oblicza koordynaty względem pozycji gracza.
        Kordynaty w grze przeliczone na koordynaty kamery:
        [-map.screen_x, -map.screen_y] to lewy górny róg ekranu,
        [res_x//2-map.screen_x, res_y//2-map.screen_y] to środek,
        [res_x-map.screen_x, res_y-map.screen_y] to prawy dolny róg,
        gdzie res_x i res_y to rozdzielczość ekranu
        """
        return [self.pos[0] + map.screen_x, self.pos[1] + map.screen_y]

    def update(self) -> None:
        self.screen_pos = self.getscreenpos()
        self.rect.center = self.screen_pos
        if self.top:
            self.top.update()

class top_texture(game_obj):
    "Klasa reprezentująca górną część wysokich obiektów"
    def __init__(self, image : pygame.Surface, parent : game_obj, offset = 0) -> None:
        self.parent = parent 
        self.offset = offset #jak daleko ma być przesunięta textura w bok w stosunku do rodzica
        game_obj.__init__(self)
        self.image = image
        self.rect = image.get_rect()
        self.layer = self.parent.layer + 1
        obj_drawable.add(self)
        self.pos = [self.parent.pos[0] + self.offset, self.parent.pos[1] - self.parent.rect.height]

    def update(self) -> None:
        self.pos = [self.parent.pos[0] + self.offset, self.parent.pos[1] - self.parent.rect.height]
        self.rect.bottom = self.parent.rect.top
        self.rect.left = self.parent.rect.left + self.offset

class background_tile(game_obj):
    """
    Klasa reprezentująca kafelke tła.
    """
    tex_dict = {}
    for x in range(201):
        tex_dict[x] = load_png(f"grass ({x}).png", r"resources\grass", False)
    tile_size = 16

    def __init__(self, pos : list, id = int) -> None:
        game_obj.__init__(self)
        self.pos = pos
        self.id = id
        self.layer = 0
        self.screen_pos = self.getscreenpos()
        self.image = self.tex_dict[id]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = self.screen_pos
        obj_drawable.add(self)

class static_object(game_obj):
    """
    Klasa reprezentująca statyczne obiekty na mapie 
    id odpowiadają poszczególnym typom obiektów
    """
    tex_dict = {} #słownik id z teksturami, słownik zawiera listę i informację czy obiekt jest wysoki 
    top_dict = {} #słownik z górnymi częściami textur dla wysokich obiektów, posegregowane po id obiektu którego jest górą 
    for x in range(1,3):
        tex_dict[x] = [load_png(f"rock({x}).png", r"resources\rocks"), False]

    tex_dict[3] = [load_png("tree_bottom.png"), True]
    top_dict[3] = [load_png("tree_top.png"), -50]

    def __init__(self, pos : list, id : int) -> None:
        game_obj.__init__(self)

        self.layer = 1
        self.pos = pos
        self.screen_pos = self.getscreenpos()

        self.id = id
        self.image = self.tex_dict[id][0]
        self.tall = self.tex_dict[id][1]
        obj_drawable.add(self)

        self.rect = self.image.get_rect()
        self.rect.center = self.screen_pos

        if self.tall:
            self.top = top_texture(self.top_dict[self.id][0], self, offset=self.top_dict[self.id][1])

class graph():
    #size = 0 # na jaką ilość trzeba podzielic jednego tile'a (16x16)
    #sizes = []
    #for key in static_object.tex_dict.keys():
    #    rect = static_object.tex_dict[key][0].get_rect()
    #    sizes.append(max(rect.width, rect.height))
    #size = min(sizes)
    #size = size/background_tile.tile_size
    #size = math.ceil(math.log2(size)) #zwraca najbliższą potęgę 2 naszego rozmiaru, efektywnie mówi nam na ile mamy node'ów podzielic jedną płytke

    def __init__(self) -> None:
        self.nodes = []
        #do sklejania grafów ze sobą przydatne są osobne list na "boki" grafu
        self.top = []
        self.bottom = []
        self.left = []
        self.right = []
        self.corner = None #lewy górny róg
    
    def join(self, other) -> None:
        "Łączy dwa node'y dwóch grafów na podstawie pozycji ich rogów"
        if self.corner.pos[1] < other.corner.pos[1]:
            for i in range(len(self.bottom)):
                self.bottom[i].add_edge(other.top[i])
        elif self.corner.pos[1] > other.corner.pos[1]:
            for i in range(len(self.bottom)):
                self.top[i].add_edge(other.bottom[i])
        if self.corner.pos[0] < other.corner.pos[0]:
            for i in range(len(self.bottom)):
                self.right[i].add_edge(other.left[i])
        elif self.corner.pos[0] > other.corner.pos[0]:
           for i in range(len(self.bottom)):
               self.left[i].add_edge(other.right[i])       
    
#    def print_graph(self):
#        text_file = open("t.txt", "w")
#        node_pos = {}
#        for node in self.nodes:
#            node_pos[node.pos] = node
#        keys = [pos for pos in node_pos.keys()]
#        for key in keys:
#            strg = ""
#            node = node_pos[key]
#            if node.top:
#                strg += " | "
#            if node.left:
#                strg += "-"
#            strg += " "
#            if node.right:
#                strg += "-"
#            if node.bottom:
#                strg += " | \n"
#            text_file.write(strg)
#        text_file.close()

    def add(self, node) -> None:
        self.nodes.append(node)

    def remove(self, node) -> None:
        self.nodes.remove(node)

    def check_corner(self) -> None:
        for node1 in self.top:
            for node2 in self.left:
                if node1 == node2:
                    self.corner = node1
        if not self.corner:
            raise ValueError("Corner doesn't exist")

class node():
    node_count = 0 
    
    def __init__(self, pos : tuple, graph : graph, edges = None) -> None:
        node.node_count += 1
        self.pos = tuple(pos) 
        self.edges = edges #sąsiedzi danego node'a
        self.graph = graph
        self.top = False
        self.bottom = False
        self.right = False
        self.left = False
        self.blocked = False
    
    def __repr__(self) -> str:
        return f"Node at {self.pos} with {len(self.edges)}"

    def kill(self) -> None:
        node.node_count -= 1
        for elem in self.edges:
            elem.edges.remove(self)
        self.graph.nodes.remove(self)

    def add_edge(self, other) -> None:
        self.edges.append(other)
        other.edges.append(self)
        if other.pos == (self.pos[0], self.pos[1] - 16):
            self.top = True
            other.bottom = True
        if other.pos == (self.pos[0], self.pos[1] + 16):
            self.bottom = True
            other.top = True
        if other.pos == (self.pos[0] - 16, self.pos[1]):
            self.left = True
            other.right = True
        if other.pos == (self.pos[0] + 16, self.pos[1]):
            self.right = True     
            other.left = True

class chunk(pygame.sprite.Group):
    """
    klasa przechowuje 5x5 tile-ów; używana do generacji mapy
    """
    size = 5
    chunk_count = 0
    node_density = 1

    #def set_nodes_pos(self) -> None:
    #    if not self.node_pos:
    #        chunk_nodes_pos = []
    #        for node in self.chunk_graph.nodes:
    #            chunk_nodes_pos.append(node.pos)
    #        self.node_pos = chunk_nodes_pos

    def chunk_gen(seed) -> list:
        "funkcja tymczasowo zastępująca generator świata"
        random.seed(seed)
        stat = []
        back = []
        static = [*list(static_object.tex_dict.keys())]
        static.append(0)
        population = [1/(100*len(static_object.tex_dict)) for _ in range(len(static_object.tex_dict))]
        population.append(0.99)
        for _ in range(chunk.size*chunk.size):
            stat.append(random.choices(static, population)[0])
            back.append(random.randint(0,200))
        return [back,stat]

    def __init__(self, pos : list, num_maps : list) -> None:
        pygame.sprite.Group.__init__(self)
        self.chunk_nodes_pos = {}
        self.chunk_graph = graph()
        self.pos = pos #pozycja lewego górnego rogu lewej górnej płytki chunka
        self.num_maps = num_maps #przechowuje 2 listy wielkości chunk.size*chunk.size, odpowiada za obiekty na mapie
        self.chunk_rect = pygame.rect.Rect(pos[0], pos[1], chunk.size*16, chunk.size*16)
        chunk.chunk_count += 1
        #dodawanie background tilów o odpowiednich id i losowych obiektów statycznych do chunka 
        #płytki są dodawane z lewego górnego rogu w prawo, potem jeden rząd w dół itd.
        for i in range(chunk.size*chunk.size):
            pos_x = self.pos[0] + 16*round((i%chunk.size),0)
            pos_y = self.pos[1] + 16*(i//chunk.size)
            tile_num = [round((i%chunk.size),0), i//chunk.size]
            tile_pos = [pos_x, pos_y]
            self.add(background_tile(tile_pos, self.num_maps[0][i]))
            for k in range(chunk.node_density):
                for n in range(chunk.node_density):
                    node_pos = (pos_x  + k*(16/chunk.node_density),
                                pos_y  + n*(16/chunk.node_density))
                    current = node(node_pos, self.chunk_graph, [])
                    self.chunk_graph.add(current)
                    self.chunk_nodes_pos[node_pos] = current
                    if k%chunk.node_density == 0 and i%chunk.size == 0:
                        self.chunk_graph.left.append(current)
                    if k%chunk.node_density == chunk.node_density-1 and i%chunk.size == chunk.size-1:
                        self.chunk_graph.right.append(current)
                    if  n%chunk.node_density == 0 and i in range(chunk.size):
                        self.chunk_graph.top.append(current)
                    if  n%chunk.node_density == 0 and i in [chunk.size*chunk.size-x-1 for x in range(chunk.size)]:
                        self.chunk_graph.bottom.append(current)
                    if tile_num[1] > 0:
                        current.add_edge(self.chunk_graph.nodes[-chunk.size - 1])
                    if tile_num[0] > 0:
                        current.add_edge(self.chunk_graph.nodes[-2])
                    if num_maps[1][i]:
                        current.blocked = True

            if num_maps[1][i]:
               st_ob = static_object(tile_pos, num_maps[1][i])
               self.add(st_ob)
               collidable.append(st_ob)
        self.chunk_graph.check_corner()

    def join_chunk_graphs(self, other) -> None:
        self.chunk_graph.join(other.chunk_graph)

    def kill(self):
        chunk.chunk_count -= 1
        for elem in self:
            if elem.top:
                elem.top.kill()
            elem.kill()
        self.empty()

class enemy(game_obj):
    tex_dict = {}
    top_dict = {}
    show_node = False
    tex_dict[0] = [load_png("slime.png"), 0]
    tex_dict[1] = [load_png("wrog(1).png"), 0]

    def __init__(self, pos : list, id : int, enemy_map : map, layer = 1) -> None:
        game_obj.__init__(self)
        self.enemy_map = enemy_map
        self.layer = layer
        self.pos = pos
        self.health = 12
        self.screen_pos = self.getscreenpos()
        self.cur_node = self.get_current_node()
        self.next_node = self.get_next_node()
        self.id = id
        self.image = self.tex_dict[id][0]
        self.tall = self.tex_dict[id][1]
        self.moving = False
        obj_drawable.add(self)
        enemies.add(self)
        collidable.append(self)

        self.rect = self.image.get_rect()
        self.rect.center = self.screen_pos

        if self.tall:
            self.top = top_texture(self.top_dict[self.id][0], self, offset=self.top_dict[self.id][1])
        
    def update(self):
        if self.health < 0:
            self.remove()
        self.node_move()
        self.screen_pos = self.getscreenpos()
        self.rect.center = self.screen_pos
        if self.top:
            self.top.update()

    def hit(self):
        global score
        score += 1
        self.health -= 3

    def move(self, delta : list, collision_group) -> None:
        possible_rect = self.rect.move(delta)
        global running

        re_add = False
        if self in collision_group:
            collision_group.remove(self)
            re_add = True

        if not possible_rect.collidelist(collision_group) + 1:
            self.pos = [self.pos[0] + delta[0], self.pos[1] + delta[1]]
        
        if possible_rect.collidelist(collision_group) + 1:
            possible = collidable[possible_rect.collidelist(collision_group)]
            if type(possible) == player:
                running = False

        if re_add:
            collision_group.append(self)

    def get_current_chunk(self) -> chunk:
        for pos in self.enemy_map.chunks.keys():
            if self.enemy_map.chunks[pos].chunk_rect.collidepoint(self.pos):
                return self.enemy_map.chunks[pos]
        else:
            self.kill()
            return None
    
    def get_current_node(self) -> node:
        chnk = self.get_current_chunk()
        if not chnk:
            return None
        #chnk.set_nodes_pos() #ustala liste pozycji node'ów dla chunka
        for pos in chnk.chunk_nodes_pos.keys():
            if abs(pos[0] - self.pos[0]) < 16:
                if abs(pos[1] - self.pos[1]) < 16:
                    return chnk.chunk_nodes_pos[pos]
                
    def get_next_node(self) -> node:
        propositions = {}
        player_pos = self.enemy_map.player.pos
        for node in self.cur_node.edges:
            if not node.blocked:
                cost = (node.pos[0] - player_pos[0])**2 + (node.pos[1] - player_pos[1])**2
                propositions[cost] = node
        best = min(propositions.keys())
        next_node = propositions[best]
        #next_pos = (self.cur_node.pos[0], self.cur_node.pos[1] - 16/chunk.node_density )
        #next_node = self.enemy_map.map_nodes_pos[next_pos]
        if self.cur_node in next_node.edges:
            self.moving = True
            return next_node
        raise ValueError("Didn't find next node")
        
    def update_cur_node(self) -> None:
        if not round(abs(self.pos[0] - self.next_node.pos[0]), 1) and not round(abs(self.pos[1] - self.next_node.pos[1]), 1):
            self.moving = False
            self.pos = self.next_node.pos
        if not self.moving:
            if not self.get_current_chunk():
                return None
            keys = list(self.get_current_chunk().chunk_nodes_pos.keys())
            keys.sort(key= lambda x: (x[0]-self.pos[0])**2+(x[1]-self.pos[1])**2)
            chunk_dist = (min(keys)[0]-self.pos[0])**2+(min(keys)[1]-self.pos[1])**2
            cur_dist = (self.cur_node.pos[0]-self.pos[0])**2+(self.cur_node.pos[1]-self.pos[1])**2
            next_dist = (self.next_node.pos[0]-self.pos[0])**2+(self.next_node.pos[1]-self.pos[1])**2
            #cur_dist = abs(self.cur_node.pos[0]+self.cur_node.pos[1] - self.pos[0] - self.pos[1])
            #next_dist = abs(self.next_node.pos[0]+self.next_node.pos[1] - self.pos[0] - self.pos[1]) 
            if next_dist < cur_dist and chunk_dist > next_dist:
                self.cur_node = self.next_node
                self.next_node = self.get_next_node()
            if chunk_dist < cur_dist:
                self.cur_node = self.get_current_chunk().chunk_nodes_pos[min(keys)]
                self.next_node = self.get_next_node()

    def node_move(self) -> None:
        delta = [-(self.pos[0] - self.next_node.pos[0]), -(self.pos[1] - self.next_node.pos[1])]
        norm = (delta[0]**2 + delta[1]**2)**(1/2)
        delta = [2*delta[0]/norm, 2*delta[1]/norm]

        if self.show_node:
            enemies.add(static_object(self.cur_node.pos, 1))
            enemy.show_node = False
        self.move(delta, collidable)
        self.update_cur_node()
    
    def remove(self):
        collidable.remove(self)
        self.kill()

class map():
    screen_x = origin[0] #pozycja ekranu na mapie
    screen_y = origin[1]

    def __init__(self) -> None:
        self.chunks = {} #słownik aktualnych chunk'ów z koordynatami jako kluczami
        #self.rects = {}
        self.main_graph = graph()
        self.map_nodes_pos = {}
        #jak dużo chunk'ów ma być na ekranie?
        self.chunks_x = res_x//(16*chunk.size) + 2
        self.chunks_y = res_y//(16*chunk.size) + 3
        self.player = None
        self.update()

    def add(self, chnk : chunk) -> None:
        self.chunks[tuple(chnk.pos)] = chnk
        #self.rects[chnk] = chnk.chunk_rect
        #spajanie node'ów grafów poszczególnych chunków
        for pos in self.chunks.keys():
            other = self.chunks[pos]
            #if 32*chunk.size > abs(pos[0] - chnk.pos[0]) >= 16*chunk.size and 32*chunk.size > abs(pos[1] - chnk.pos[1]) >= 16*chunk.size:
            if pos == (chnk.pos[0], chnk.pos[1]+16*chunk.size):
                chnk.join_chunk_graphs(other)
            if pos == (chnk.pos[0], chnk.pos[1]-16*chunk.size):
                chnk.join_chunk_graphs(other)
            if pos == (chnk.pos[0]+16*chunk.size, chnk.pos[1]):
                chnk.join_chunk_graphs(other)
            if pos == (chnk.pos[0]-16*chunk.size, chnk.pos[1]):
                chnk.join_chunk_graphs(other)                              
            #    #jeśli nasz sprawdzany chunk jest bardziej na prawo to połącz lewe nody sprawdzanego z prawymi dodawanego, reszta podobnie
            #    if pos[0] - chnk.pos[0] > 0:
            #        for i in range(len(chnk.chunk_graph.left)):
            #            chnk.chunk_graph.left[i].add_edge(other.chunk_graph.right[i])
            #    else:
            #        for i in range(len(chnk.chunk_graph.left)):
            #            chnk.chunk_graph.right[i].add_edge(other.chunk_graph.left[i])
            #if 32*chunk.size > abs(pos[1] - chnk.pos[1]) >= 16*chunk.size:
            #     chnk.join_chunk_graphs(other)
            #    if pos[1] - chnk.pos[1] > 0:
            #        for i in range(len(chnk.chunk_graph.left)):
            #            chnk.chunk_graph.top[i].add_edge(other.chunk_graph.bottom[i])
            #    else:
            #        for i in range(len(chnk.chunk_graph.left)):
            #            chnk.chunk_graph.bottom[i].add_edge(other.chunk_graph.top[i])
        for node in chnk.chunk_graph.nodes:
            self.main_graph.add(node)
            self.map_nodes_pos[node.pos] = node

    def chunk_search(self) -> list:
        "metoda sprawdza jaki chunk jest w lewym górnym rogu i na tej podstawie zwraca jakie koordynaty powinny mieć chunki na ekranie"
        ch_x = (-map.screen_x//(16*chunk.size))*16*chunk.size
        ch_y = (-map.screen_y//(16*chunk.size))*16*chunk.size
        chunks_pos = []
        for x in range(self.chunks_x):
            for y in range(self.chunks_y):
                chunks_pos.append((ch_x + x*chunk.size*16, ch_y + y*chunk.size*16))
        return chunks_pos

    def update(self) -> None:
        new_pos = self.chunk_search()
        to_del = [] 
        #usuwanie chunków poza ekranem
        for pos in self.chunks.keys():
            if not pos in new_pos:
                to_del.append(pos)
        for pos in to_del:
            chnk = self.chunks[pos]
            for node in chnk.chunk_graph.nodes:
                self.main_graph.remove(node)
            self.chunks.pop(pos)
            #self.rects[chnk.chunk_rect].pop(chnk)
            chnk.kill()
        #dodawanie chunków potrzebnych by wypełnic ekran, a których nie ma jeszcze na mapie 
        for pos in new_pos:
            if not pos in list(self.chunks.keys()):
                self.add(chunk(pos, chunk.chunk_gen(pos)))
        #by podczas chodzenia w dół obiekty z chunków poprawnie na siebie nakładały,
        obj_drawable.sort_layer(2)
        #update wszystkich chunków
        for pos in self.chunks.keys():
            self.chunks[pos].update()

class weapon(game_obj):
    tex_dict = {"laser" : load_png("laser.png")}
    
    def __init__(self, type : str, parent : game_obj) -> None:
        game_obj.__init__(self)
        self.projectiles = []
        self.type = type
        self.image = weapon.tex_dict[self.type]
        self.rect = self.image.get_rect()
        self.parent = parent
        self.direc = "right"
        self.cur_node = self
        self.layer = self.parent.layer + 1
        obj_drawable.add(self)
        self.pos = [self.parent.pos[0] + 20, self.parent.pos[1]]
        self.rect.center = [self.parent.rect.center[0] + 20, self.parent.rect.center[1]]

    def shoot(self):
        if not pygame.time.get_ticks()%5:
            print(pygame.time.get_ticks())
            vector = None
            if self.direc == "left":
                vector = [-6,0]
            if self.direc == "right":
                vector = [6,0]
            if self.direc == "bottom":
                vector = [0,6]
            if self.direc == "top":
                vector = [0,-6]                       
            self.projectiles.append(projectile(self.pos, self.type, vector, self, self.parent.player_map))

    def update(self) -> None:
        for proj in self.projectiles:
            proj.update() 
        self.image = weapon.tex_dict[self.type]
        if self.direc == "left":
            self.image = pygame.transform.flip(self.image, True, False)
            self.pos = [self.parent.pos[0] - 20, self.parent.pos[1]]
            self.rect.center = [self.parent.rect.center[0] - 25, self.parent.rect.center[1]]
        if self.direc == "top":
            self.image = pygame.transform.rotate(self.image, 90)
            self.pos = [self.parent.pos[0], self.parent.pos[1] - 30]
            self.rect.center = [self.parent.rect.center[0] + 5, self.parent.rect.center[1] - 40]
        if self.direc == "bottom":
            self.image = pygame.transform.rotate(self.image, -90)
            self.pos = [self.parent.pos[0], self.parent.pos[1] + 20]
            self.rect.center = [self.parent.rect.center[0] + 5, self.parent.rect.center[1] + 20]
        if self.direc == "right":
            self.pos = [self.parent.pos[0] + 20, self.parent.pos[1]]
            self.rect.center = [self.parent.rect.center[0] + 25, self.parent.rect.center[1]]       

    def update_orientation(self, direc : str) -> None:
        self.direc = direc
    
    def node_move(self) -> None:
        delta = [-(self.pos[0] - self.next_node.pos[0]), -(self.pos[1] - self.next_node.pos[1])]
        norm = (delta[0]**2 + delta[1]**2)**(1/2)
        delta = [2*delta[0]/norm, 2*delta[1]/norm]

class projectile(game_obj):
    tex_dict = {"laser":load_png("laserbeam.png")}
    def __init__(self, pos : list, type : str, vector : list, parent : weapon, proj_map : map) -> None:
        game_obj.__init__(self)
        self.type = type
        self.image = projectile.tex_dict[self.type]
        self._layer = 1
        self.vector = vector
        self.parent = parent
        self.proj_map = proj_map
        self.pos = pos
        self.rect = self.image.get_rect()
        self.rect.center = self.parent.rect.center
        obj_drawable.add(self)
        self.cur_node = self.get_current_node()
    
    def get_current_chunk(self) -> chunk:
        try:
            for pos in self.proj_map.chunks.keys():
                if self.proj_map.chunks[pos].chunk_rect.collidepoint(self.pos):
                    return self.proj_map.chunks[pos]
        except:
            self.kill()
    
    def get_current_node(self) -> node:
        chnk = self.get_current_chunk()
        if not self:
            return None
        #chnk.set_nodes_pos() #ustala liste pozycji node'ów dla chunka
        if not chnk:
            return None
        for pos in chnk.chunk_nodes_pos.keys():
            if abs(pos[0] - self.pos[0]) < 16:
                if abs(pos[1] - self.pos[1]) < 16:
                    return chnk.chunk_nodes_pos[pos]

    def damage(self):
        for enemy in enemies:
            if enemy.cur_node == self.cur_node:
                print("ouch")
    
    def update(self) -> None:
        self.move(self.vector, collidable)
        self.screen_pos = self.getscreenpos()
        self.cur_node = self.get_current_node()
        self.rect.center = self.screen_pos
        if self.top:
            self.top.update()

    def kill(self):
        self.parent.projectiles.remove(self)
        obj_drawable.remove(self)

    def move(self, delta : list, collision_group) -> None:
        possible_rect = self.rect.move(delta)

        re_add = False
        if self in collision_group:
            collision_group.remove(self)
            re_add = True

        if not possible_rect.collidelist(collision_group) + 1:
            self.pos = [self.pos[0] + delta[0], self.pos[1] + delta[1]]

        if re_add:
            collision_group.append(self)
        
        if possible_rect.collidelist(collision_group) + 1:
            hited = collidable[possible_rect.collidelist(collision_group)]
            if type(hited) == enemy:
                hited.hit()
            self.kill()
#Gracz
class player(game_obj):
    def __init__(self, player_map : map) -> None:
        game_obj.__init__(self)
        self.image = load_png("Player_bottom_south.png")
        self.top_image = load_png("Player_top_south.png")
        self.layer = 1
        self.player_map = player_map
        player_map.player = self
        self.pos = [0,0] #pozycja gracza względem koordynatów w grze
        self.screen_pos = self.getscreenpos() #pozycja gracza na ekranie, zawsze powinna być taka sama (na środku)
        self.rect = self.image.get_rect()
        self.rect.bottomright = self.screen_pos
        self.top = top_texture(self.top_image, self)
        self.weapon = weapon("laser", self)
        obj_drawable.add(self)
    
    def check_collision(self, collision_group : list) -> bool:
        """Sprawdza czy gracz nie zderza się z żadnym elementem z collision_group"""
        for rect in collision_group:
            if self.rect.colliderect(rect):
                return True
        return False
    
    def get_current_chunk(self) -> chunk:
        for pos in self.player_map.chunks.keys():
            if self.player_map.chunks[pos].chunk_rect.collidepoint(self.pos):
                return self.player_map.chunks[pos]
        else:
            raise TypeError("Could't find objects' chunk")
    
    def get_current_node(self) -> node:
        chnk = self.get_current_chunk()
        #chnk.set_nodes_pos() #ustala liste pozycji node'ów dla chunka
        for pos in chnk.chunk_nodes_pos.keys():
            if abs(pos[0] - self.pos[0]) < 16:
                if abs(pos[1] - self.pos[1]) < 16:
                    return chnk.chunk_nodes_pos[pos]

    def move(self, delta : list, collision_group) -> None:
        """
        Porusza gracza o delta jeśli ten nie zderza się 
        z żadnym obiektem z collision_group
        """
        possible_rect = self.rect.move(delta)

        re_add = False
        if self in collision_group:
            collision_group.remove(self)
            re_add = True

        if not possible_rect.collidelist(collision_group) + 1:
            map.screen_x = map.screen_x - delta[0]
            map.screen_y = map.screen_y - delta[1] 
            self.pos = [self.pos[0] + delta[0], self.pos[1] + delta[1]]

        if re_add:
            collision_group.append(self)   

def spawner(mapa : map):
    possible = mapa.chunks.keys()
    pos = random.choice(list(possible))
    if len(enemies) < 5 and random.choice([0,1]):
        enemies.add(enemy(pos, 0, mapa))

def score_window():
    font = pygame.font.SysFont('comicsans', 40)
    text = font.render('Score: ' + str(score), 1, (0, 0, 0))
    rect = text.get_rect()
    #screen.draw.rect_text(text, (255, 255, 255), rect)
    screen.blit(text, (0, 10))  

#Pętla gry
def main():
    global running
    Clock = pygame.time.Clock() #tworznie zegara 
    mapa = map()
    gracz = player(mapa)
    przeciwnik = enemy([0,48], 0, mapa)
    collidable.append(gracz)

    while running:
        keys = pygame.key.get_pressed() #lista przyciśniętych klawiszy na klawiaturze, musi być zdefiniowana w mainloopie by aktualizować się co klatke
        screen.fill((0,0,0)) #wyczyść ekran przed narysowaniem kolejnej klatki

        #obsługa wydarzeń
        for event in pygame.event.get():
            #wyłączanie gry
            if event.type == pygame.QUIT:
                running = False

        #obsługa klawiatury
        if keys[pygame.K_LEFT]:
            gracz.move([-4,0], collidable)
            gracz.weapon.update_orientation("left")
        
        if keys[pygame.K_RIGHT]:
            gracz.move([4,0], collidable)
            gracz.weapon.update_orientation("right")

        if keys[pygame.K_UP]:
            gracz.move([0,-4], collidable)
            gracz.weapon.update_orientation("top")

        if keys[pygame.K_DOWN]:
            gracz.weapon.update_orientation("bottom")
            gracz.move([0,4], collidable)

        if keys[pygame.K_SPACE]:
            gracz.weapon.shoot()
        
        if keys[pygame.K_F1]:
            #for pos in mapa.map_nodes_pos.keys():
                enemy.show_node = True
            #i = 0
            #for node in mapa.main_graph.nodes:
            #    if len(node.edges) < 3:
            #        i += 1
            #print(i)

        #update ekranu
        gracz.update()
        gracz.weapon.update()
        enemies.update()
        mapa.update()
        spawner(mapa)
        obj_drawable.draw(screen) #ta metoda rysuje obiekt tam gdzie jest jego rect
        score_window()
        pygame.display.flip()
        Clock.tick(30) #ograniczenie prędkości wykonywania się programu, nigdy nie będzie wykonywał więcej niż 30 klatek na sekundę
if __name__ == "__main__":
    main()