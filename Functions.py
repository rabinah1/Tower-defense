import pygame
import sys
from pygame.locals import QUIT, K_ESCAPE
from Towersprite import (Machine_gun_tower, Shotgun_tower, Assistant_tower, Pistol_tower, Mine,
                         Smart_bomb, Homing_missile_tower)
from math import sqrt, ceil
from Bulletsprite import Bullet
from Enemysprite import Enemy
from common import BLACK, GREEN, WHITE, RED, BLUE, GRAY, black_monster
import sqlite3
import time


WEAPON_TYPE_TO_PROPERTIES = {
    "machine_gun": {
        "image_small": lambda param_dict: param_dict["machine_gun_small"],
        "class": Machine_gun_tower
    },
    "shotgun": {
        "image_small": lambda param_dict: param_dict["shotgun_small"],
        "class": Shotgun_tower
    },
    "assistant": {
        "image_small": lambda param_dict: param_dict["assistant_small"],
        "class": Assistant_tower
    },
    "pistol": {
        "image_small": lambda param_dict: param_dict["pistol_small"],
        "class": Pistol_tower
    },
    "mine": {
        "image_small": lambda param_dict: param_dict["mine_small"],
        "class": Mine
    },
    "smart_bomb": {
        "image_small": lambda param_dict: param_dict["smart_bomb_small"],
        "class": Smart_bomb
    },
    "homing_missile": {
        "image_small": lambda param_dict: param_dict["homing_missile_small"],
        "class": Homing_missile_tower
    }
}


def update_enemies(param_dict, window, player):
    for enemy in param_dict["enemy_list"]:
        if enemy.direction == "up" or enemy.direction == "down":
            window.blit((param_dict["font"].render(str(enemy.health), True, BLACK)),
                        (enemy.rect.centerx + 16, enemy.rect.centery - 7))
        elif enemy.direction == "left" or enemy.direction == "right":
            window.blit((param_dict["font"].render(str(enemy.health), True, BLACK)),
                        (enemy.rect.x, enemy.rect.centery - 28))
        if enemy.health <= 0:
            enemy.kill()
            player.Money += enemy.price
        # Enemy goes outside the game field
        if (enemy.rect.centerx < 0 or enemy.rect.centerx > 1500 or
           enemy.rect.centery < 0 or enemy.rect.centery > 700):
            enemy.kill()
            player.Lives -= 1
            if player.Lives <= 0:
                game_over(window)
                param_dict["tower_list"].empty()
                param_dict["bullet_list"].empty()
                param_dict["enemy_list"].empty()
                param_dict["dictionary"].clear()
                param_dict["contact_bomb_list"].empty()
                param_dict["range_bomb_list"].empty()
                param_dict["missile_list"].empty()
                del param_dict["range_list"][:]
                del param_dict["value_list"][:]
                return "return_menu"

        for bullet in param_dict["bullet_list"]:
            if pygame.sprite.collide_rect(bullet, enemy):
                if bullet.type != enemy.immunity:
                    enemy.health -= bullet.damage
                    if bullet.poison == 1 and enemy.poison == 0:
                        enemy.poison = 1
                        enemy.poison_time = time.monotonic()
                    if bullet.is_assistant:
                        if enemy.speed == 2:
                            enemy.speed = 1
                        if enemy.immunity != 5:
                            enemy.immunity = 5
                        enemy.image = black_monster
                bullet.kill()
        for bullet in param_dict["missile_list"]:
            bullet.target = [bullet.target_enemy.rect.centerx,
                             bullet.target_enemy.rect.centery]
            if pygame.sprite.collide_rect(bullet, enemy):
                if bullet.type != enemy.immunity:
                    enemy.health -= bullet.damage
                    if bullet.poison == 1 and enemy.poison == 0:
                        enemy.poison = 1
                        enemy.poison_time = time.monotonic()
                bullet.kill()


def process_contact_bombs(param_dict, xpos, ypos, window, check_mouse):
    for tower in param_dict["contact_bomb_list"]:
        if (check_mouse and xpos > (tower.rect.centerx-10) and xpos < (tower.rect.centerx+10) and
           ypos > (tower.rect.centery-10) and ypos < (tower.rect.centery+10)):
            pygame.draw.circle(window, BLUE, (tower.rect.centerx, tower.rect.centery), 100, 1)
        for enemy in param_dict["enemy_list"]:
            if pygame.sprite.collide_rect(tower, enemy):
                enemy.health -= tower.damage
                tower.kill()


def process_range_bombs(param_dict, xpos, ypos, window, mouse_check):
    for tower in param_dict["range_bomb_list"]:
        if (mouse_check and xpos > (tower.rect.centerx-10) and xpos < (tower.rect.centerx+10) and
           ypos > (tower.rect.centery-10) and ypos < (tower.rect.centery+10)):
            pygame.draw.circle(window, BLUE, (tower.rect.centerx, tower.rect.centery), 100, 1)
        for enemy in param_dict["enemy_list"]:
            enemy.dist = sqrt((enemy.rect.centerx - tower.rect.centerx)**2 +
                              (enemy.rect.centery - tower.rect.centery)**2)
            if enemy.dist <= 100 and tower.number == 0:
                tower.elist.append(enemy)
        if len(tower.elist) >= 5:
            if tower.number == 0:
                tower.t = float(time.monotonic())
                for enemy in tower.elist:
                    enemy.health -= 100
            tower.number = 1
            tower.elist = [0, 1, 2, 3, 4]
            if float(time.monotonic()) - tower.t < 1.0:
                pygame.draw.circle(window, RED, (tower.rect.centerx, tower.rect.centery), 100, 0)
            else:
                tower.kill()
        if tower.number == 0:
            del tower.elist[:]


