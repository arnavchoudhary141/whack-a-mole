import pygame
import random
import math
from .hole import Hole

# Game Engine

DARK_BROWN = (60, 40, 20)
MOLE_BROWN = (140, 95, 55)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class GameEngine:
    def __init__(self, width, height, rows=3, cols=3):
        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols

        self.holes = []

        spacing_x = width // (cols + 1)
        spacing_y = (height - 80) // (rows + 1)

        for r in range(rows):
            for c in range(cols):
                cx = spacing_x * (c + 1)
                cy = 80 + spacing_y * (r + 1)
                self.holes.append(Hole(cx, cy))

        self.font = pygame.font.SysFont("Arial", 28)
        self.game_over_font = pygame.font.SysFont("Arial", 48)
        self.menu_font = pygame.font.SysFont("Arial", 32)
        self.small_font = pygame.font.SysFont("Arial", 24)

        self.difficulties = {
            "Easy": {
                "spawn_chance": 0.015,
                "mole_up_frames": 60
            },
            "Medium": {
                "spawn_chance": 0.025,
                "mole_up_frames": 45
            },
            "Hard": {
                "spawn_chance": 0.04,
                "mole_up_frames": 30
            }
        }

        self.difficulty = "Medium"

        self.game_over = False
        self.show_difficulty_menu = False

        self.whack_sound = self._create_sound(700, 0.12)
        self.miss_sound = self._create_sound(180, 0.10)
        self.game_over_sound = self._create_sound(100, 0.35)

        self._start_round()

    def _create_sound(self, frequency, duration):
        try:
            sample_rate = 44100
            samples = int(sample_rate * duration)

            buffer = bytearray()

            for i in range(samples):
                value = int(
                    127
                    * math.sin(
                        2 * math.pi * frequency * i / sample_rate
                    )
                )

                value = max(-128, min(127, value))
                buffer.append(value + 128)

            return pygame.mixer.Sound(buffer=bytes(buffer))

        except Exception:
            return None

    def _play_sound(self, sound):
        try:
            if sound is not None:
                sound.play()
        except Exception:
            pass

    def _start_round(self):
        settings = self.difficulties[self.difficulty]

        self.spawn_chance = settings["spawn_chance"]
        self.mole_up_frames = settings["mole_up_frames"]

        self.round_seconds = 30
        self.time_left_frames = self.round_seconds * 60

        self.score = 0
        self.misses = 0

        self.game_over = False
        self.show_difficulty_menu = False

        for hole in self.holes:
            hole.active = False
            hole.timer = 0

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if self.show_difficulty_menu:
            self._handle_difficulty_event(event)
            return

        if self.game_over:
            self._handle_game_over_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos)

    def _handle_game_over_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.show_difficulty_menu = True

            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                raise SystemExit

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.show_difficulty_menu = True

    def _handle_difficulty_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.difficulty = "Easy"
                self._start_round()

            elif event.key == pygame.K_2:
                self.difficulty = "Medium"
                self._start_round()

            elif event.key == pygame.K_3:
                self.difficulty = "Hard"
                self._start_round()

            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                raise SystemExit

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if self.width // 2 - 150 <= x <= self.width // 2 + 150:
                if 250 <= y <= 300:
                    self.difficulty = "Easy"
                    self._start_round()

                elif 320 <= y <= 370:
                    self.difficulty = "Medium"
                    self._start_round()

                elif 390 <= y <= 440:
                    self.difficulty = "Hard"
                    self._start_round()

    def _handle_click(self, pos):
        hit_something = False

        candidates = [
            hole for hole in self.holes
            if hole.rect().collidepoint(pos)
        ]

        if candidates:
            clicked_hole = min(
                candidates,
                key=lambda hole: (
                    (hole.center_x - pos[0]) ** 2
                    + (hole.center_y - pos[1]) ** 2
                )
            )

            if clicked_hole.whack():
                self.score += 1
                hit_something = True

                self._play_sound(self.whack_sound)

        if not hit_something:
            self.misses += 1
            self._play_sound(self.miss_sound)

    def handle_input(self):
        pass

    def update(self):
        if self.game_over or self.show_difficulty_menu:
            return

        self.time_left_frames -= 1

        if self.time_left_frames <= 0:
            self.time_left_frames = 0
            self.game_over = True

            self._play_sound(self.game_over_sound)

            return

        for hole in self.holes:
            hole.update()

            if not hole.active and random.random() < self.spawn_chance:
                hole.pop_up(self.mole_up_frames)

    def render(self, screen):
        screen.fill((220, 220, 220))

        for hole in self.holes:
            pygame.draw.circle(
                screen,
                DARK_BROWN,
                (hole.center_x, hole.center_y),
                40
            )

            if hole.active:
                pygame.draw.circle(
                    screen,
                    MOLE_BROWN,
                    (hole.center_x, hole.center_y),
                    32
                )

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            BLACK
        )
        screen.blit(score_text, (10, 10))

        seconds_left = max(0, self.time_left_frames // 60)

        timer_text = self.font.render(
            f"Time: {seconds_left}s",
            True,
            BLACK
        )

        screen.blit(
            timer_text,
            (self.width - 140, 10)
        )

        difficulty_text = self.small_font.render(
            f"Difficulty: {self.difficulty}",
            True,
            BLACK
        )

        screen.blit(
            difficulty_text,
            (10, 45)
        )

        if self.game_over and not self.show_difficulty_menu:
            overlay = pygame.Surface(
                (self.width, self.height),
                pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))

            title = self.game_over_font.render(
                "GAME OVER",
                True,
                WHITE
            )

            score = self.menu_font.render(
                f"Final Score: {self.score}",
                True,
                WHITE
            )

            replay = self.small_font.render(
                "Press R or click to replay",
                True,
                WHITE
            )

            exit_text = self.small_font.render(
                "Press ESC to exit",
                True,
                WHITE
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(self.width // 2, 170)
                )
            )

            screen.blit(
                score,
                score.get_rect(
                    center=(self.width // 2, 230)
                )
            )

            screen.blit(
                replay,
                replay.get_rect(
                    center=(self.width // 2, 300)
                )
            )

            screen.blit(
                exit_text,
                exit_text.get_rect(
                    center=(self.width // 2, 350)
                )
            )

        if self.show_difficulty_menu:
            screen.fill((35, 35, 35))

            title = self.game_over_font.render(
                "CHOOSE DIFFICULTY",
                True,
                WHITE
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(self.width // 2, 130)
                )
            )

            easy = self.menu_font.render(
                "1 - EASY",
                True,
                WHITE
            )

            medium = self.menu_font.render(
                "2 - MEDIUM",
                True,
                WHITE
            )

            hard = self.menu_font.render(
                "3 - HARD",
                True,
                WHITE
            )

            exit_text = self.small_font.render(
                "ESC - EXIT",
                True,
                WHITE
            )

            screen.blit(
                easy,
                easy.get_rect(
                    center=(self.width // 2, 270)
                )
            )

            screen.blit(
                medium,
                medium.get_rect(
                    center=(self.width // 2, 340)
                )
            )

            screen.blit(
                hard,
                hard.get_rect(
                    center=(self.width // 2, 410)
                )
            )

            screen.blit(
                exit_text,
                exit_text.get_rect(
                    center=(self.width // 2, 480)
                )
            )