

import pygame
import sys
import math
from dataclasses import dataclass
from typing import Tuple


SMALL_SPRITE = 16         #sprite size 
SCALE = 8                 
WINDOW_W, WINDOW_H = 640, 480
FPS = 30


TICK_MS = 3000            # every 3 seconds a game tick happens
ANIM_MS = 200             # frame change for animation


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
UI_BG = (20, 20, 30)
BAR_BG = (50, 50, 60)
BAR_FILL = (120, 200, 120)
BAD_FILL = (220, 80, 80)
BUTTON_BG = (70, 70, 90)
BUTTON_HOVER = (100, 100, 140)
TEXT_COLOR = (230, 230, 240)

pygame.init()
FONT = pygame.font.SysFont("consolas", 16)


def clamp(v, a=0, b=100):
    return max(a, min(b, int(v)))


@dataclass
class Pet:
    name: str = "Zae"
    hunger: int = 20        # 0 full, 100 starving
    happiness: int = 80
    energy: int = 80
    health: int = 95
    clean: int = 80
    alive: bool = True
    age_ticks: int = 0      # number of ticks
    mood: str = "idle"      # idle/happy/sleep/sick

    def tick(self):
        if not self.alive:
            return
        self.age_ticks += 1
        # Natural decay
        self.hunger = clamp(self.hunger + 6)      # gets hungrier
        self.energy = clamp(self.energy - 5)      # uses energy
        self.clean = clamp(self.clean - 3)        # gets dirty
        # Happiness decreases with bad stats
        if self.hunger > 60:
            self.happiness = clamp(self.happiness - 4)
        else:
            self.happiness = clamp(self.happiness - 1)
        if self.clean < 40:
            self.happiness = clamp(self.happiness - 2)
        if self.energy < 30:
            self.happiness = clamp(self.happiness - 2)
        # Health affected
        if self.hunger > 85:
            self.health = clamp(self.health - 6)
        elif self.hunger > 60:
            self.health = clamp(self.health - 2)
        else:
            # small recovery if well-fed
            if self.health < 98:
                self.health = clamp(self.health + 1)
        if self.clean < 25:
            self.health = clamp(self.health - 3)
        if self.happiness < 20:
            self.health = clamp(self.health - 2)
        # Mood inference
        if self.health < 40:
            self.mood = "sick"
        elif self.energy < 25:
            self.mood = "sleep"
        elif self.happiness > 80:
            self.mood = "happy"
        else:
            self.mood = "idle"
        # Death check
        if self.health <= 0 or self.hunger >= 100:
            self.alive = False
            self.mood = "dead"

    # Player actions:
    def feed(self):
        if not self.alive:
            return
        self.hunger = clamp(self.hunger - 30)
        self.clean = clamp(self.clean - 5)
        self.happiness = clamp(self.happiness + 6)
        self.mood = "happy"

    def play(self):
        if not self.alive:
            return False
        if self.energy < 12:
            return False
        self.happiness = clamp(self.happiness + 18)
        self.energy = clamp(self.energy - 20)
        self.hunger = clamp(self.hunger + 8)
        self.mood = "happy"
        return True

    def sleep(self):
        if not self.alive:
            return
        self.energy = clamp(self.energy + 45)
        self.hunger = clamp(self.hunger + 18)
        self.mood = "sleep"

    def med(self):
        if not self.alive:
            return
        healed = 30
        self.health = clamp(self.health + healed)
        self.happiness = clamp(self.happiness - 8)
        self.mood = "idle"

    def clean_pet(self):
        if not self.alive:
            return
        self.clean = clamp(self.clean + 40)
        self.happiness = clamp(self.happiness + 6)
        self.energy = clamp(self.energy - 6)
        self.mood = "idle"