def process_towers(param_dict, xpos, ypos, window, check_mouse):
    for tower in param_dict["tower_list"]:
        if tower.pipe_up:
            tower.x0 = tower.rect.centerx
            tower.y0 = tower.rect.centery - 12
            tower.pipe_up = False
        pygame.draw.line(window, BLACK, (tower.rect.centerx, tower.rect.centery),
                         (tower.x0, tower.y0), 1)
        if (check_mouse and xpos > (tower.rect.centerx-10) and xpos < (tower.rect.centerx+10) and
           ypos > (tower.rect.centery-10) and ypos < (tower.rect.centery+10)):
            pygame.draw.circle(window, BLUE, (tower.rect.centerx, tower.rect.centery),
                               tower.range, 1)
        for enemy in param_dict["enemy_list"]:
            enemy.dist = sqrt((enemy.rect.centerx - tower.rect.centerx)**2 +
                              (enemy.rect.centery - tower.rect.centery)**2)
            if enemy.dist <= tower.range:
                param_dict["range_list"].append(enemy)
                param_dict["dictionary"][enemy.travelled] = enemy
                param_dict["value_list"].append(enemy.travelled)

        param_dict["value_list"].sort()
        param_dict["value_list"].reverse()
        # Check if enough time has passed from the previous shot so that we can shoot again
        if (float(time.monotonic()) - float(tower.beginning) >= tower.interval and
           (param_dict["value_list"])):
            # Set the target to be the enemy that has travelled the longest distance.
            target = [param_dict["dictionary"][param_dict["value_list"][0]].rect.centerx,
                      param_dict["dictionary"][param_dict["value_list"][0]].rect.centery]
            startpoint = [tower.rect.centerx, tower.rect.centery]
            tower.x0 = (startpoint[0] + 12*(target[0]-startpoint[0]) /
                        param_dict["dictionary"][param_dict["value_list"][0]].dist)
            tower.y0 = (startpoint[1] + 12*(target[1]-startpoint[1]) /
                        param_dict["dictionary"][param_dict["value_list"][0]].dist)
            pygame.draw.line(window, BLACK, (startpoint[0], startpoint[1]),
                             (round(tower.x0), round(tower.y0)), 1)
            damage = tower.damage
            poison = tower.poison
            bullet = Bullet(target, startpoint, damage, poison, tower.is_assistant,
                            tower.bullet_type,
                            param_dict["dictionary"][param_dict["value_list"][0]])
            if tower.homing == 0:
                param_dict["bullet_list"].add(bullet)
            elif tower.homing == 1:
                param_dict["missile_list"].add(bullet)
            tower.beginning = time.monotonic()  # The moment when a tower shoots a bullet
        del param_dict["value_list"][:]
        del param_dict["range_list"][:]
        param_dict["dictionary"].clear()


def set_weapon(param_dict, window, pieces_list, round_stats,
               Delta, round_idx, player, start, field, jump_rounds,
               environment_list, weapon_type):
    initial_time = time.monotonic()
    if weapon_type == "mine" or weapon_type == "smart_bomb":
        gun = WEAPON_TYPE_TO_PROPERTIES[weapon_type]["class"](
            WEAPON_TYPE_TO_PROPERTIES[weapon_type]["image_small"](param_dict))
    else:
        gun = WEAPON_TYPE_TO_PROPERTIES[weapon_type]["class"](
            WEAPON_TYPE_TO_PROPERTIES[weapon_type]["image_small"](param_dict), initial_time)
    while True:
        gun.rect.centerx = pygame.mouse.get_pos()[0]
        gun.rect.centery = pygame.mouse.get_pos()[1]
        (round_stats, Delta, round_idx) = \
            draw_game_dynamic(param_dict, window, pieces_list, round_stats, Delta, round_idx,
                              player, start, field, jump_rounds, gun, weapon_type,
                              environment_list)
        if (round_stats, Delta, round_idx) == (None, None, None):
            return (None, None, None, None)
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                gun.rect.centerx = pygame.mouse.get_pos()[0]
                gun.rect.centery = pygame.mouse.get_pos()[1]
                if (gun.price > player.Money or gun.rect.centerx >= 1178 or
                   (gun.rect.centerx <= 60 and gun.rect.centery <= 60)):
                    gun.kill()
                    initial_time = 0
                    return (None, round_stats, Delta, round_idx)
                for piece in pieces_list:
                    if pygame.sprite.collide_rect(gun, piece) and weapon_type != "mine":
                        gun.kill()
                        initial_time = 0
                        return (None, round_stats, Delta, round_idx)
                for r in param_dict["tower_list"]:
                    if pygame.sprite.collide_rect(r, gun):
                        gun.kill()
                        initial_time = 0
                        return (None, round_stats, Delta, round_idx)
                for r in param_dict["contact_bomb_list"]:
                    if pygame.sprite.collide_rect(r, gun):
                        gun.kill()
                        initial_time = 0
                        return (None, round_stats, Delta, round_idx)
                for r in param_dict["range_bomb_list"]:
                    if pygame.sprite.collide_rect(r, gun):
                        gun.kill()
                        initial_time = 0
                        return (None, round_stats, Delta, round_idx)
                for r in environment_list:
                    if pygame.sprite.collide_rect(r, gun):
                        gun.kill()
                        initial_time = 0
                        return (None, round_stats, Delta, round_idx)
                player.Money -= gun.price
                return (gun, round_stats, Delta, round_idx)
    return (gun, round_stats, Delta, round_idx)


