import sys

import pygame

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from game import Game
from login import LoginScreen


class GameApplication:
    SCENE_LOGIN = "login"
    SCENE_GAME = "game"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Starfall Island RPG")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_scene = self.SCENE_LOGIN
        self.login_screen = LoginScreen(self.screen)
        self.game = None

    def switch_to_game(self):
        self.game = Game(
            self.screen,
            self.login_screen.username,
            self.login_screen.player_data,
            self.login_screen.get_db(),
        )
        self.current_scene = self.SCENE_GAME

    def switch_to_login(self):
        self.game = None
        self.login_screen = LoginScreen(self.screen)
        self.current_scene = self.SCENE_LOGIN

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.game:
                    self.game.save_player_data()
                self.running = False
                return

            if self.current_scene == self.SCENE_LOGIN:
                self.login_screen.handle_event(event)
                if self.login_screen.logged_in:
                    self.switch_to_game()
            elif self.current_scene == self.SCENE_GAME and self.game:
                self.game.handle_event(event)
                if self.game.should_return_to_login():
                    self.switch_to_login()

    def update(self):
        if self.current_scene == self.SCENE_LOGIN:
            self.login_screen.update()
        elif self.current_scene == self.SCENE_GAME and self.game:
            self.game.update()

    def draw(self):
        if self.current_scene == self.SCENE_LOGIN:
            self.login_screen.draw()
        elif self.current_scene == self.SCENE_GAME and self.game:
            self.game.draw()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


def main():
    app = GameApplication()
    app.run()


if __name__ == "__main__":
    main()
