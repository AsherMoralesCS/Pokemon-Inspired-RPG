import pygame

from config import (
    BLACK,
    DIALOGUE_BG,
    DIALOGUE_BORDER,
    FIRE_COLOR,
    GRASS_COLOR,
    GRAY,
    HP_GREEN,
    HP_RED,
    HP_YELLOW,
    MENU_HIGHLIGHT,
    MENU_NORMAL,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TYPE_COLORS,
    WATER_COLOR,
    WHITE,
    XP_BLUE,
    FONT_PATH,
)


_font_cache = {}


def get_font(size):
    if size not in _font_cache:
        try:
            _font_cache[size] = pygame.font.Font(FONT_PATH, size)
        except (FileNotFoundError, pygame.error):
            _font_cache[size] = pygame.font.SysFont("consolas", size)
    return _font_cache[size]


class DialogueBox:
    def __init__(self):
        self.visible = False
        self.speaker = ""
        self.lines = []
        self.current_line = 0
        self.font = get_font(18)
        self.name_font = get_font(16)
        self.box_rect = pygame.Rect(20, SCREEN_HEIGHT - 140, SCREEN_WIDTH - 40, 120)

    def show(self, speaker, text_lines):
        self.visible = True
        self.speaker = speaker
        if isinstance(text_lines, str):
            self.lines = [text_lines]
        else:
            self.lines = list(text_lines)
        self.current_line = 0

    def hide(self):
        self.visible = False
        self.lines = []
        self.current_line = 0

    def advance(self):
        if self.current_line < len(self.lines) - 1:
            self.current_line += 1
            return False
        self.hide()
        return True

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                self.advance()
                return True
        return True

    def draw(self, surface):
        if not self.visible:
            return
        pygame.draw.rect(surface, DIALOGUE_BG, self.box_rect)
        pygame.draw.rect(surface, DIALOGUE_BORDER, self.box_rect, 3)
        name_rect = pygame.Rect(self.box_rect.x + 10, self.box_rect.y + 8, 200, 24)
        pygame.draw.rect(surface, DIALOGUE_BORDER, name_rect, 1)
        name_surf = self.name_font.render(self.speaker, True, WHITE)
        surface.blit(name_surf, (name_rect.x + 8, name_rect.y + 4))
        y = self.box_rect.y + 40
        for index in range(self.current_line, min(self.current_line + 3, len(self.lines))):
            text_surf = self.font.render(self.lines[index], True, WHITE)
            surface.blit(text_surf, (self.box_rect.x + 16, y))
            y += 24
        hint = self.font.render("Press SPACE/ENTER", True, GRAY)
        surface.blit(hint, (self.box_rect.right - 180, self.box_rect.bottom - 24))


class HPBar:
    def __init__(self, x, y, width, height, show_label=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.show_label = show_label
        self.current_hp = 100
        self.max_hp = 100
        self.display_ratio = 1.0
        self.target_ratio = 1.0
        self.font = get_font(14)

    def set_hp(self, current, maximum):
        self.current_hp = current
        self.max_hp = max(1, maximum)
        self.target_ratio = self.current_hp / self.max_hp

    def update(self):
        if self.display_ratio > self.target_ratio:
            self.display_ratio = max(self.target_ratio, self.display_ratio - 0.02)
        elif self.display_ratio < self.target_ratio:
            self.display_ratio = min(self.target_ratio, self.display_ratio + 0.02)

    def get_color(self, ratio):
        if ratio > 0.5:
            return HP_GREEN
        if ratio > 0.25:
            return HP_YELLOW
        return HP_RED

    def draw(self, surface):
        pygame.draw.rect(surface, BLACK, self.rect)
        fill_width = int(self.rect.width * self.display_ratio)
        if fill_width > 0:
            color = self.get_color(self.display_ratio)
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, color, fill_rect)
        pygame.draw.rect(surface, WHITE, self.rect, 1)
        if self.show_label:
            label = str(self.current_hp) + "/" + str(self.max_hp)
            text = self.font.render(label, True, WHITE)
            surface.blit(text, (self.rect.x + 4, self.rect.y + 1))