def Initialize():
    font = pygame.font.SysFont('Calibri', 14, True, False)
    start_font = pygame.font.SysFont('Calibri', 45, True, False)
    info_font = pygame.font.SysFont('Calibri', 30, True, False)
    update_font = pygame.font.SysFont('Calibri', 20, True, False)
    welcome_font = pygame.font.SysFont('Calibri', 120, True, False)
    welcome_1 = welcome_font.render("TOWER", True, RED)
    welcome_2 = welcome_font.render("DEFENSE", True, RED)
    money_text = update_font.render("Money", True, BLACK)
    round_text = update_font.render("Round", True, BLACK)
    lives_text = update_font.render("Lives", True, BLACK)
    machine_gun_text = font.render("Machine gun", True, BLACK)
    shotgun_text = font.render("Shotgun", True, BLACK)
    assistant_text = font.render("Assistant", True, BLACK)
    pistol_text = font.render("Pistol", True, BLACK)
    mine_text = font.render("Mine", True, BLACK)
    smart_bomb_text = font.render("Smart bomb", True, BLACK)
    homing_missile_text = font.render("Homing missile", True, BLACK)
    homing_missile_price = font.render("500$", True, BLACK)
    machine_gun_price = font.render("350$", True, BLACK)
    shotgun_price = font.render("450$", True, BLACK)
    assistant_price = font.render("300$", True, BLACK)
    pistol_price = font.render("200$", True, BLACK)
    mine_price = font.render("150$", True, BLACK)
    smart_bomb_price = font.render("300$", True, BLACK)
    start_text = start_font.render("Start Round", True, BLACK)
    update_range_text = update_font.render("Update fire range", True, BLACK)
    update_range_price = update_font.render("100$", True, BLACK)
    update_rate_text = update_font.render("Update fire rate", True, BLACK)
    update_rate_price = update_font.render("250$", True, BLACK)
    update_damage_text = update_font.render("Increase damage", True, BLACK)
    update_damage_price = update_font.render("300$", True, BLACK)
    info_text = info_font.render("Click on the map you want to start the game or press EXIT "
                                 "if you want to quit. Press INSTRUCTIONS to learn how to play.",
                                 True, BLACK)
    exit_text = start_font.render("EXIT", True, BLACK)
    instructions_text = start_font.render("INSTRUCTIONS", True, BLACK)
    tower_list = pygame.sprite.Group()
    bullet_list = pygame.sprite.Group()
    missile_list = pygame.sprite.Group()
    contact_bomb_list = pygame.sprite.Group()
    range_bomb_list = pygame.sprite.Group()
    enemy_list = pygame.sprite.Group()
    homing_missile = pygame.image.load("homing_missile.jpg")
    homing_missile_small = pygame.image.load("homing_missile_small.jpg")
    shotgun = pygame.image.load("shotgun.jpg")
    machine_gun = pygame.image.load("machine_gun.jpg")
    assistant = pygame.image.load("assistant.jpg")
    pistol = pygame.image.load("pistol.jpg")
    shotgun_small = pygame.image.load("shotgun_small.jpg")
    machine_gun_small = pygame.image.load("machine_gun_small.jpg")
    pistol_small = pygame.image.load("pistol_small.jpg")
    assistant_small = pygame.image.load("assistant_small.jpg")
    poison_text = update_font.render("Add poison", True, BLACK)
    poison_price = update_font.render("300$", True, BLACK)
    mine = pygame.image.load("mine.jpg")
    mine_small = pygame.image.load("mine_small.jpg")
    smart_bomb = pygame.image.load("smart_bomb.jpg")
    smart_bomb_small = pygame.image.load("smart_bomb_small.jpg")
    tree = pygame.image.load("tree.jpg")
    lake = pygame.image.load("lake.jpg")
    tree_2 = pygame.image.load("tree_2.jpg")
    map_1 = pygame.image.load("map_1.jpg")
    map_2 = pygame.image.load("map_2.jpg")
    map_3 = pygame.image.load("map_3.jpg")
    map_4 = pygame.image.load("map_4.jpg")
    range_list = []
    value_list = []
    dictionary = {}
    param_dict = {
        "machine_gun_text": machine_gun_text,
        "shotgun_text": shotgun_text,
        "assistant_text": assistant_text,
        "pistol_text": pistol_text,
        "machine_gun_price": machine_gun_price,
        "shotgun_price": shotgun_price,
        "assistant_price": assistant_price,
        "pistol_price": pistol_price,
        "start_text": start_text,
        "update_range_text": update_range_text,
        "update_range_price": update_range_price,
        "update_rate_text": update_rate_text,
        "update_rate_price": update_rate_price,
        "update_damage_text": update_damage_text,
        "update_damage_price": update_damage_price,
        "tower_list": tower_list,
        "bullet_list": bullet_list,
        "enemy_list": enemy_list,
        "shotgun": shotgun,
        "machine_gun": machine_gun,
        "assistant": assistant,
        "pistol": pistol,
        "shotgun_small": shotgun_small,
        "machine_gun_small": machine_gun_small,
        "pistol_small": pistol_small,
        "assistant_small": assistant_small,
        "money_text": money_text,
        "round_text": round_text,
        "lives_text": lives_text,
        "range_list": range_list,
        "value_list": value_list,
        "dictionary": dictionary,
        "info_text": info_text,
        "exit_text": exit_text,
        "welcome_1": welcome_1,
        "welcome_2": welcome_2,
        "map_1": map_1,
        "map_2": map_2,
        "map_3": map_3,
        "map_4": map_4,
        "poison_text": poison_text,
        "poison_price": poison_price,
        "update_font": update_font,
        "instructions_text": instructions_text,
        "mine": mine,
        "mine_small": mine_small,
        "mine_text": mine_text,
        "mine_price": mine_price,
        "contact_bomb_list": contact_bomb_list,
        "font": font, "tree": tree,
        "lake": lake,
        "tree_2": tree_2,
        "smart_bomb": smart_bomb,
        "smart_bomb_small": smart_bomb_small,
        "smart_bomb_text": smart_bomb_text,
        "smart_bomb_price": smart_bomb_price,
        "range_bomb_list": range_bomb_list,
        "homing_missile": homing_missile,
        "homing_missile_small": homing_missile_small,
        "homing_missile_text": homing_missile_text,
        "homing_missile_price": homing_missile_price,
        "missile_list": missile_list}
    return param_dict