#Pixel sprite generator
def make_pet_frame(mood: str, frame_index: int) -> pygame.Surface:
    s = pygame.Surface((SMALL_SPRITE, SMALL_SPRITE))
    # We'll treat black as background; fill with black
    s.fill((0, 0, 0))
    # Colors
    body = (220, 180, 100)
    eye = (20, 20, 20)
    blush = (255, 120, 120)
    sleep_eye = (60, 60, 120)
    sick_color = (170, 200, 140)
    outline = (40, 30, 20)

    cx, cy = SMALL_SPRITE // 2, SMALL_SPRITE // 2

    for y in range(SMALL_SPRITE):
        for x in range(SMALL_SPRITE):
            dx = x - cx
            dy = y - cy + 1
            dist = math.hypot(dx, dy)
            if dist < 6.2:
                s.set_at((x, y), body)
            elif dist < 7.2:
                s.set_at((x, y), outline)

    if mood == "idle":
        s.set_at((cx - 2, cy - 1), eye)
        s.set_at((cx + 1, cy - 1), eye)
    elif mood == "happy":
        s.set_at((cx - 2, cy - 1), eye)
        s.set_at((cx - 2, cy), eye)
        s.set_at((cx + 1, cy - 1), eye)
        s.set_at((cx + 1, cy), eye)
        s.set_at((cx - 4, cy + 1), blush)
        s.set_at((cx + 3, cy + 1), blush)
    elif mood == "sleep":
        s.set_at((cx - 3, cy - 1), sleep_eye)
        s.set_at((cx + 2, cy - 1), sleep_eye)
    elif mood == "sick":
        for y in range(SMALL_SPRITE):
            for x in range(SMALL_SPRITE):
                if s.get_at((x, y))[:3] == body:
                    s.set_at((x, y), sick_color)

                    
        s.set_at((cx - 3, cy - 1), eye)
        s.set_at((cx - 2, cy), eye)
        s.set_at((cx + 2, cy), eye)
        s.set_at((cx + 3, cy - 1), eye)
    elif mood == "dead":
        for y in range(SMALL_SPRITE):
            for x in range(SMALL_SPRITE):
                if s.get_at((x, y))[:3] != (0, 0, 0):
                    s.set_at((x, y), (110, 110, 110))
        s.set_at((cx - 2, cy - 1), (30, 30, 30))
        s.set_at((cx + 1, cy - 1), (30, 30, 30))

    if frame_index % 2 == 0 and mood in ("idle", "happy"):
        if 0 <= cx < SMALL_SPRITE and 0 <= (cy - 3) < SMALL_SPRITE:
            s.set_at((cx, cy - 3), (255, 230, 200))

    return s


def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], size=16, color=TEXT_COLOR):
    font = pygame.font.SysFont("consolas", size)
    surf = font.render(text, True, color)
    surface.blit(surf, pos)


def draw_bar(surface: pygame.Surface, rect: pygame.Rect, value: int, max_val=100, fill_color=BAR_FILL):
    pygame.draw.rect(surface, BAR_BG, rect)
    w = int((value / max_val) * (rect.width - 4))
    if value < 35:
        fill = BAD_FILL
    else:
        fill = fill_color
    fill_rect = pygame.Rect(rect.left + 2, rect.top + 2, max(0, w), rect.height - 4)
    pygame.draw.rect(surface, fill, fill_rect)
    pygame.draw.rect(surface, (100, 100, 110), rect, 2)


