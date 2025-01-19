import random
import pygame

from ZODB import FileStorage, DB
import transaction
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping


#baza podataka
storage = FileStorage.FileStorage('database/BazaSkakac.fs')  
db = DB(storage)
connection = db.open() 
root = connection.root  

# provjera i inicijalizacija baze podataka ako entiteti ne postoje
if not hasattr(root, 'all_games'):
    print("Inicijalizacija 'all_games' jer nije pronađena u bazi.")
    root.all_games = PersistentList() 
    transaction.commit()

if not hasattr(root, 'users'):
    root.users = PersistentMapping() 
    transaction.commit()

if not hasattr(root, 'daily_challenges'):
    print("Inicijalizacija 'daily_challenges' jer nije pronađena u bazi.")
    root.daily_challenges = PersistentList() 
    transaction.commit()



#izazovi
from datetime import datetime, timedelta

izazovi = [
    {
        'challenge_id': 1,
        'description': 'Prikupi 20 zvijezda u jednoj igri',
        'reward': 20,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    },
    {
        'challenge_id': 2,
        'description': 'Pretrpi 5 sudara s raketama',
        'reward': 30,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    },
    {
        'challenge_id': 3,
        'description': 'Dođi do udaljenosti od 1000m',
        'reward': 100,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'end_date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d')
    }
]

#dodavanje izazova ako ne postoje
for challenge in izazovi:
    if not any(ch['challenge_id'] == challenge['challenge_id'] for ch in root.daily_challenges):
        root.daily_challenges.append(challenge)
        print(f"Izazov dodan: {challenge['description']}")

transaction.commit()


#provjera u db
for user_name, user_data in root.users.items():
    if 'lifetime_stars' not in user_data:
        user_data['lifetime_stars'] = 0  
    transaction.commit()

    if 'games_played' not in user_data:
        user_data['games_played'] = 0
    if 'crashes_lasers' not in user_data:
        user_data['crashes_lasers'] = 0
    if 'crashes_rockets' not in user_data:
        user_data['crashes_rockets'] = 0
    if 'record' not in user_data:
        user_data['record'] = 0
    if 'stars' not in user_data:
        user_data['stars'] = 0
    if 'jetpacks' not in user_data:
        user_data['jetpacks'] = ['jetpack']
    if 'active_jetpack' not in user_data:
        user_data['active_jetpack'] = 'jetpack'
    transaction.commit()



print("Svi podaci u root.all_games prilikom pokretanja igre:")
if hasattr(root, 'all_games') and root.all_games:
    for game in root.all_games:
        print(game)
else:
    print("Baza je prazna ili nema zapisa u 'all_games'!")

  

high_score = max((game['distance'] for game in root.all_games), default=0)
lifetime_stars = sum(user_data.get('lifetime_stars', 0) for user_data in root.users.values())


pygame.init()

WIDTH = 1000
HEIGHT = 600
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption('Skakac by Petar Semiga')
fps = 60
timer = pygame.time.Clock()
font = pygame.font.Font('freesansbold.ttf', 32)
lines = [0, WIDTH / 4, 2 * WIDTH / 4, 3 * WIDTH / 4]
game_speed = 3
pause = False
init_y = HEIGHT - 130
player_y = init_y
booster = False
counter = 0
y_velocity = 0
gravity = 0.4
new_laser = True
laser = []
distance = 0
restart_cmd = False
walk_counter = 0 
TOP_MARGIN = 50  
BOTTOM_MARGIN = 130
rocket_counter = 0
rocket_active = False
rocket_delay = 0
rocket_coords = []

#učitavanje slika
start_screen_image = pygame.image.load('images/start.png')
start_screen_image = pygame.transform.scale(start_screen_image, (WIDTH, HEIGHT)) 

end_screen_image = pygame.image.load('images/kraj.png')
end_screen_image = pygame.transform.scale(end_screen_image, (WIDTH, HEIGHT))  

oprez_image = pygame.image.load('images/oprez.png')
oprez_image = pygame.transform.scale(oprez_image, (50, 50))

rocket_image = pygame.image.load('images/raketa.png')
rocket_image = pygame.transform.scale(rocket_image, (70, 70))