def draw_menu(window, param_dict):
    window.fill(WHITE)
    pygame.draw.line(window, BLACK, (780, 600), (900, 600), 2)
    pygame.draw.line(window, BLACK, (780, 600), (780, 670), 2)
    pygame.draw.line(window, BLACK, (900, 600), (900, 670), 2)
    pygame.draw.line(window, BLACK, (780, 670), (900, 670), 2)
    pygame.draw.line(window, BLACK, (380, 595), (380, 670), 2)
    pygame.draw.line(window, BLACK, (380, 595), (695, 595), 2)
    pygame.draw.line(window, BLACK, (695, 595), (695, 670), 2)
    pygame.draw.line(window, BLACK, (380, 670), (695, 670), 2)
    window.blit(param_dict["instructions_text"], (400, 615))
    window.blit(param_dict["info_text"], (2, 550))
    window.blit(param_dict["exit_text"], (800, 615))
    window.blit(param_dict["welcome_1"], (550, 150))
    window.blit(param_dict["welcome_2"], (520, 300))
    window.blit(param_dict["map_1"], (70, 30))
    window.blit(param_dict["map_2"], (1000, 30))
    window.blit(param_dict["map_3"], (70, 300))
    window.blit(param_dict["map_4"], (1000, 300))
    return


def draw_game_static(window, param_dict, pieces_list, player, environment_list):
    pygame.draw.rect(window, GREEN, (0, 0, 1177, 700), 0)
    pieces_list.draw(window)
    environment_list.draw(window)
    pygame.draw.rect(window, WHITE, (1180, 0, 1500, 700), 0)
    pygame.draw.line(window, BLACK, (1178, 0), (1178, 700), 3)
    pygame.draw.line(window, BLACK, (1180, 110), (1500, 110), 3)
    pygame.draw.line(window, BLACK, (1180, 600), (1500, 600), 3)
    pygame.draw.line(window, BLACK, (1340, 310), (1340, 600), 3)
    pygame.draw.line(window, BLACK, (1180, 455), (1500, 455), 3)
    pygame.draw.line(window, BLACK, (1180, 310), (1500, 310), 3)
    pygame.draw.line(window, BLACK, (1180, 220), (1500, 220), 3)
    window.blit(param_dict["machine_gun"], (1420, 0))
    window.blit(param_dict["machine_gun_text"], (1422, 80))
    window.blit(param_dict["machine_gun_price"], (1445, 95))
    window.blit(param_dict["shotgun"], (1340, 0))
    window.blit(param_dict["shotgun_text"], (1350, 80))
    window.blit(param_dict["shotgun_price"], (1362, 95))
    window.blit(param_dict["assistant"], (1260, 0))
    window.blit(param_dict["assistant_text"], (1275, 80))
    window.blit(param_dict["assistant_price"], (1288, 95))
    window.blit(param_dict["pistol"], (1180, 0))
    window.blit(param_dict["pistol_text"], (1200, 80))
    window.blit(param_dict["pistol_price"], (1203, 95))
    window.blit(param_dict["start_text"], (1230, 630))
    window.blit(param_dict["update_range_text"], (1185, 370))
    window.blit(param_dict["update_range_price"], (1240, 390))
    window.blit(param_dict["update_rate_text"], (1350, 370))
    window.blit(param_dict["update_rate_price"], (1400, 390))
    window.blit(param_dict["update_damage_text"], (1190, 500))
    window.blit(param_dict["update_damage_price"], (1240, 520))
    window.blit(param_dict["round_text"], (1210, 240))
    window.blit(param_dict["money_text"], (1310, 240))
    window.blit(param_dict["lives_text"], (1410, 240))
    window.blit(param_dict["poison_text"], (1370, 500))
    window.blit(param_dict["poison_price"], (1395, 520))
    window.blit(param_dict["mine"], (1180, 112))
    window.blit(param_dict["mine_text"], (1205, 192))
    window.blit(param_dict["mine_price"], (1205, 205))
    window.blit(param_dict["smart_bomb"], (1260, 112))
    window.blit(param_dict["homing_missile"], (1340, 112))
    window.blit(param_dict["homing_missile_text"], (1340, 192))
    window.blit(param_dict["homing_missile_price"], (1368, 205))
    window.blit(param_dict["smart_bomb_text"], (1267, 192))
    window.blit(param_dict["smart_bomb_price"], (1286, 205))
    window.blit((param_dict["update_font"].render(str(player.Money), True, BLACK)), (1320, 270))
    window.blit((param_dict["update_font"].render(str(player.Lives), True, BLACK)), (1420, 270))
    window.blit((param_dict["update_font"].render(str(player.Round), True, BLACK)), (1217, 270))
    window.blit(param_dict["update_font"].render("/", True, BLACK), (1237, 270))
    window.blit(param_dict["update_font"].render("10", True, BLACK), (1245, 270))