class XPBar:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.ratio = 0.0
        self.display_ratio = 0.0
        self.font = get_font(12)

    def set_progress(self, current, needed):
        if needed <= 0:
            self.ratio = 1.0
        else:
            self.ratio = min(1.0, current / needed)

    def update(self):
        if self.display_ratio < self.ratio:
            self.display_ratio = min(self.ratio, self.display_ratio + 0.03)
        elif self.display_ratio > self.ratio:
            self.display_ratio = max(self.ratio, self.display_ratio - 0.03)

    def draw(self, surface):
        pygame.draw.rect(surface, BLACK, self.rect)
        fill_width = int(self.rect.width * self.display_ratio)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, XP_BLUE, fill_rect)
        pygame.draw.rect(surface, WHITE, self.rect, 1)


class MessageLog:
    def __init__(self, x, y, width):
        self.rect = pygame.Rect(x, y, width, 30)
        self.message = ""
        self.font = get_font(16)

    def set_message(self, text):
        self.message = text

    def draw(self, surface):
        pygame.draw.rect(surface, DIALOGUE_BG, self.rect)
        pygame.draw.rect(surface, DIALOGUE_BORDER, self.rect, 1)
        text = self.font.render(self.message, True, WHITE)
        surface.blit(text, (self.rect.x + 8, self.rect.y + 6))