okvir_image = pygame.image.load('images/okvir.png')
okvir_image = pygame.transform.scale(okvir_image, (WIDTH, 50))

background_image = pygame.image.load('images/background.png')
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

laser_image = pygame.image.load('images/laser.png')  
laser_image = pygame.transform.scale(laser_image, (10, 100))

laser_pk_image = pygame.image.load('images/laser_poc_kraj.png')  
laser_pk_image = pygame.transform.scale(laser_pk_image, (30, 30)) 

lik_leti = pygame.image.load('images/lik_leti.png')
lik_leti = pygame.transform.scale(lik_leti, (75, 105)) 

lik_korak = pygame.image.load('images/lik_korak.png')
lik_korak = pygame.transform.scale(lik_korak, (75, 105))

lik_korak2 = pygame.image.load('images/lik_korak2.png')
lik_korak2 = pygame.transform.scale(lik_korak2, (75, 105))

jetpack_image = pygame.image.load('images/jetpack.png')
jetpack_image = pygame.transform.scale(jetpack_image, (30, 50))

star_image = pygame.image.load('images/zvijezda.png')
star_image = pygame.transform.scale(star_image, (20, 20)) 



def generiraj_zvijezdu():
    x = random.randint(WIDTH, WIDTH + 300) 
    y = random.randint(50, HEIGHT - 150)  
    speed = random.randint(2, 5)  
    return {"rect": pygame.Rect(x, y, 20, 20), "speed": speed}

stars = [generiraj_zvijezdu() for _ in range(3)] 