def draw_game_dynamic(param_dict, window, pieces_list, round_stats, Delta,
                      round_idx, player, start, field, jump_rounds, gun,
                      weapon_type, environment_list):
    clock = pygame.time.Clock()
    if (float(time.monotonic()) - Delta > 0.5 and round_idx < len(round_stats) and
       round_idx != -1):
        param_dict["enemy_list"].add(round_stats[round_idx])
        Delta = float(time.monotonic())
        if (len(round_stats) - round_idx == 1):
            del round_stats[:]
            round_idx = -1
        else:
            round_idx += 1
    draw_game_static(window, param_dict, pieces_list, player, environment_list)
    pygame.draw.circle(window, BLUE, (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]),
                       gun.range, 1)

    if weapon_type != "mine":
        for piece in pieces_list:
            if pygame.sprite.collide_rect(gun, piece):
                pygame.draw.circle(window, RED, (pygame.mouse.get_pos()[0],
                                                 pygame.mouse.get_pos()[1]), gun.range, 1)
    for r in param_dict["tower_list"]:
        if pygame.sprite.collide_rect(r, gun):
            pygame.draw.circle(window, RED, (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]),
                               gun.range, 1)
    for r in param_dict["contact_bomb_list"]:
        if pygame.sprite.collide_rect(r, gun):
            pygame.draw.circle(window, RED, (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]),
                               gun.range, 1)
    for r in param_dict["range_bomb_list"]:
        if pygame.sprite.collide_rect(r, gun):
            pygame.draw.circle(window, RED, (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]),
                               gun.range, 1)
    for r in environment_list:
        if pygame.sprite.collide_rect(r, gun):
            pygame.draw.circle(window, RED, (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]),
                               gun.range, 1)
    if gun.rect.centerx >= 1178 or (gun.rect.centerx <= 60 and gun.rect.centery <= 60):
        pygame.draw.circle(window, RED, (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]),
                           gun.range, 1)

    window.blit(WEAPON_TYPE_TO_PROPERTIES[weapon_type]["image_small"](param_dict),
                (pygame.mouse.get_pos()[0]-10, pygame.mouse.get_pos()[1]-10))
    param_dict["tower_list"].draw(window)
    param_dict["contact_bomb_list"].draw(window)
    param_dict["range_bomb_list"].draw(window)

    if update_enemies(param_dict, window, player) == "return_menu":
        return (None, None, None)
    process_contact_bombs(param_dict, 0, 0, window, False)
    process_range_bombs(param_dict, 0, 0, window, False)
    process_towers(param_dict, 0, 0, window, False)

    for tower in param_dict["tower_list"]:
        if tower.pipe_up:
            tower.x0 = tower.rect.centerx
            tower.y0 = tower.rect.centery - 12
            tower.pipe_up = False
        pygame.draw.line(window, BLACK, (tower.rect.centerx, tower.rect.centery),
                         (tower.x0, tower.y0), 1)
        for enemy in param_dict["enemy_list"]:
            if (enemy.health <= 0):
                enemy.kill()
                player.Money += enemy.price
            enemy.dist = sqrt((enemy.rect.centerx - tower.rect.centerx)**2 +
                              (enemy.rect.centery - tower.rect.centery)**2)
            if enemy.dist <= tower.range:
                param_dict["range_list"].append(enemy)
                param_dict["dictionary"][enemy.travelled] = enemy
                param_dict["value_list"].append(enemy.travelled)

        param_dict["value_list"].sort()
        param_dict["value_list"].reverse()
        if (float(time.monotonic()) - float(tower.beginning) >= tower.interval and
           (param_dict["value_list"])):
            target = [param_dict["dictionary"][param_dict["value_list"][0]].rect.centerx,
                      param_dict["dictionary"][param_dict["value_list"][0]].rect.centery]
            startpoint = [tower.rect.centerx, tower.rect.centery]
            tower.x0 = (startpoint[0] + 12*(target[0]-startpoint[0]) /
                        param_dict["dictionary"][param_dict["value_list"][0]].dist)
            tower.y0 = (startpoint[1] + 12*(target[1]-startpoint[1]) /
                        param_dict["dictionary"][param_dict["value_list"][0]].dist)
            pygame.draw.line(window, BLACK, (startpoint[0], startpoint[1]),
                             (round(tower.x0), round(tower.y0)), 1)
            damage = tower.damage
            poison = tower.poison
            bullet = Bullet(target, startpoint, damage, poison, tower.is_assistant,
                            tower.bullet_type,
                            param_dict["dictionary"][param_dict["value_list"][0]])
            if tower.homing == 0:
                param_dict["bullet_list"].add(bullet)
            elif tower.homing == 1:
                param_dict["missile_list"].add(bullet)
            tower.beginning = time.monotonic()
        del param_dict["value_list"][:]
        del param_dict["range_list"][:]
        param_dict["dictionary"].clear()

    if jump_rounds == 0 and field.map_number == 1:
        window.blit(start, (5, 315))
    elif jump_rounds == 0 and field.map_number == 2:
        window.blit(start, (5, 67))
    elif jump_rounds == 0 and field.map_number == 3:
        window.blit(start, (570, 670))
    elif jump_rounds == 0 and field.map_number == 4:
        window.blit(start, (620, 670))
    param_dict["bullet_list"].update()
    param_dict["enemy_list"].update()
    param_dict["missile_list"].update()
    param_dict["bullet_list"].draw(window)
    param_dict["enemy_list"].draw(window)
    param_dict["missile_list"].draw(window)
    del param_dict["value_list"][:]
    del param_dict["range_list"][:]
    param_dict["dictionary"].clear()
    pygame.display.update()
    clock.tick(60)
    return (round_stats, Delta, round_idx)