class BattleMenu:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.move_ids = []
        self.selected = 0
        self.visible = False
        self.font = get_font(16)
        self.move_lookup = None

    def set_moves(self, move_ids, move_lookup):
        self.move_ids = move_ids
        self.move_lookup = move_lookup
        self.selected = 0
        self.visible = True

    def hide(self):
        self.visible = False

    def handle_event(self, event):
        if not self.visible:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 2) % len(self.move_ids)
                return "navigate"
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 2) % len(self.move_ids)
                return "navigate"
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(self.move_ids)
                return "navigate"
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(self.move_ids)
                return "navigate"
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                return self.move_ids[self.selected]
        return None

    def draw(self, surface):
        if not self.visible:
            return
        pygame.draw.rect(surface, DIALOGUE_BG, self.rect)
        pygame.draw.rect(surface, DIALOGUE_BORDER, self.rect, 2)
        cols = 2
        rows = max(1, (len(self.move_ids) + cols - 1) // cols)
        cell_w = self.rect.width // cols
        cell_h = self.rect.height // rows
        for index, move_id in enumerate(self.move_ids):
            col = index % cols
            row = index // cols
            cell_rect = pygame.Rect(
                self.rect.x + col * cell_w + 4,
                self.rect.y + row * cell_h + 4,
                cell_w - 8,
                cell_h - 8,
            )
            move = self.move_lookup.get_move(move_id)
            color = MENU_HIGHLIGHT if index == self.selected else MENU_NORMAL
            pygame.draw.rect(surface, color if index == self.selected else DIALOGUE_BG, cell_rect)
            pygame.draw.rect(surface, DIALOGUE_BORDER, cell_rect, 1)
            move_name = move["name"] if move else move_id
            type_color = TYPE_COLORS.get(move["type"], WHITE) if move else WHITE
            text = self.font.render(move_name, True, BLACK if index == self.selected else WHITE)
            surface.blit(text, (cell_rect.x + 8, cell_rect.y + 6))
            type_text = self.font.render(move["type"].upper(), True, type_color)
            surface.blit(type_text, (cell_rect.x + 8, cell_rect.y + 22))


class StarterSelectScreen:
    STARTERS = [
        ("water_stage1", "Aqualet", "Water", WATER_COLOR),
        ("grass_stage1", "Sproutling", "Grass", GRASS_COLOR),
        ("fire_stage1", "Emberpup", "Fire", FIRE_COLOR),
    ]

    def __init__(self):
        self.selected = 0
        self.done = False
        self.chosen_id = None
        self.font = get_font(24)
        self.small_font = get_font(18)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % 3
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % 3
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.chosen_id = self.STARTERS[self.selected][0]
                self.done = True
                return True
        return False

    def draw(self, surface):
        surface.fill((30, 40, 60))
        title = self.font.render("Choose Your Starter", True, WHITE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
        box_width = 220
        start_x = SCREEN_WIDTH // 2 - (box_width * 3 + 40) // 2
        for index, (species_id, name, ptype, color) in enumerate(self.STARTERS):
            x = start_x + index * (box_width + 20)
            y = 180
            rect = pygame.Rect(x, y, box_width, 280)
            highlight = index == self.selected
            pygame.draw.rect(surface, (50, 50, 70) if not highlight else color, rect)
            if highlight:
                pygame.draw.rect(surface, MENU_HIGHLIGHT, rect, 4)
            else:
                pygame.draw.rect(surface, GRAY, rect, 2)
            sprite_rect = pygame.Rect(x + 60, y + 30, 100, 100)
            pygame.draw.rect(surface, color, sprite_rect)
            name_surf = self.font.render(name, True, WHITE)
            surface.blit(name_surf, (x + box_width // 2 - name_surf.get_width() // 2, y + 150))
            type_surf = self.small_font.render(ptype + " Type", True, color)
            surface.blit(type_surf, (x + box_width // 2 - type_surf.get_width() // 2, y + 190))
        hint = self.small_font.render("Arrow keys to select, ENTER to confirm", True, GRAY)
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 60))


class TextInput:
    def __init__(self, x, y, width, height, label, password=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.text = ""
        self.active = False
        self.password = password
        self.font = get_font(20)
        self.label_font = get_font(16)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return "submit"
            elif event.unicode.isprintable() and len(self.text) < 20:
                self.text += event.unicode
        return None

    def draw(self, surface):
        label_surf = self.label_font.render(self.label, True, WHITE)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 22))
        color = MENU_HIGHLIGHT if self.active else WHITE
        pygame.draw.rect(surface, DIALOGUE_BG, self.rect)
        pygame.draw.rect(surface, color, self.rect, 2)
        display = "*" * len(self.text) if self.password else self.text
        text_surf = self.font.render(display, True, WHITE)
        surface.blit(text_surf, (self.rect.x + 8, self.rect.y + 8))


class Button:
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.font = get_font(18)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return True
        return False

    def draw(self, surface, highlighted=False):
        color = MENU_HIGHLIGHT if highlighted else DIALOGUE_BORDER
        pygame.draw.rect(surface, DIALOGUE_BG, self.rect)
        pygame.draw.rect(surface, color, self.rect, 2)
        text = self.font.render(self.label, True, WHITE)
        surface.blit(
            text,
            (
                self.rect.centerx - text.get_width() // 2,
                self.rect.centery - text.get_height() // 2,
            ),
        )


class PokemonStatusScreen:
    def __init__(self):
        self.visible = False
        self.pokemon = None
        self.title_font = get_font(28)
        self.label_font = get_font(18)
        self.value_font = get_font(16)
        self.move_lookup = None

    def show(self, pokemon, move_lookup):
        self.pokemon = pokemon
        self.move_lookup = move_lookup
        self.visible = True

    def hide(self):
        self.visible = False
        self.pokemon = None

    def is_visible(self):
        return self.visible

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN, pygame.K_SPACE):
                self.hide()
                return True
        return True

    def draw(self, surface):
        if not self.visible or self.pokemon is None:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(80, 40, SCREEN_WIDTH - 160, SCREEN_HEIGHT - 80)
        pygame.draw.rect(surface, DIALOGUE_BG, panel)
        pygame.draw.rect(surface, DIALOGUE_BORDER, panel, 3)

        pokemon = self.pokemon
        type_color = TYPE_COLORS.get(pokemon.get_pokemon_type(), WHITE)

        title = self.title_font.render("View Pokemon", True, WHITE)
        surface.blit(title, (panel.x + 20, panel.y + 16))

        y = panel.y + 60
        left_x = panel.x + 30
        right_x = panel.x + panel.width // 2 + 10

        name_line = pokemon.get_name() + "  Lv " + str(pokemon.level)
        surface.blit(self.label_font.render(name_line, True, MENU_HIGHLIGHT), (left_x, y))
        y += 32

        hp_text = "HP: " + str(pokemon.hp_current) + " / " + str(pokemon.max_hp)
        surface.blit(self.value_font.render(hp_text, True, WHITE), (left_x, y))
        y += 26

        type_text = "Type: " + pokemon.get_pokemon_type().capitalize()
        type_surf = self.value_font.render(type_text, True, type_color)
        surface.blit(type_surf, (left_x, y))
        y += 26

        exp_text = "EXP: " + str(pokemon.get_exp_in_level()) + " / " + str(pokemon.get_exp_to_next())
        surface.blit(self.value_font.render(exp_text, True, XP_BLUE), (left_x, y))
        y += 26

        total_exp = "Total EXP: " + str(pokemon.exp)
        surface.blit(self.value_font.render(total_exp, True, GRAY), (left_x, y))

        stat_y = panel.y + 60
        stats = [
            ("Attack", pokemon.get_attack()),
            ("Defense", pokemon.get_defense()),
            ("Speed", pokemon.get_speed()),
        ]
        for stat_name, stat_value in stats:
            line = stat_name + ": " + str(stat_value)
            surface.blit(self.value_font.render(line, True, WHITE), (right_x, stat_y))
            stat_y += 26

        moves_y = panel.y + 180
        surface.blit(self.label_font.render("Moves:", True, WHITE), (left_x, moves_y))
        moves_y += 28
        for move_id in pokemon.get_moves():
            move = self.move_lookup.get_move(move_id)
            move_name = move["name"] if move else move_id
            move_type = move["type"].capitalize() if move else ""
            move_color = TYPE_COLORS.get(move["type"], WHITE) if move else WHITE
            move_line = "- " + move_name + " (" + move_type + ")"
            surface.blit(self.value_font.render(move_line, True, move_color), (left_x + 10, moves_y))
            moves_y += 24

        hint = self.value_font.render("Press P, ESC, or ENTER to close", True, GRAY)
        surface.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 36))