def show_start_screen():
    player_name = ''
    input_active = False 
    input_box = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 20, 300, 50) 
    color_active = pygame.Color('red')
    color_inactive = pygame.Color('black')
    color = color_inactive
    font_input = pygame.font.Font(None, 48)

    while True:
        screen.blit(start_screen_image, (0, 0))
        button_width = 300
        button_height = 80
        button_x = WIDTH // 2 - button_width // 2  
        button_y = HEIGHT // 2 + 100

        start_button = pygame.draw.rect(screen, 'white', [button_x, button_y, button_width, button_height], 0, 15)
        screen.blit(font.render('Start Game', True, 'black'), (button_x + 60, button_y + 20))

        pygame.draw.rect(screen, 'white', input_box)
        pygame.draw.rect(screen, color, input_box, 2) 
        text_surface = font_input.render(player_name, True, 'black')
        screen.blit(text_surface, (input_box.x + 10, input_box.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):  
                    if player_name:
                        player_name = player_name.strip()
                        player_name = player_name.lower()
                        return player_name  
                elif input_box.collidepoint(event.pos): 
                    input_active = True
                    color = color_active
                else:
                    input_active = False
                    color = color_inactive
            if event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_RETURN:  
                    input_active = False
                    color = color_inactive
                elif event.key == pygame.K_BACKSPACE:  
                    player_name = player_name[:-1]
                else:
                    player_name += event.unicode 



def show_end_screen(player_name):
    while True:
        screen.blit(end_screen_image, (0, 0))

        # Leaderboard za najveće rezultate 
        sorted_games = sorted(root.all_games, key=lambda x: x['distance'], reverse=True)

        y_offset = 120
        screen.blit(font.render("Najveći rezultati", True, 'white'), (WIDTH // 4 - 150, 80)) 
        for i, game in enumerate(sorted_games[:5]):
            text = f"{i + 1}. {game['player']}: {game['distance']} m"
            entry = font.render(text, True, 'white')
            screen.blit(entry, (WIDTH // 4 - 150, y_offset))
            y_offset += 50

        # Leaderboard za najviše zvijezda
        sorted_users = sorted(root.users.items(), key=lambda x: x[1].get('lifetime_stars', 0), reverse=True)

        y_offset = 120  
        screen.blit(font.render("Najviše prikupljenih zvijezda", True, 'white'), (3 * WIDTH // 4 - 200, 80))  
        for i, (name, data) in enumerate(sorted_users[:5]):
            lifetime_stars = data.get('lifetime_stars', 0)
            text = f"{i + 1}. {name}: {lifetime_stars} zvijezda"
            entry = font.render(text, True, 'white')
            screen.blit(entry, (3 * WIDTH // 4 - 200, y_offset))
            y_offset += 50


        button_width = 300
        button_height = 80
        button_spacing = 30  
        first_row_y = HEIGHT - 200  
        second_row_y = HEIGHT - 100  


        left_button_x = (WIDTH - (2 * button_width + button_spacing)) // 2  
        retry_button = pygame.draw.rect(screen, 'white', [left_button_x, first_row_y, button_width, button_height], 0, 15)
        screen.blit(font.render('Igraj Ponovno', True, 'black'), (left_button_x + 50, first_row_y + 20))

        exit_button = pygame.draw.rect(screen, 'red', [left_button_x + button_width + button_spacing, first_row_y, button_width, button_height], 0, 15)
        screen.blit(font.render('Izlaz iz igre', True, 'white'), (left_button_x + 50 + button_width + button_spacing, first_row_y + 20))


        second_row_start_x = (WIDTH - (3 * button_width + 2 * button_spacing)) // 2 
        reset_button = pygame.draw.rect(screen, 'red', [second_row_start_x, second_row_y, button_width, button_height], 0, 15)
        screen.blit(font.render('Reset Baze', True, 'black'), (second_row_start_x + 70, second_row_y + 20))

        shop_button = pygame.draw.rect(screen, 'green', [second_row_start_x + button_width + button_spacing, second_row_y, button_width, button_height], 0, 15)
        screen.blit(font.render('Go to Shop', True, 'black'), (second_row_start_x + 70 + button_width + button_spacing, second_row_y + 20))

        stats_button = pygame.draw.rect(screen, 'blue', [second_row_start_x + 2 * (button_width + button_spacing), second_row_y, button_width, button_height], 0, 15)
        screen.blit(font.render('Statistika', True, 'white'), (second_row_start_x + 70 + 2 * (button_width + button_spacing), second_row_y + 20))


        pygame.display.flip()


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if stats_button.collidepoint(event.pos): 
                    show_user_stats(player_name)
                if retry_button.collidepoint(event.pos):  
                    return True 
                if reset_button.collidepoint(event.pos):  #reset baze
                    root.all_games.clear() 
                    root.users.clear()
                    transaction.commit() 
                    connection.close()
                    db.close()
                    pygame.quit()
                    exit()
                if exit_button.collidepoint(event.pos): 
                    transaction.commit()
                    connection.close()
                    db.close()
                    pygame.quit()
                    exit()
                if shop_button.collidepoint(event.pos):
                    show_shop(player_name)



def show_shop(player_name):
    while True:
        screen.fill((0, 0, 0))  
        shop_image = pygame.image.load('images/shop.png') 
        shop_image = pygame.transform.scale(shop_image, (WIDTH, HEIGHT))
        screen.blit(shop_image, (0, 0))

        font_shop = pygame.font.Font(None, 36)
        user_data = root.users[player_name]

        screen.blit(font_shop.render(f"Zvijezde: {user_data['stars']}", True, 'white'), (50, 20))

        jetpack_buttons = []
        jetpack_images = [
            {"name": "jetpack", "price": 0},
            {"name": "jetpack2", "price": 3},
            {"name": "jetpack3", "price": 100},
        ]

        x_offset = 100
        y_offset = 200


        for i, jetpack in enumerate(jetpack_images):
            jetpack_img_path = f'images/{jetpack["name"]}.png'
            jetpack_img = pygame.image.load(jetpack_img_path)
            jetpack_img = pygame.transform.scale(jetpack_img, (200, 200))

            screen.blit(jetpack_img, (x_offset, y_offset))


            if jetpack["name"] == user_data.get('active_jetpack', 'jetpack'):
                button_color = 'yellow'  
                button_text = "Odabran"
            elif jetpack["name"] in user_data['jetpacks']:
                button_color = 'green'  
                button_text = "Odaberi"
            else:
                button_color = 'white'  
                button_text = f"Kupi ({jetpack['price']} *)"


            button_rect = pygame.draw.rect(screen, button_color, (x_offset, y_offset + 220, 200, 50), 0, 15)

            text_surface = font_shop.render(button_text, True, 'black')
            text_rect = text_surface.get_rect(center=(button_rect.x + button_rect.width / 2, button_rect.y + button_rect.height / 2))
            screen.blit(text_surface, text_rect)

            jetpack_buttons.append({"rect": button_rect, "name": jetpack["name"], "price": jetpack["price"]})


            x_offset += 300


        back_button = pygame.draw.rect(screen, 'red', (WIDTH // 2 - 100, HEIGHT - 80, 200, 50), 0, 15)
        back_text = font_shop.render("Natrag", True, 'white')
        back_text_rect = back_text.get_rect(center=(back_button.x + back_button.width / 2, back_button.y + back_button.height / 2))
        screen.blit(back_text, back_text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in jetpack_buttons:
                    if button["rect"].collidepoint(event.pos):
                        jetpack_name = button["name"]
                        if jetpack_name in user_data['jetpacks']: #vec kupljen
                            user_data['active_jetpack'] = jetpack_name
                            transaction.commit()  
                            print(f"Odabrali ste {jetpack_name}!")
                        elif user_data['stars'] >= button["price"]:
                            root.users[player_name]['stars'] -= button["price"]
                            collected_stars = root.users[player_name]['stars']  
                            user_data['jetpacks'].append(jetpack_name)  
                            transaction.commit()  
                            print(f"DEBUG: {player_name} kupio {jetpack_name}. Preostalo: {collected_stars} zvijezda.")
                        else:
                            print(f"Nemate dovoljno zvijezda za {jetpack_name}.")

                        break

                if back_button.collidepoint(event.pos):
                    collected_stars = root.users[player_name]['stars'] 
                    transaction.commit()
                    print(f"DEBUG: Spremanje zvijezda za {player_name} prilikom povratka iz trgovine: {collected_stars}")
                    return


def show_user_stats(player_name):
    user_data = root.users[player_name]

    stats_background = pygame.image.load('images/statistika.png')
    stats_background = pygame.transform.scale(stats_background, (WIDTH, HEIGHT))

    while True:
        screen.blit(stats_background, (0, 0))
        font_stats = pygame.font.Font(None, 36)

        stats = [
            f"Broj odigranih igara: {user_data['games_played']}",
            f"Najveća udaljenost: {user_data['record']} m",
            f"Ukupno zvijezda: {user_data['lifetime_stars']}",
            f"Sudari s laserima: {user_data['crashes_lasers']}",
            f"Sudari s raketama: {user_data['crashes_rockets']}",
        ]

        y_offset = 150
        for stat in stats:
            text_surface = font_stats.render(stat, True, 'white')
            screen.blit(text_surface, (WIDTH // 2 - 250, y_offset))
            y_offset += 50

        back_button = pygame.draw.rect(screen, 'red', (WIDTH // 2 - 100, HEIGHT - 80, 200, 50), 0, 15)
        back_text = font_stats.render("Natrag", True, 'white')
        back_text_rect = back_text.get_rect(center=(back_button.x + back_button.width / 2, back_button.y + back_button.height / 2))
        screen.blit(back_text, back_text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):  
                    return


def show_challenges():
    while True:
        screen.fill((0, 0, 0))  
        challenges_image = pygame.image.load('images/challenges.png')  
        challenges_image = pygame.transform.scale(challenges_image, (WIDTH, HEIGHT))
        screen.blit(challenges_image, (0, 0))
        font_challenges = pygame.font.Font(None, 36)

        y_offset = 150
        current_date = datetime.now().strftime('%Y-%m-%d')
        for challenge in root.daily_challenges:
            if challenge['start_date'] <= current_date <= challenge['end_date']:
                description = f"{challenge['description']} - Nagrada: {challenge['reward']} zvijezda"
                screen.blit(font_challenges.render(description, True, 'white'), (100, y_offset))
                y_offset += 50

        continue_button = pygame.draw.rect(screen, 'green', (WIDTH // 2 - 150, HEIGHT - 100, 300, 50), 0, 15)
        screen.blit(font_challenges.render("Nastavi", True, 'black'), (WIDTH // 2 - 50, HEIGHT - 85))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                transaction.commit()
                connection.close()
                db.close()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_button.collidepoint(event.pos):  
                    return



def show_completed_challenges():
    screen.fill((0, 0, 0))  
    font_completed = pygame.font.Font(None, 36)

    title = font_completed.render("Ispunjeni Izazovi", True, 'white')
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

    y_offset = 150
    for challenge in root.daily_challenges:
        current_date = datetime.now().strftime('%Y-%m-%d')
        if challenge['start_date'] <= current_date <= challenge['end_date']:
            if challenge['challenge_id'] == 1 and collected_stars >= 20:
                text = font_completed.render(challenge['description'], True, 'green')
                screen.blit(text, (50, y_offset))
                y_offset += 50

    pygame.display.flip()
     





def generiraj_sliku(line_list, lase):
    screen.blit(background_image, (0, 0)) 

    for star in stars:
        screen.blit(star_image, (star["rect"].x, star["rect"].y))

    for i in range(len(line_list)):
        pygame.draw.line(screen, 'black', (line_list[i], 0), (line_list[i], 50), 3)
        pygame.draw.line(screen, 'black', (line_list[i], HEIGHT - 50), (line_list[i], HEIGHT), 3)
        if not pause:
            line_list[i] -= game_speed
            lase[0][0] -= game_speed
            lase[1][0] -= game_speed
        if line_list[i] < 0:
            line_list[i] = WIDTH

    screen.blit(okvir_image, (0, 0))  
    screen.blit(okvir_image, (0, HEIGHT - 50)) 

    #horizontalni laser
    if lase[0][1] == lase[1][1]:  
        laser_img = pygame.transform.scale(laser_image, (lase[1][0] - lase[0][0], 20))  
        screen.blit(laser_img, (lase[0][0], lase[0][1] - 10))  
        laser_line = pygame.Rect(lase[0][0], lase[0][1] - 10, lase[1][0] - lase[0][0], 20) 
    else:  #vertikalni laser
        rotated_laser_img = pygame.transform.rotate(laser_image, 90) 
        laser_img = pygame.transform.scale(rotated_laser_img, (20, lase[1][1] - lase[0][1]))  
        screen.blit(laser_img, (lase[0][0] - 10, lase[0][1]))  
        laser_line = pygame.Rect(lase[0][0] - 10, lase[0][1], 20, lase[1][1] - lase[0][1]) 

    screen.blit(laser_pk_image, (lase[0][0] - 15, lase[0][1] - 15))  
    screen.blit(laser_pk_image, (lase[1][0] - 15, lase[1][1] - 15)) 

    screen.blit(font.render(f'Distance: {int(distance)} m', True, 'white'), (10, 10))
    stars_display = root.users[player_name]['stars'] 
    screen.blit(font.render(f'Zvijezde: {stars_display}', True, 'white'), (10, 50))

    top_plat = pygame.Rect(0, 0, WIDTH, 50)
    bot_plat = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)

    return line_list, top_plat, bot_plat, lase, laser_line



def generiraj_igraca():
    global walk_counter
    active_jetpack = root.users.get(player_name, {}).get('active_jetpack', 'jetpack')  
    
    try:
        jetpack_image = pygame.image.load(f'images/{active_jetpack}.png')  
    except FileNotFoundError:
        print(f"Datoteka 'images/{active_jetpack}.png' nije pronađena! Provjeravam zadanu sliku 'jetpack.png'.")
        jetpack_image = pygame.image.load('images/jetpack.png')
    
    jetpack_image = pygame.transform.scale(jetpack_image, (30, 50))
    screen.blit(jetpack_image, (100 - 10, player_y + 20))

    if booster:
        pygame.draw.ellipse(screen, 'red', [100, player_y + 70, 20, 30])
        pygame.draw.ellipse(screen, 'orange', [105, player_y + 75, 10, 20])
        pygame.draw.ellipse(screen, 'yellow', [110, player_y + 80, 5, 15])

    if booster:
        screen.blit(lik_leti, (100, player_y))
    elif player_y >= HEIGHT - 130:
        if walk_counter < 20:
            screen.blit(lik_korak, (100, player_y))
        elif 20 <= walk_counter < 40:
            screen.blit(lik_leti, (100, player_y))
        elif 40 <= walk_counter < 60:
            screen.blit(lik_korak2, (100, player_y))
        elif 60 <= walk_counter < 80:
            screen.blit(lik_leti, (100, player_y))

        walk_counter += 1
        if walk_counter >= 80:
            walk_counter = 0
    else:
        screen.blit(lik_leti, (100, player_y))

    return pygame.Rect((120, player_y + 10), (25, 60))



def provjeri_sudar():
    global stars, collected_stars
    coll = [False, False]
    rstrt = False
    if player.colliderect(bot_plat):
        coll[0] = True
    elif player.colliderect(top_plat):
        coll[1] = True
    if laser_line.colliderect(player):
        root.users[player_name]['crashes_lasers'] += 1 
        transaction.commit()
        rstrt = True
    if rocket_active:
        if rocket.colliderect(player):
            root.users[player_name]['crashes_rockets'] += 1 
            transaction.commit()
            print(f"DEBUG: Sudar s raketom! Ukupno: {root.users[player_name]['crashes_rockets']}")
            rstrt = True
    return coll, rstrt



def generiraj_laser():
    laser_type = random.randint(0, 1)
    offset = random.randint(10, 300)
    if laser_type == 0:
        laser_width = random.randint(100, 300)
        laser_y = random.randint(100, HEIGHT - 100)
        new_lase = [[WIDTH + offset, laser_y], [WIDTH + offset + laser_width, laser_y]]
    else:
        laser_height = random.randint(100, 300)
        laser_y = random.randint(100, HEIGHT - 400)
        new_lase = [[WIDTH + offset, laser_y], [WIDTH + offset, laser_y + laser_height]]
    return new_lase



def generiraj_raketu(coords, mode):
    if mode == 0:  
        rock = screen.blit(oprez_image, (coords[0] - 60, coords[1] - 25))
        if not pause:
            if coords[1] > player_y + 10:
                coords[1] -= 3
            else:
                coords[1] += 3
    else: 
        rock = screen.blit(rocket_image, (coords[0], coords[1] - 10))
        if not pause:
            coords[0] -= 10 + game_speed
    return coords, rock



player_name = show_start_screen()
if '' in root.users:
    del root.users['']
    transaction.commit()
player_name = player_name.strip()        
player_name = player_name.lower()     
print(f"DEBUG: Korisnici u bazi: {list(root.users.keys())}")
print(f"DEBUG: Prijavljeni korisnik: '{player_name}' (duljina = {len(player_name)})")

#provjera korisnika u bazi
if player_name not in root.users:
    root.users[player_name] = PersistentMapping({
        'record': 0,
        'lifetime_stars': 0,
        'games': [],
        'stars': 0,  
        'jetpacks': ['jetpack'],  
        'active_jetpack': 'jetpack',
        'games_played': 0,
        'crashes_lasers': 0,
        'crashes_rockets': 0,
        'completed_challenges': []
    })
    transaction.commit()

user_data = root.users[player_name]  
print("DEBUG: Svi korisnici u bazi:", list(root.users.keys()))
collected_stars = user_data['stars'] 
print(f"Prilikom pokretanja igre za {player_name}, pronađeno {collected_stars} zvijezda.")
print(f"DEBUG: Za korisnika '{player_name}' dohvaćeno {collected_stars} zvijezda iz baze.")




run = True
while run:
    timer.tick(fps)
    if counter < 40:
        counter += 1
    else:
        counter = 0
    if new_laser:
        laser = generiraj_laser()
        new_laser = False
    lines, top_plat, bot_plat, laser, laser_line = generiraj_sliku(lines, laser)
    

    if not rocket_active and not pause:
        rocket_counter += 1
    if rocket_counter > 180:
        rocket_counter = 0
        rocket_active = True
        rocket_delay = 0
        rocket_coords = [WIDTH, HEIGHT / 2]
    if rocket_active:
        if rocket_delay < 90: 
            if not pause:
                rocket_delay += 1
            rocket_coords, rocket = generiraj_raketu(rocket_coords, 0)  
        else:  
            rocket_coords, rocket = generiraj_raketu(rocket_coords, 1)  
        if rocket_coords[0] < -50:  
            rocket_active = False

    player = generiraj_igraca()

    for star in stars[:]:
        if player.colliderect(star["rect"]):  
            stars.remove(star)  
            root.users[player_name]['stars'] += 1 
            root.users[player_name]['lifetime_stars'] += 1 
            collected_stars = root.users[player_name]['stars']
            transaction.commit()
            print(f"DEBUG: {player_name} lifetime_stars: {root.users[player_name]['lifetime_stars']}")
            stars.append(generiraj_zvijezdu())


    colliding, restart_cmd = provjeri_sudar()

    for challenge in root.daily_challenges:
        current_date = datetime.now().strftime('%Y-%m-%d')
        if challenge['start_date'] <= current_date <= challenge['end_date']:
            if challenge['challenge_id'] not in root.users[player_name]['completed_challenges']:
                if challenge['challenge_id'] == 1 and collected_stars >= 20:
                    root.users[player_name]['stars'] += challenge['reward']
                    root.users[player_name]['completed_challenges'].append(challenge['challenge_id'])
                    print(f"Izazov '{challenge['description']}' ispunjen! Dobivaš {challenge['reward']} zvijezda.")
                elif challenge['challenge_id'] == 2 and root.users[player_name]['crashes_rockets'] >= 5:
                    root.users[player_name]['stars'] += challenge['reward']
                    root.users[player_name]['completed_challenges'].append(challenge['challenge_id'])
                    print(f"Izazov '{challenge['description']}' ispunjen! Dobivaš {challenge['reward']} zvijezda.")
                elif challenge['challenge_id'] == 3 and distance >= 1000:
                    root.users[player_name]['stars'] += challenge['reward']
                    root.users[player_name]['completed_challenges'].append(challenge['challenge_id'])
                    print(f"Izazov '{challenge['description']}' ispunjen! Dobivaš {challenge['reward']} zvijezda.")
    transaction.commit()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            transaction.commit()
            connection.close()
            db.close()
            pygame.quit()
            exit() 
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:  
                booster = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE: 
                booster = False
        if booster:  
            if player_y > TOP_MARGIN:  
                player_y -= 5
        else:  
            if player_y < HEIGHT - BOTTOM_MARGIN:  
                player_y += 5
            elif player_y > HEIGHT - BOTTOM_MARGIN:  
                player_y = HEIGHT - BOTTOM_MARGIN

    if not pause:
        distance += game_speed
        if booster:
            y_velocity -= gravity
        else:
            y_velocity += gravity
        if (colliding[0] and y_velocity > 0) or (colliding[1] and y_velocity < 0):
            y_velocity = 0
        player_y += y_velocity

    if distance < 20000:
        game_speed = 1 + (distance // 500) / 10
    else:
        game_speed = 11

    if laser[0][0] < 0 and laser[1][0] < 0:
        new_laser = True

    if distance > root.users[player_name]['record']:
        root.users[player_name]['record'] = int(distance)
    transaction.commit()

    if restart_cmd:
        root.users[player_name]['games_played'] += 1
        user_data = root.users[player_name] 
        collected_stars = user_data['stars'] 
        transaction.commit()
        print(f"Ažurirane zvijezde za igrača {player_name}: {collected_stars}")

        root.all_games.append({
            'player': player_name,
            'distance': int(distance),
            'stars': collected_stars
                })
        transaction.commit()  
        print(f"Dodan zapis za igrača {player_name}: {distance}m, {collected_stars} zvijezde.")


        show_challenges()
        if not show_end_screen(player_name):  
            break  

        if not show_end_screen(player_name):  
            break  


        show_end_screen(player_name)
        distance = 0
        rocket_active = False
        rocket_counter = 0
        pause = False
        player_y = init_y
        y_velocity = 0
        restart_cmd = 0
        new_laser = True

    if distance > high_score:
        high_score = int(distance)
    
    for star in stars[:]:  
        star["rect"].x -= star["speed"]  
        if star["rect"].x < -20:  
            stars.remove(star) 
            stars.append(generiraj_zvijezdu())  

    pygame.display.flip()