def read(field, table_id, jump_rounds, player, window, database):
    try:
        table = sqlite3.connect(database)
        cursor = table.cursor()
        player.Round += 1  # Add one completed round.
        round_stats = []  # List, that contains the information about enemies.
        health = 0  # Health of the enemy.
        speed = 0  # Speed of the enemy.
        color = " "  # The color of the enemy.
        i = 0

        while (i < jump_rounds):
            i += 1

        if (table_id == "1"):
            cursor.execute("SELECT * FROM field1 WHERE roundNum=" + str(i+1))
        elif (table_id == "2"):
            cursor.execute("SELECT * FROM field2 WHERE roundNum=" + str(i+1))
        elif (table_id == "3"):
            cursor.execute("SELECT * FROM field3 WHERE roundNum=" + str(i+1))
        elif (table_id == "4"):
            cursor.execute("SELECT * FROM field4 WHERE roundNum=" + str(i+1))
        result = cursor.fetchall()
        if player.Round > 10:
            win(window)
            round_stats.append("RET")
            return round_stats
        for r in result:
            health = r[0]
            money = r[1]
            color = r[2]
            speed = r[3]
            immunity = r[4]
            if (speed == "slow"):
                speed = 1
            elif (speed == "fast"):
                speed = 2
            enemy = Enemy(health, speed, money, color, immunity, field.get_crit_points())
            enemy.rect.centerx = field.get_startx()
            enemy.rect.centery = field.get_starty()
            round_stats.append(enemy)
        return round_stats
    except ValueError:
        print("Reading the file failed!")
        round_stats = []
        round_stats.append("RET")
        return round_stats


def draw_while_update(param_dict, window, pieces_list, round_stats, Delta, round_idx, tower_A,
                      player, start, field, jump_rounds, environment_list, updateable):
    clock = pygame.time.Clock()
    while True:
        pos = pygame.mouse.get_pos()
        xpos = pos[0]
        ypos = pos[1]
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if param_dict["tower_list"].has(tower_A):
                # The player clicks on the "update range"-button
                if (event.type == pygame.MOUSEBUTTONDOWN and xpos > 1180 and xpos < 1340 and
                   ypos > 310 and ypos < 455 and updateable):
                    if player.Money >= 100 and not tower_A.range_state:
                        tower_A.range += 20
                        tower_A.range_state = True
                        tower_A.price += 100
                        player.Money -= 100
                        return (tower_A, round_stats, Delta, round_idx)

                # The player clicks on the "update fire rate"-button
                elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 1340 and xpos < 1500 and
                      ypos > 310 and ypos < 455 and updateable):
                    if player.Money >= 250 and not tower_A.rate_state:
                        tower_A.interval -= tower_A.interval*0.4
                        tower_A.rate_state = True
                        tower_A.price += 250
                        player.Money -= 250
                        return (tower_A, round_stats, Delta, round_idx)

                # The player clicks on the "update damage"-button
                elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 1180 and xpos < 1340 and
                      ypos > 455 and ypos < 600 and updateable):
                    if player.Money >= 300 and not tower_A.damage_state:
                        tower_A.damage += ceil(tower_A.damage*0.5)
                        tower_A.damage_state = True
                        tower_A.price += 300
                        player.Money -= 300
                        return (tower_A, round_stats, Delta, round_idx)

                # The player clicks on the "add poison"-button
                elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 1340 and xpos < 1500 and
                      ypos > 455 and ypos < 600 and updateable):
                    if player.Money >= 300 and not tower_A.poison_state:
                        tower_A.poison = 1
                        tower_A.poison_state = True
                        tower_A.price += 300
                        player.Money -= 300
                        return (tower_A, round_stats, Delta, round_idx)

            # The player clicks on the chosen tower again
            if (event.type == pygame.MOUSEBUTTONDOWN and xpos > (tower_A.rect.centerx-10) and
               xpos < (tower_A.rect.centerx+10) and ypos > (tower_A.rect.centery-10) and
               ypos < (tower_A.rect.centery+10)):
                return (tower_A, round_stats, Delta, round_idx)

            # The player presses button d to sell the chosen tower.
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                tower_A.kill()
                player.Money += round(tower_A.price*0.7)
                return (tower_A, round_stats, Delta, round_idx)

            # The player clicks on the pause button
            elif event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                diff = float(time.monotonic()) - Delta
                while True:
                    n = 0
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
                            n = 1
                            break
                        if event.type == QUIT:
                            pygame.quit()
                            sys.exit()
                    if n == 1:
                        Delta = float(time.monotonic()) - diff
                        break

        if (float(time.monotonic()) - Delta > 0.5 and round_idx < len(round_stats) and
           round_idx != -1):
            param_dict["enemy_list"].add(round_stats[round_idx])
            Delta = float(time.monotonic())
            if (len(round_stats) - round_idx == 1):
                del round_stats[:]
                round_idx = -1
            else:
                round_idx += 1
        draw_game_static(window, param_dict, pieces_list, player, environment_list)

        if param_dict["tower_list"].has(tower_A):
            if tower_A.range_state:
                pygame.draw.rect(window, BLUE, (1180, 310, 160, 145), 0)
                window.blit(param_dict["update_range_text"], (1185, 370))
                window.blit(param_dict["update_range_price"], (1240, 390))
            if tower_A.rate_state:
                pygame.draw.rect(window, BLUE, (1340, 310, 160, 145), 0)
                window.blit(param_dict["update_rate_text"], (1350, 370))
                window.blit(param_dict["update_rate_price"], (1400, 390))
            if tower_A.damage_state:
                pygame.draw.rect(window, BLUE, (1180, 455, 160, 145), 0)
                window.blit(param_dict["update_damage_text"], (1190, 500))
                window.blit(param_dict["update_damage_price"], (1240, 520))
            if tower_A.poison_state:
                pygame.draw.rect(window, BLUE, (1340, 455, 160, 145), 0)
                window.blit(param_dict["poison_text"], (1370, 500))
                window.blit(param_dict["poison_price"], (1395, 520))
        elif (param_dict["contact_bomb_list"].has(tower_A) or
              param_dict["range_bomb_list"].has(tower_A)):
            pygame.draw.rect(window, GRAY, (1180, 310, 160, 145), 0)
            pygame.draw.rect(window, GRAY, (1340, 310, 160, 145), 0)
            pygame.draw.rect(window, GRAY, (1180, 455, 160, 145), 0)
            pygame.draw.rect(window, GRAY, (1340, 455, 160, 145), 0)
            window.blit(param_dict["update_range_text"], (1185, 370))
            window.blit(param_dict["update_range_price"], (1240, 390))
            window.blit(param_dict["update_rate_text"], (1350, 370))
            window.blit(param_dict["update_rate_price"], (1400, 390))
            window.blit(param_dict["update_damage_text"], (1190, 500))
            window.blit(param_dict["update_damage_price"], (1240, 520))
            window.blit(param_dict["poison_text"], (1370, 500))
            window.blit(param_dict["poison_price"], (1395, 520))
        pygame.draw.line(window, BLACK, (1180, 310), (1500, 310), 3)
        pygame.draw.line(window, BLACK, (1180, 455), (1500, 455), 3)
        pygame.draw.line(window, BLACK, (1180, 600), (1500, 600), 3)
        pygame.draw.line(window, BLACK, (1340, 310), (1340, 600), 3)

        if update_enemies(param_dict, window, player) == "return_menu":
            return (None, None, None, None)

        if param_dict["tower_list"].has(tower_A):
            pygame.draw.circle(window, BLUE, (tower_A.rect.centerx, tower_A.rect.centery),
                               tower_A.range, 1)
        elif (param_dict["contact_bomb_list"].has(tower_A) or
              param_dict["range_bomb_list"].has(tower_A)):
            pygame.draw.circle(window, BLUE, (tower_A.rect.centerx, tower_A.rect.centery), 100, 1)
        if not tower_A.alive():
            return (None, round_stats, Delta, round_idx)
        param_dict["tower_list"].draw(window)
        param_dict["contact_bomb_list"].draw(window)
        param_dict["range_bomb_list"].draw(window)

        process_contact_bombs(param_dict, 0, 0, window, False)
        process_range_bombs(param_dict, 0, 0, window, False)
        process_towers(param_dict, 0, 0, window, False)

        if jump_rounds == 0 and field.map_number == 1:
            window.blit(start, (5, 315))
        elif jump_rounds == 0 and field.map_number == 2:
            window.blit(start, (5, 67))
        elif jump_rounds == 0 and field.map_number == 3:
            window.blit(start, (570, 670))
        elif jump_rounds == 0 and field.map_number == 4:
            window.blit(start, (620, 670))
        param_dict["bullet_list"].update()
        param_dict["enemy_list"].update()
        param_dict["missile_list"].update()
        param_dict["bullet_list"].draw(window)
        param_dict["enemy_list"].draw(window)
        param_dict["missile_list"].draw(window)
        del param_dict["value_list"][:]
        del param_dict["range_list"][:]
        param_dict["dictionary"].clear()
        pygame.display.update()
        clock.tick(60)

    return (tower_A, round_stats, Delta, round_idx)