DISCLAIMER_LINES = [
    "Credits / Disclaimer",
    "",
    "Code inspired by:",
    "https://www.youtube.com/watch?v=fo4e3njyGy0",
    "",
    "Pokemon and all related names, characters, creatures, artwork,",
    "and trademark features are property of The Pokemon Company,",
    "Nintendo, Game Freak, and Creatures Inc.",
    "",
    "This is a fan-made project created for educational and",
    "entertainment purposes only.",
    "",
    "All rights to Pokemon belong to their respective owners.",
]


class DisclaimerScreen:
    def __init__(self):
        self.visible = False
        self.scroll_offset = 0
        self.title_font = get_font(24)
        self.body_font = get_font(15)

    def show(self):
        self.visible = True
        self.scroll_offset = 0

    def hide(self):
        self.visible = False
        self.scroll_offset = 0

    def is_visible(self):
        return self.visible

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.hide()
                return True
            if event.key in (pygame.K_UP, pygame.K_w):
                self.scroll_offset = max(0, self.scroll_offset - 1)
                return True
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.scroll_offset += 1
                return True
        return True

    def draw(self, surface):
        if not self.visible:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(60, 40, SCREEN_WIDTH - 120, SCREEN_HEIGHT - 80)
        pygame.draw.rect(surface, DIALOGUE_BG, panel)
        pygame.draw.rect(surface, DIALOGUE_BORDER, panel, 3)

        y = panel.y + 20
        line_height = 22
        visible_lines = (panel.height - 60) // line_height
        max_scroll = max(0, len(DISCLAIMER_LINES) - visible_lines)
        if self.scroll_offset > max_scroll:
            self.scroll_offset = max_scroll

        for index in range(self.scroll_offset, min(len(DISCLAIMER_LINES), self.scroll_offset + visible_lines)):
            line = DISCLAIMER_LINES[index]
            if index == 0:
                text = self.title_font.render(line, True, MENU_HIGHLIGHT)
            else:
                text = self.body_font.render(line, True, WHITE)
            surface.blit(text, (panel.x + 24, y))
            y += line_height

        hint = self.body_font.render("Press ESC or ENTER to close | Up/Down to scroll", True, GRAY)
        surface.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 30))
