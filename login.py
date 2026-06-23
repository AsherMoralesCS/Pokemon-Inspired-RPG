import hashlib
import json
import os

import pygame

from config import PLAYER_DB_PATH, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, GRAY
from ui import Button, DisclaimerScreen, get_font, TextInput


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class PlayerDataManager:
    def __init__(self):
        self.db_path = PLAYER_DB_PATH
        self.accounts = {}
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as file:
                self.accounts = json.load(file)
        else:
            self.accounts = {}

    def save(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as file:
            json.dump(self.accounts, file, indent=2)

    def account_exists(self, username):
        return username in self.accounts

    def register_account(self, username, password):
        if not username or not password:
            return False, "Username and password required."
        if username in self.accounts:
            return False, "Account already exists."
        self.accounts[username] = {
            "password_hash": hash_password(password),
            "party": [],
            "game_completed": False,
            "position": {"x": 15, "y": 11},
            "battle_npc_defeated": False,
            "guide_tutorial_completed": False,
        }
        self.save()
        return True, "Account created!"

    def attempt_login(self, username, password):
        if username not in self.accounts:
            return False, None, "Account not found."
        stored_hash = self.accounts[username]["password_hash"]
        if stored_hash != hash_password(password):
            return False, None, "Incorrect password."
        return True, self.accounts[username], "Login successful!"

    def update_account(self, username, data):
        if username in self.accounts:
            self.accounts[username].update(data)
            self.save()

    def get_account(self, username):
        return self.accounts.get(username)


class LoginScreen:
    def __init__(self, screen):
        self.screen = screen
        self.db = PlayerDataManager()
        self.username_input = TextInput(
            SCREEN_WIDTH // 2 - 150, 200, 300, 36, "Username"
        )
        self.password_input = TextInput(
            SCREEN_WIDTH // 2 - 150, 280, 300, 36, "Password", password=True
        )
        self.login_button = Button(SCREEN_WIDTH // 2 - 160, 360, 140, 40, "Login")
        self.register_button = Button(SCREEN_WIDTH // 2 + 20, 360, 140, 40, "Register")
        self.disclaimer_button = Button(
            SCREEN_WIDTH // 2 - 120, 420, 240, 36, "Credits / Disclaimer"
        )
        self.disclaimer_screen = DisclaimerScreen()
        self.message = ""
        self.logged_in = False
        self.username = ""
        self.player_data = None
        self.title_font = get_font(36)
        self.msg_font = get_font(16)

    def attempt_login(self):
        username = self.username_input.text.strip()
        password = self.password_input.text
        success, data, msg = self.db.attempt_login(username, password)
        self.message = msg
        if success:
            self.logged_in = True
            self.username = username
            self.player_data = data
        return success

    def register_account(self):
        username = self.username_input.text.strip()
        password = self.password_input.text
        success, msg = self.db.register_account(username, password)
        self.message = msg
        if success:
            self.attempt_login()
        return success

    def handle_event(self, event):
        if self.disclaimer_screen.is_visible():
            self.disclaimer_screen.handle_event(event)
            return

        if self.disclaimer_button.handle_event(event):
            self.disclaimer_screen.show()
            return
        if self.username_input.handle_event(event) == "submit":
            self.attempt_login()
            return
        if self.password_input.handle_event(event) == "submit":
            self.attempt_login()
            return
        if self.login_button.handle_event(event):
            self.attempt_login()
        if self.register_button.handle_event(event):
            self.register_account()

    def update(self):
        pass

    def draw(self):
        self.screen.fill((20, 30, 50))
        title = self.title_font.render("Starfall Island RPG", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))
        subtitle = self.msg_font.render("Login or Register to begin your adventure", True, GRAY)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 120))
        self.username_input.draw(self.screen)
        self.password_input.draw(self.screen)
        self.login_button.draw(self.screen)
        self.register_button.draw(self.screen)
        self.disclaimer_button.draw(self.screen)
        if self.message:
            msg_surf = self.msg_font.render(self.message, True, WHITE)
            self.screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, 480))
        self.disclaimer_screen.draw(self.screen)

    def get_db(self):
        return self.db