def game_over(window):
    window.fill(WHITE)
    End_font = pygame.font.SysFont('Calibri', 120, True, False)
    Exit_font = pygame.font.SysFont('Calibri', 45, True, False)
    Info_font = pygame.font.SysFont('Calibri', 30, True, False)
    Exit = Exit_font.render("EXIT", True, BLACK)
    Menu = Exit_font.render("MENU", True, BLACK)
    End = End_font.render("GAME OVER", True, BLACK)
    Info = Info_font.render("If you want to return to menu, click MENU, "
                            "or if you want to quit the game, click EXIT.", True, BLACK)
    window.blit(End, (400, 250))
    window.blit(Exit, (500, 600))
    window.blit(Menu, (830, 600))
    window.blit(Info, (200, 420))
    pygame.draw.line(window, BLACK, (490, 590), (490, 650), 3)
    pygame.draw.line(window, BLACK, (490, 590), (590, 590), 3)
    pygame.draw.line(window, BLACK, (490, 650), (590, 650), 3)
    pygame.draw.line(window, BLACK, (590, 590), (590, 650), 3)
    pygame.draw.line(window, BLACK, (820, 590), (820, 650), 3)
    pygame.draw.line(window, BLACK, (820, 590), (960, 590), 3)
    pygame.draw.line(window, BLACK, (960, 590), (960, 650), 3)
    pygame.draw.line(window, BLACK, (820, 650), (960, 650), 3)
    clock = pygame.time.Clock()
    while True:
        pos = pygame.mouse.get_pos()
        xpos = pos[0]
        ypos = pos[1]
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # The user clicks on the "EXIT"-button
            elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 490 and xpos < 590 and
                  ypos > 590 and ypos < 650):
                pygame.quit()
                sys.exit()

            # The user clicks on the "MENU"-button
            elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 820 and xpos < 960 and
                  ypos > 590 and ypos < 650):
                return

        pygame.display.update()
        clock.tick(60)