class Button:
    def __init__(self, rect: pygame.Rect, label: str):
        self.rect = rect
        self.label = label

    def draw(self, surf: pygame.Surface, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        color = BUTTON_HOVER if hover else BUTTON_BG
        pygame.draw.rect(surf, color, self.rect, border_radius=6)
        draw_text(surf, self.label, (self.rect.x + 8, self.rect.y + 6), size=16)


def main():
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Simple Tamagotchi")
    clock = pygame.time.Clock()

    pet = Pet(name="Zae")

    last_tick_time = pygame.time.get_ticks()
    last_anim_time = pygame.time.get_ticks()
    anim_frame = 0

    btn_feed = Button(pygame.Rect(36, 380, 110, 40), "Feed (F)")
    btn_play = Button(pygame.Rect(162, 380, 110, 40), "Play (P)")
    btn_sleep = Button(pygame.Rect(288, 380, 110, 40), "Sleep (S)")
    btn_med = Button(pygame.Rect(414, 380, 110, 40), "Med (M)")
    btn_clean = Button(pygame.Rect(36, 430, 110, 40), "Clean (C)")

    buttons = [btn_feed, btn_play, btn_sleep, btn_med, btn_clean]

    running = True
    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_feed.rect.collidepoint(event.pos):
                    pet.feed()
                elif btn_play.rect.collidepoint(event.pos):
                    pet.play()
                elif btn_sleep.rect.collidepoint(event.pos):
                    pet.sleep()
                elif btn_med.rect.collidepoint(event.pos):
                    pet.med()
                elif btn_clean.rect.collidepoint(event.pos):
                    pet.clean_pet()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    pet.feed()
                elif event.key == pygame.K_p:
                    pet.play()
                elif event.key == pygame.K_s:
                    pet.sleep()
                elif event.key == pygame.K_m:
                    pet.med()
                elif event.key == pygame.K_c:
                    pet.clean_pet()

        now = pygame.time.get_ticks()
        if now - last_anim_time >= ANIM_MS:
            anim_frame = (anim_frame + 1) % 4
            last_anim_time = now

        if now - last_tick_time >= TICK_MS:
            pet.tick()
            last_tick_time = now

        screen.fill(UI_BG)
        pygame.draw.rect(screen, (30, 30, 40), pygame.Rect(16, 16, WINDOW_W - 32, 300), border_radius=8)

        pet_box = pygame.Rect(36, 36, SMALL_SPRITE * SCALE + 20, SMALL_SPRITE * SCALE + 20)
        pygame.draw.rect(screen, (18, 18, 28), pet_box, border_radius=6)

        mood = pet.mood
        if not pet.alive:
            mood = "dead"
        small_surf = make_pet_frame(mood, anim_frame)

        # Correct scaling call (two arguments only)
        scaled_surf = pygame.transform.scale(small_surf, (SMALL_SPRITE * SCALE, SMALL_SPRITE * SCALE))

        sx = pet_box.left + (pet_box.width - SMALL_SPRITE * SCALE) // 2
        sy = pet_box.top + (pet_box.height - SMALL_SPRITE * SCALE) // 2
        screen.blit(scaled_surf, (sx, sy))

        bar_x = 220
        bar_y = 48
        bar_w = 360
        bar_h = 28
        gap = 10

        draw_text(screen, f"Name: {pet.name}", (bar_x, bar_y - 22))
        draw_text(screen, f"Age ticks: {pet.age_ticks}", (bar_x + 220, bar_y - 22), size=14)

        draw_text(screen, "Hunger (0=full,100=starving)", (bar_x, bar_y))
        draw_bar(screen, pygame.Rect(bar_x, bar_y + 18, bar_w, bar_h), pet.hunger)

        draw_text(screen, "Happiness", (bar_x, bar_y + 18 + bar_h + gap))
        draw_bar(screen, pygame.Rect(bar_x, bar_y + 18 + bar_h + gap + 18, bar_w, bar_h), pet.happiness, fill_color=(180, 180, 250))

        draw_text(screen, "Energy", (bar_x, bar_y + 18 + (bar_h + gap) * 2))
        draw_bar(screen, pygame.Rect(bar_x, bar_y + 18 + (bar_h + gap) * 2 + 18, bar_w, bar_h), pet.energy, fill_color=(240, 200, 120))

        draw_text(screen, "Health", (bar_x, bar_y + 18 + (bar_h + gap) * 3))
        draw_bar(screen, pygame.Rect(bar_x, bar_y + 18 + (bar_h + gap) * 3 + 18, bar_w, bar_h), pet.health, fill_color=(150, 240, 170))

        draw_text(screen, "Cleanliness", (bar_x, bar_y + 18 + (bar_h + gap) * 4))
        draw_bar(screen, pygame.Rect(bar_x, bar_y + 18 + (bar_h + gap) * 4 + 18, bar_w, bar_h), pet.clean, fill_color=(200, 180, 240))

        draw_text(screen, "Controls: F=Feed P=Play S=Sleep M=Med C=Clean | Click buttons too", (24, 346), size=14)

        for b in buttons:
            b.draw(screen, mouse_pos)

        if not pet.alive:
            draw_text(screen, "Your pet has passed away. Close window to quit.", (36, 320), size=18, color=(220, 120, 120))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