def win(window):
    window.fill(WHITE)
    Win_font = pygame.font.SysFont('Calibri', 120, True, False)
    Exit_font = pygame.font.SysFont('Calibri', 45, True, False)
    Info_font = pygame.font.SysFont('Calibri', 30, True, False)
    Exit = Exit_font.render("EXIT", True, BLACK)
    Menu = Exit_font.render("MENU", True, BLACK)
    Win = Win_font.render("YOU WON!", True, BLACK)
    Info = Info_font.render("If you want to return to menu, click MENU, "
                            "or if you want to quit the game, click EXIT.", True, BLACK)
    window.blit(Win, (430, 250))
    window.blit(Exit, (500, 600))
    window.blit(Menu, (830, 600))
    window.blit(Info, (200, 420))
    pygame.draw.line(window, BLACK, (490, 590), (490, 650), 3)
    pygame.draw.line(window, BLACK, (490, 590), (590, 590), 3)
    pygame.draw.line(window, BLACK, (490, 650), (590, 650), 3)
    pygame.draw.line(window, BLACK, (590, 590), (590, 650), 3)
    pygame.draw.line(window, BLACK, (820, 590), (820, 650), 3)
    pygame.draw.line(window, BLACK, (820, 590), (960, 590), 3)
    pygame.draw.line(window, BLACK, (960, 590), (960, 650), 3)
    pygame.draw.line(window, BLACK, (820, 650), (960, 650), 3)
    clock = pygame.time.Clock()
    while True:
        pos = pygame.mouse.get_pos()
        xpos = pos[0]
        ypos = pos[1]
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # The user clicks on the "EXIT"-button
            elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 490 and xpos < 590 and
                  ypos > 590 and ypos < 650):
                pygame.quit()
                sys.exit()

            # The user clicks on the "MENU"-button
            elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 820 and xpos < 960 and
                  ypos > 590 and ypos < 650):
                return

        pygame.display.update()
        clock.tick(60)


def guide(window):
    window.fill(WHITE)
    Font = pygame.font.SysFont('Calibri', 22, True, False)
    Font_2 = pygame.font.SysFont('Calibri', 45, True, False)
    Menu = Font_2.render("MENU", True, BLACK)
    line_1 = Font.render("- Left side of the screen is the actual game field. "
                         "On the right side of the screen you can buy towers, upgrade them, etc.",
                         True, BLACK)
    line_2 = Font.render("- To start a new round, press the Start round -button at the "
                         "lower right corner of the screen.", True, BLACK)
    line_3 = Font.render("- To place a new tower to the field, choose a tower on the "
                         "top right corner of the screen, drag it somewhere on the field, "
                         "and drop it there. You can't", True, BLACK)
    line_4 = Font.render("  place a new tower on top of an existing tower or on the "
                         "road where enemies move.", True, BLACK)
    line_5 = Font.render("- You can't change the position of a tower once you have "
                         "placed it on the field.", True, BLACK)
    line_6 = Font.render("- To upgrade a tower, click on the tower you want to upgrade "
                         "and then click on the upgrade you want on the right side of the screen.",
                         True, BLACK)
    line_7 = Font.render("- To sell a tower, click on the tower you want to sell and then "
                         "press d. When you sell a tower you will get 70 % of the price of the "
                         "tower (including upgrades).", True, BLACK)
    line_8 = Font.render("- To pause or unpause the game, press ESC.", True, BLACK)
    line_9 = Font.render("- There are enemies of several colors in the game. Each color "
                         "(except black) corresponds to a color of some tower. This tells "
                         "that the enemy is immune to that", True, BLACK)
    line_10 = Font.render("  tower. This means that red enemy is immune to red tower and so on. "
                          "Black enemy isn't immune to any tower.", True, BLACK)
    line_11 = Font.render("- You can let 20 enemies reach the goal before you lose the game.",
                          True, BLACK)
    line_12 = Font.render("- There are five different types of towers, one bomb and one mine "
                          "in the game. Pistol, machine gun and shotgun are basic towers that "
                          "differ in damage and", True, BLACK)
    line_13 = Font.render("  fire rate. The assistant tower is a little different as its damage "
                          "is very low but it reduces the speed of a fast enemy and it removes "
                          "the immunity of an enemy.", True, BLACK)
    line_14 = Font.render("  The Homing missile -gun has a very large range and it always hits "
                          "the target. The smart bomb explodes when there are at least five "
                          "enemies within the range", True, BLACK)
    line_15 = Font.render("  of the bomb. It makes damage to these enemies. The mine is used "
                          "by setting it on the path of the enemies. When an enemy hits the mine, "
                          "the health of the", True, BLACK)
    line_16 = Font.render("  enemy is reduced and the mine is destroyed.", True, BLACK)
    # Set texts and lines on the screen.
    window.blit(Menu, (700, 600))
    pygame.draw.line(window, BLACK, (680, 580), (680, 660), 2)
    pygame.draw.line(window, BLACK, (680, 580), (835, 580), 2)
    pygame.draw.line(window, BLACK, (835, 580), (835, 660), 2)
    pygame.draw.line(window, BLACK, (680, 660), (835, 660), 2)
    window.blit(line_1, (10, 20))
    window.blit(line_2, (10, 55))
    window.blit(line_3, (10, 90))
    window.blit(line_4, (10, 125))
    window.blit(line_5, (10, 160))
    window.blit(line_6, (10, 195))
    window.blit(line_7, (10, 230))
    window.blit(line_8, (10, 265))
    window.blit(line_9, (10, 300))
    window.blit(line_10, (10, 335))
    window.blit(line_11, (10, 370))
    window.blit(line_12, (10, 405))
    window.blit(line_13, (10, 440))
    window.blit(line_14, (10, 475))
    window.blit(line_15, (10, 510))
    window.blit(line_16, (10, 545))
    clock = pygame.time.Clock()
    while True:
        pos = pygame.mouse.get_pos()
        xpos = pos[0]
        ypos = pos[1]

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # If the player clics on the "MENU"-button on the screen, return back to the menu.
            elif (event.type == pygame.MOUSEBUTTONDOWN and xpos > 680 and xpos < 835 and
                  ypos > 580 and ypos < 660):
                return

        pygame.display.update()
        clock.tick(60)
