
from pathlib import Path

from character import Attribute

from ..renderer import GOOD, GOLD, MUTED, TEXT_SOFT, WARN


class CharacterCreationScreen:
    """Modern fantasy RPG character creation screen."""

    ATTRIBUTES = (
        (Attribute.STRENGTH, "Güç", "Yakın dövüş ve taşıma"),
        (Attribute.DEXTERITY, "Çeviklik", "Hız ve isabet"),
        (Attribute.CONSTITUTION, "Dayanıklılık", "Can ve direnç"),
        (Attribute.INTELLIGENCE, "Zeka", "Bilgi ve büyü"),
        (Attribute.WISDOM, "Bilgelik", "Algı ve irade"),
        (Attribute.CHARISMA, "Karizma", "İkna ve ilişkiler"),
    )

    BASE_SCORE = 10
    POINTS = 12
    MIN_SCORE = 8
    MAX_SCORE = 15

    APPEARANCE_OPTIONS = {
        "Ten": (
            ("açık", (224, 172, 132)),
            ("buğday", (184, 125, 86)),
            ("esmer", (112, 70, 50)),
        ),
        "Saç": (
            ("siyah", (35, 29, 30)),
            ("kahverengi", (91, 54, 35)),
            ("sarı", (211, 170, 72)),
        ),
        "Göz": (
            ("mavi", (80, 160, 205)),
            ("yeşil", (90, 170, 110)),
            ("kahverengi", (105, 65, 45)),
        ),
        "Yüz": (
            ("sakin", (0, 0, 0)),
            ("kararlı", (0, 0, 0)),
            ("neşeli", (0, 0, 0)),
        ),
    }

    COLORS = {
        "background": (13, 22, 37),
        "panel": (19, 31, 49),
        "panel_light": (29, 44, 65),
        "card": (27, 41, 61),
        "card_selected": (70, 55, 32),
        "border": (65, 91, 126),
        "gold": (238, 180, 68),
        "gold_light": (255, 218, 139),
        "white": (237, 235, 226),
        "muted": (155, 174, 201),
        "blue": (104, 148, 204),
    }

    def __init__(self, service):
        self.service = service

        self.focus = 0
        self.selected_attribute = 0
        self.selected_appearance = 0

        self.name = ""
        self.age = ""

        self.message = (
            "Eren seni dikkatle inceliyor. Önce kendini tanıt."
        )

        self.scores = {
            attribute: self.BASE_SCORE
            for attribute, _label, _help in self.ATTRIBUTES
        }

        self.appearance = {
            key: options[0][0]
            for key, options in self.APPEARANCE_OPTIONS.items()
        }

        self.name_entry_active = True

        self._background = None
        self._assets = {}
        self._hit_rects = {}

        races, classes = self._factory_options()
        character = self._character()

        self.races = races
        self.classes = classes

        self.race_index = next(
            (
                index
                for index, item in enumerate(races)
                if character is not None
                and item.race_id == character.race.race_id
            ),
            0,
        )

        self.class_index = next(
            (
                index
                for index, item in enumerate(classes)
                if character is not None
                and item.class_id
                == character.character_class.class_id
            ),
            0,
        )

        if character is not None:
            self.appearance.update(
                getattr(character, "appearance", {})
            )

    # ---------------------------------------------------------
    # CHARACTER DATA
    # ---------------------------------------------------------

    def _character(self):
        return (
            self.service.application
            .holder.current.characters.get("hero")
        )

    def _factory_options(self):
        factory = self.service._character_factory

        if factory is None:
            return (), ()

        return (
            tuple(factory.races.values()),
            tuple(factory.classes.values()),
        )

    def _remaining_points(self):
        return self.POINTS - sum(
            score - self.BASE_SCORE
            for score in self.scores.values()
        )

    def _reset(self):
        self.__init__(self.service)

    # ---------------------------------------------------------
    # INPUT
    # ---------------------------------------------------------

    def handle(self, state):
        if state.mouse_clicked and state.mouse_pos is not None:
            result = self._handle_mouse(state.mouse_pos)
            if result is not None:
                return result
        self.name_entry_active = self.focus < 2

        if self.focus == 0:
            if state.pressed("backspace"):
                self.name = self.name[:-1]

            if state.text:
                self.name = (
                    self.name + state.text
                )[:24]

        elif self.focus == 1:
            if state.pressed("backspace"):
                self.age = self.age[:-1]

            if state.text:
                self.age = "".join(
                    char
                    for char in self.age + state.text
                    if char.isdigit()
                )[:3]

        if state.pressed("back"):
            if getattr(
                self.service,
                "_creation_from_eren",
                False,
            ):
                self.message = (
                    "Eren'e cevap vermeden önce "
                    "karakterini oluşturmalısın."
                )
                return None

            return "world"

        # ATTRIBUTE SELECTION
        if self.focus == 4:
            if state.pressed("up"):
                self.selected_attribute = (
                    self.selected_attribute - 1
                ) % len(self.ATTRIBUTES)

            if state.pressed("down"):
                self.selected_attribute = (
                    self.selected_attribute + 1
                ) % len(self.ATTRIBUTES)

            attribute = self.ATTRIBUTES[
                self.selected_attribute
            ][0]

            if (
                state.pressed("left")
                and self.scores[attribute] > self.MIN_SCORE
            ):
                self.scores[attribute] -= 1

            if (
                state.pressed("right")
                and self.scores[attribute] < self.MAX_SCORE
                and self._remaining_points() > 0
            ):
                self.scores[attribute] += 1

            if state.pressed("confirm"):
                return self._finish()

            return None

        # APPEARANCE SELECTION
        if self.focus == 5:
            keys = tuple(self.APPEARANCE_OPTIONS)

            if state.pressed("up") or state.pressed("down"):
                step = (
                    -1 if state.pressed("up") else 1
                )

                self.selected_appearance = (
                    self.selected_appearance + step
                ) % len(keys)

            if state.pressed("left") or state.pressed("right"):
                key = keys[self.selected_appearance]
                options = self.APPEARANCE_OPTIONS[key]

                current = next(
                    (
                        index
                        for index, item in enumerate(options)
                        if item[0] == self.appearance[key]
                    ),
                    0,
                )

                step = (
                    -1 if state.pressed("left") else 1
                )

                self.appearance[key] = options[
                    (current + step) % len(options)
                ][0]

            if state.pressed("confirm"):
                return self._finish()

            return None

        # RACE SELECTION
        if self.focus == 2 and self.races:
            if state.pressed("left") or state.pressed("up"):
                self.race_index = (
                    self.race_index - 1
                ) % len(self.races)

            if state.pressed("right") or state.pressed("down"):
                self.race_index = (
                    self.race_index + 1
                ) % len(self.races)

        # CLASS SELECTION
        elif self.focus == 3 and self.classes:
            if state.pressed("left") or state.pressed("up"):
                self.class_index = (
                    self.class_index - 1
                ) % len(self.classes)

            if state.pressed("right") or state.pressed("down"):
                self.class_index = (
                    self.class_index + 1
                ) % len(self.classes)

        # GENERAL NAVIGATION
        if state.pressed("up") and self.focus not in (2, 3):
            self.focus = (self.focus - 1) % 6

        if state.pressed("down") and self.focus not in (2, 3):
            self.focus = (self.focus + 1) % 6

        if state.pressed("left") and self.focus not in (2, 3):
            self.focus = (self.focus - 1) % 6

        if state.pressed("right") and self.focus not in (2, 3):
            self.focus = (self.focus + 1) % 6

        if state.pressed("confirm"):
            if self.focus < 5:
                self.focus += 1
            else:
                return self._finish()

        return None

    def _handle_mouse(self, position):
        """Select and edit creation controls with a single left click."""
        for key, rect in self._hit_rects.get("fields", {}).items():
            if rect.collidepoint(position):
                self.focus = key
                self.name_entry_active = key < 2
                return None

        for key, rect in self._hit_rects.get("races", {}).items():
            if rect.collidepoint(position):
                self.race_index = key
                self.focus = 2
                return None

        for key, rect in self._hit_rects.get("classes", {}).items():
            if rect.collidepoint(position):
                self.class_index = key
                self.focus = 3
                return None

        for index, rect in self._hit_rects.get("attributes", {}).items():
            if rect.collidepoint(position):
                self.selected_attribute = index
                self.focus = 4
                attribute = self.ATTRIBUTES[index][0]
                if position[0] >= rect.centerx:
                    if self.scores[attribute] < self.MAX_SCORE and self._remaining_points() > 0:
                        self.scores[attribute] += 1
                elif self.scores[attribute] > self.MIN_SCORE:
                    self.scores[attribute] -= 1
                return None

        for index, rect in self._hit_rects.get("appearance", {}).items():
            if rect.collidepoint(position):
                self.selected_appearance = index
                self.focus = 5
                key = tuple(self.APPEARANCE_OPTIONS)[index]
                options = self.APPEARANCE_OPTIONS[key]
                current = next(
                    (i for i, option in enumerate(options)
                     if option[0] == self.appearance[key]),
                    0,
                )
                self.appearance[key] = options[(current + 1) % len(options)][0]
                return None

        if self._hit_rects.get("finish") is not None and self._hit_rects["finish"].collidepoint(position):
            return self._finish()
        if self._hit_rects.get("back") is not None and self._hit_rects["back"].collidepoint(position):
            return "world" if not getattr(self.service, "_creation_from_eren", False) else None
        return None

    # ---------------------------------------------------------
    # CHARACTER CREATION
    # ---------------------------------------------------------

    def _finish(self):
        character = self._character()

        if character is None:
            self.message = "Oyuncu karakteri bulunamadı."
            return None

        if not self.name.strip():
            self.message = "İsim alanı boş bırakılamaz."
            self.focus = 0
            return None

        try:
            age = int(self.age)
        except ValueError:
            self.message = "Yaşını sayı olarak gir."
            self.focus = 1
            return None

        if not 13 <= age <= 120:
            self.message = "Yaş 13 ile 120 arasında olmalı."
            self.focus = 1
            return None

        if self._remaining_points() != 0:
            self.message = (
                f"Dağıtılmamış "
                f"{self._remaining_points()} puanın var."
            )
            self.focus = 4
            return None

        try:
            self.service.application.customize_character(
                "hero",
                self.name,
                age,
                self.scores,
                race=(
                    self.races[self.race_index]
                    if self.races else None
                ),
                character_class=(
                    self.classes[self.class_index]
                    if self.classes else None
                ),
                appearance=self.appearance,
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as error:
            self.message = str(error)
            return None

        from_eren = getattr(
            self.service,
            "_creation_from_eren",
            False,
        )

        self.service._player_name_confirmed = True
        self.service._creation_from_eren = False

        self.message = (
            f"{self.name}, Eldoria'ya hoş geldin."
        )

        return "dialogue" if from_eren else "world"

    # ---------------------------------------------------------
    # ASSET LOADING
    # ---------------------------------------------------------

    def _asset_path(self, filename):
        return (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "character_creation"
            / filename
        )

    def _load_image(self, renderer, filename):
        if filename in self._assets:
            return self._assets[filename]

        image_module = getattr(renderer.pg, "image", None)

        path = self._asset_path(filename)

        if (
            image_module is None
            or not hasattr(image_module, "load")
            or not path.is_file()
        ):
            self._assets[filename] = None
            return None

        try:
            image = image_module.load(str(path))

            if hasattr(image, "convert_alpha"):
                image = image.convert_alpha()

            self._assets[filename] = image
            return image

        except (OSError, RuntimeError):
            self._assets[filename] = None
            return None

    def _load_background(self, renderer):
        if self._background is not None:
            return self._background

        self._background = self._load_image(
            renderer,
            "background.png",
        )

        if self._background is None:
            image_module = getattr(renderer.pg, "image", None)

            fallback = (
                Path(__file__).resolve().parents[1]
                / "assets"
                / "main_menu1.png"
            )

            if (
                image_module is not None
                and hasattr(image_module, "load")
                and fallback.is_file()
            ):
                try:
                    self._background = image_module.load(
                        str(fallback)
                    )
                except (OSError, RuntimeError):
                    self._background = None

        return self._background

    # ---------------------------------------------------------
    # DRAWING HELPERS
    # ---------------------------------------------------------

    def _panel(
        self,
        renderer,
        rect,
        fill=None,
        border=None,
        radius=12,
    ):
        colors = self.COLORS

        fill = fill or colors["panel"]
        border = border or colors["border"]

        draw = renderer.pg.draw

        shadow = renderer.pg.Rect(
            rect.x + 5,
            rect.y + 6,
            rect.width,
            rect.height,
        )

        draw.rect(
            renderer.surface,
            (7, 11, 19),
            shadow,
            border_radius=radius,
        )

        draw.rect(
            renderer.surface,
            fill,
            rect,
            border_radius=radius,
        )

        draw.rect(
            renderer.surface,
            border,
            rect,
            2,
            border_radius=radius,
        )

    def _line(self, renderer, x1, y, x2, color=None):
        renderer.pg.draw.line(
            renderer.surface,
            color or self.COLORS["gold"],
            (x1, y),
            (x2, y),
            1,
        )

    def _draw_card(
        self,
        renderer,
        rect,
        label,
        selected=False,
        subtitle=None,
    ):
        colors = self.COLORS

        fill = (
            colors["card_selected"]
            if selected
            else colors["card"]
        )

        border = (
            colors["gold"]
            if selected
            else colors["border"]
        )

        self._panel(
            renderer,
            rect,
            fill,
            border,
            radius=9,
        )

        if selected:
            renderer.pg.draw.rect(
                renderer.surface,
                colors["gold_light"],
                renderer.pg.Rect(
                    rect.x + 4,
                    rect.y + 4,
                    rect.width - 8,
                    rect.height - 8,
                ),
                1,
                border_radius=7,
            )

        text_color = (
            colors["gold_light"]
            if selected
            else colors["white"]
        )

        renderer.text(
            label,
            rect.x + 8,
            rect.y + (rect.height // 2) - 9,
            text_color,
            max_width=rect.width - 16,
        )

        if subtitle:
            renderer.text(
                subtitle,
                rect.x + 8,
                rect.bottom - 23,
                colors["muted"],
                max_width=rect.width - 16,
            )

    def _draw_button(
        self,
        renderer,
        rect,
        label,
        primary=False,
    ):
        colors = self.COLORS

        if primary:
            fill = (151, 105, 38)
            border = colors["gold"]
            text_color = (255, 235, 187)
        else:
            fill = colors["panel_light"]
            border = colors["blue"]
            text_color = colors["white"]

        self._panel(
            renderer,
            rect,
            fill,
            border,
            radius=12,
        )

        width = renderer.text_width(label)

        renderer.text(
            label,
            rect.centerx - width // 2,
            rect.y + rect.height // 2 - 10,
            text_color,
        )

    def _field(
        self,
        renderer,
        rect,
        label,
        value,
        active=False,
        hint="",
    ):
        colors = self.COLORS

        renderer.text(
            label,
            rect.x,
            rect.y - 23,
            colors["gold"] if active else colors["muted"],
        )

        self._panel(
            renderer,
            rect,
            (
                (46, 43, 34)
                if active
                else (17, 29, 46)
            ),
            (
                colors["gold"]
                if active
                else colors["border"]
            ),
            radius=8,
        )

        shown = value or hint

        renderer.text(
            shown,
            rect.x + 14,
            rect.y + rect.height // 2 - 9,
            (
                colors["white"]
                if value
                else colors["muted"]
            ),
            max_width=rect.width - 28,
        )

    # ---------------------------------------------------------
    # CHARACTER PREVIEW
    # ---------------------------------------------------------

    def _render_character_preview(self, renderer, area):
        colors = self.COLORS

        platform = self._load_image(
            renderer,
            "stone_platform.png",
        )

        hero = self._load_image(
            renderer,
            "hero.png",
        )

        if platform is not None:
            transform = getattr(renderer.pg, "transform", None)

            if transform is not None:
                platform = transform.smoothscale(
                    platform,
                    (area.width - 10, 100),
                )

            renderer.surface.blit(
                platform,
                (
                    area.centerx - platform.get_width() // 2,
                    area.bottom - 115,
                ),
            )

        else:
            renderer.pg.draw.ellipse(
                renderer.surface,
                (52, 60, 67),
                renderer.pg.Rect(
                    area.x + 25,
                    area.bottom - 110,
                    area.width - 50,
                    85,
                ),
            )

            renderer.pg.draw.ellipse(
                renderer.surface,
                colors["gold"],
                renderer.pg.Rect(
                    area.x + 25,
                    area.bottom - 110,
                    area.width - 50,
                    85,
                ),
                2,
            )

        if hero is not None:
            transform = getattr(renderer.pg, "transform", None)

            if transform is not None:
                max_height = area.height - 100
                ratio = min(
                    (area.width - 35) / hero.get_width(),
                    max_height / hero.get_height(),
                )

                size = (
                    max(1, int(hero.get_width() * ratio)),
                    max(1, int(hero.get_height() * ratio)),
                )

                hero = transform.smoothscale(hero, size)

            renderer.surface.blit(
                hero,
                (
                    area.centerx - hero.get_width() // 2,
                    area.bottom - 120 - hero.get_height(),
                ),
            )

        else:
            # Placeholder until the real low-poly hero asset is added.
            draw = renderer.pg.draw

            cx = area.centerx
            cy = area.y + 115

            skin = dict(
                self.APPEARANCE_OPTIONS["Ten"]
            )[self.appearance["Ten"]]

            hair = dict(
                self.APPEARANCE_OPTIONS["Saç"]
            )[self.appearance["Saç"]]

            eyes = dict(
                self.APPEARANCE_OPTIONS["Göz"]
            )[self.appearance["Göz"]]

            draw.ellipse(
                renderer.surface,
                (70, 45, 37),
                renderer.pg.Rect(
                    cx - 48, cy - 48, 96, 115
                ),
            )

            draw.circle(
                renderer.surface,
                skin,
                (cx, cy),
                42,
            )

            draw.polygon(
                renderer.surface,
                hair,
                [
                    (cx - 43, cy - 10),
                    (cx - 30, cy - 48),
                    (cx + 8, cy - 60),
                    (cx + 43, cy - 28),
                    (cx + 38, cy - 5),
                    (cx - 36, cy - 5),
                ],
            )

            draw.circle(
                renderer.surface,
                eyes,
                (cx - 14, cy + 5),
                4,
            )

            draw.circle(
                renderer.surface,
                eyes,
                (cx + 14, cy + 5),
                4,
            )

            draw.polygon(
                renderer.surface,
                (105, 61, 46),
                [
                    (cx - 60, cy + 50),
                    (cx + 60, cy + 50),
                    (cx + 105, area.bottom - 125),
                    (cx - 105, area.bottom - 125),
                ],
            )

            draw.polygon(
                renderer.surface,
                (125, 39, 44),
                [
                    (cx - 50, cy + 55),
                    (cx + 50, cy + 55),
                    (cx + 120, area.bottom - 115),
                    (cx - 120, area.bottom - 115),
                ],
            )

        renderer.text(
            "KAHRAMAN ÖNİZLEMESİ",
            area.centerx - 105,
            area.bottom - 25,
            colors["muted"],
        )

        # Appearance color indicators
        swatch_y = area.y + 12

        for index, key in enumerate(("Ten", "Saç", "Göz")):
            options = dict(self.APPEARANCE_OPTIONS[key])
            color = options[self.appearance[key]]

            x = area.x + 22 + index * 105

            renderer.pg.draw.circle(
                renderer.surface,
                color,
                (x + 8, swatch_y + 8),
                7,
            )

            renderer.text(
                key,
                x + 20,
                swatch_y,
                colors["muted"],
            )

    # ---------------------------------------------------------
    # RACE CARDS
    # ---------------------------------------------------------

    def _render_race_cards(
        self,
        renderer,
        x,
        y,
        width,
        height,
    ):
        count = len(self.races)

        if not count:
            renderer.text(
                "Irk seçeneği bulunamadı.",
                x,
                y,
                WARN,
            )
            return

        gap = 10
        card_width = (width - gap * (count - 1)) // count

        for index, race in enumerate(self.races):
            rect = renderer.pg.Rect(
                x + index * (card_width + gap),
                y,
                card_width,
                height,
            )

            self._draw_card(
                renderer,
                rect,
                race.name,
                selected=index == self.race_index,
            )

    # ---------------------------------------------------------
    # CLASS CARDS
    # ---------------------------------------------------------

    def _render_class_cards(
        self,
        renderer,
        x,
        y,
        width,
        height,
    ):
        count = len(self.classes)

        if not count:
            renderer.text(
                "Sınıf seçeneği bulunamadı.",
                x,
                y,
                WARN,
            )
            return

        gap = 10
        card_width = (width - gap * (count - 1)) // count

        for index, character_class in enumerate(self.classes):
            rect = renderer.pg.Rect(
                x + index * (card_width + gap),
                y,
                card_width,
                height,
            )

            self._draw_card(
                renderer,
                rect,
                character_class.name,
                selected=index == self.class_index,
            )

    # ---------------------------------------------------------
    # ATTRIBUTE CARDS
    # ---------------------------------------------------------

    def _render_attribute_cards(
        self,
        renderer,
        x,
        y,
        width,
    ):
        gap_x = 12
        gap_y = 5

        card_width = (width - gap_x * 2) // 3
        card_height = 34

        for index, (attribute, label, help_text) in enumerate(
            self.ATTRIBUTES
        ):
            row = index // 3
            column = index % 3

            rect = renderer.pg.Rect(
                x + column * (card_width + gap_x),
                y + row * (card_height + gap_y),
                card_width,
                card_height,
            )

            selected = (
                self.focus == 4
                and index == self.selected_attribute
            )

            self._panel(
                renderer,
                rect,
                (
                    self.COLORS["card_selected"]
                    if selected
                    else self.COLORS["card"]
                ),
                (
                    self.COLORS["gold"]
                    if selected
                    else self.COLORS["border"]
                ),
                radius=8,
            )

            renderer.text(
                label,
                rect.x + 10,
                rect.y + 7,
                (
                    self.COLORS["gold_light"]
                    if selected
                    else self.COLORS["white"]
                ),
            )

            score = self.scores[attribute]

            renderer.text(
                f"−     {score}     +",
                rect.x + 10,
                rect.y + 20,
                self.COLORS["blue"],
            )

    # ---------------------------------------------------------
    # APPEARANCE OPTIONS
    # ---------------------------------------------------------

    def _render_appearance(self, renderer, x, y, width):
        keys = tuple(self.APPEARANCE_OPTIONS)

        item_width = width // len(keys)

        for index, key in enumerate(keys):
            options = dict(self.APPEARANCE_OPTIONS[key])

            value = self.appearance[key]

            rect = renderer.pg.Rect(
                x + index * item_width,
                y,
                item_width - 8,
                30,
            )

            selected = (
                self.focus == 5
                and index == self.selected_appearance
            )

            self._panel(
                renderer,
                rect,
                (
                    self.COLORS["card_selected"]
                    if selected
                    else self.COLORS["card"]
                ),
                (
                    self.COLORS["gold"]
                    if selected
                    else self.COLORS["border"]
                ),
                radius=7,
            )

            if key in ("Ten", "Saç", "Göz"):
                color = options[value]

                renderer.pg.draw.circle(
                    renderer.surface,
                    color,
                    (rect.x + 15, rect.centery),
                    6,
                )

            renderer.text(
                f"{key}: {value}",
                rect.x + 26,
                rect.y + 10,
                self.COLORS["white"],
                max_width=rect.width - 30,
            )

    # ---------------------------------------------------------
    # MAIN RENDER
    # ---------------------------------------------------------

    def render(self, renderer):
        colors = self.COLORS

        # BACKGROUND
        background = self._load_background(renderer)

        if background is None:
            renderer.clear(colors["background"])
        else:
            surface = background

            if surface.get_size() != (
                renderer.width,
                renderer.height,
            ):
                transform = getattr(
                    renderer.pg,
                    "transform",
                    None,
                )

                if transform is not None:
                    surface = transform.smoothscale(
                        background,
                        (renderer.width, renderer.height),
                    )

            renderer.surface.blit(surface, (0, 0))

        margin = max(18, round(renderer.width * 0.025))
        gap = max(18, round(renderer.width * 0.02))
        title_rect = renderer.pg.Rect(
            (renderer.width - min(445, renderer.width - margin * 2)) // 2,
            18,
            min(445, renderer.width - margin * 2),
            58,
        )

        self._panel(
            renderer,
            title_rect,
            colors["panel"],
            colors["gold"],
            radius=20,
        )

        title = "Karakter Oluştur"

        renderer.text(
            title,
            title_rect.centerx
            - renderer.text_width(title, title=True) // 2,
            title_rect.y + 10,
            colors["gold_light"],
            title=True,
            max_width=title_rect.width - 24,
        )

        content_top = title_rect.bottom + 14
        content_bottom = renderer.height - 42
        content_height = max(260, content_bottom - content_top)
        portrait_width = min(340, max(220, round(renderer.width * 0.29)))
        portrait = renderer.pg.Rect(
            margin,
            content_top,
            portrait_width,
            content_height,
        )

        self._render_character_preview(
            renderer,
            portrait,
        )

        panel_x = portrait.right + gap
        panel = renderer.pg.Rect(
            panel_x,
            content_top,
            max(320, renderer.width - panel_x - margin),
            content_height,
        )

        self._panel(
            renderer,
            panel,
            colors["panel"],
            (85, 112, 151),
            radius=13,
        )

        # PANEL HEADER
        inner = max(16, round(panel.width * 0.045))
        content_x = panel.x + inner
        content_width = panel.width - inner * 2
        renderer.text(
            "Kendini Tanıt",
            content_x,
            panel.y + 16,
            colors["gold_light"],
            title=True,
            max_width=content_width,
        )
        renderer.text(
            "İsim, yaş, ırk, sınıf, nitelikler ve görünümünü seç.",
            content_x,
            panel.y + 54,
            colors["muted"],
            max_width=content_width,
        )
        self._line(renderer, content_x, panel.y + 79, panel.right - inner)

        row = panel.y + 92
        field_height = 36
        self._hit_rects = {"fields": {}, "races": {}, "classes": {}, "attributes": {}, "appearance": {}}

        # NAME
        name_rect = renderer.pg.Rect(content_x, row, content_width, field_height)
        self._field(
            renderer,
            name_rect,
            "İsim *",
            self.name,
            self.focus == 0,
            "Karakter ismini gir...",
        )
        self._hit_rects["fields"][0] = name_rect

        # AGE
        age_rect = renderer.pg.Rect(content_x, row + 54, min(220, content_width), field_height)
        self._field(
            renderer,
            age_rect,
            "Yaş *",
            self.age,
            self.focus == 1,
            "13 - 120",
        )
        self._hit_rects["fields"][1] = age_rect

        race_y = row + 100
        # RACE
        renderer.text(
            "IRK SEÇİMİ",
            content_x,
            race_y,
            colors["gold"],
        )

        self._render_race_cards(
            renderer,
            content_x,
            race_y + 20,
            content_width,
            34,
        )
        race_gap = 10
        race_width = (content_width - race_gap * max(0, len(self.races) - 1)) // max(1, len(self.races))
        for index in range(len(self.races)):
            self._hit_rects["races"][index] = renderer.pg.Rect(
                content_x + index * (race_width + race_gap), race_y + 20, race_width, 34
            )

        # CLASS
        class_y = race_y + 62
        renderer.text(
            "SINIF SEÇİMİ",
            content_x,
            class_y,
            colors["gold"],
        )

        self._render_class_cards(
            renderer,
            content_x,
            class_y + 20,
            content_width,
            34,
        )
        class_gap = 10
        class_width = (content_width - class_gap * max(0, len(self.classes) - 1)) // max(1, len(self.classes))
        for index in range(len(self.classes)):
            self._hit_rects["classes"][index] = renderer.pg.Rect(
                content_x + index * (class_width + class_gap), class_y + 20, class_width, 34
            )

        # ATTRIBUTES
        attribute_y = class_y + 62
        renderer.text(
            f"NİTELİKLER   Kalan puan: {self._remaining_points()}",
            content_x,
            attribute_y,
            colors["gold"],
            max_width=content_width,
        )

        self._render_attribute_cards(
            renderer,
            content_x,
            attribute_y + 20,
            content_width,
        )
        attribute_gap_x = 8
        attribute_gap_y = 4
        attribute_width = (content_width - attribute_gap_x * 2) // 3
        for index in range(len(self.ATTRIBUTES)):
            self._hit_rects["attributes"][index] = renderer.pg.Rect(
                content_x + (index % 3) * (attribute_width + attribute_gap_x),
                attribute_y + 20 + (index // 3) * (34 + attribute_gap_y),
                attribute_width,
                34,
            )

        # APPEARANCE
        appearance_y = attribute_y + 98
        renderer.text(
            "GÖRÜNÜM",
            content_x,
            appearance_y,
            colors["gold"],
        )

        self._render_appearance(
            renderer,
            content_x,
            appearance_y + 20,
            content_width,
        )
        appearance_width = content_width // len(self.APPEARANCE_OPTIONS)
        for index in range(len(self.APPEARANCE_OPTIONS)):
            self._hit_rects["appearance"][index] = renderer.pg.Rect(
                content_x + index * appearance_width,
                appearance_y + 20,
                appearance_width - 8,
                30,
            )

        # MESSAGE
        message_color = WARN if self.message.startswith(
            ("Yaş", "İsim", "Dağıt", "Oyuncu")
        ) else GOOD if self.message.endswith("hoş geldin.") else colors["muted"]
        renderer.text(
            self.message,
            portrait.x + 14,
            portrait.bottom - 52,
            message_color,
            max_width=portrait.width - 28,
        )

        self._hit_rects["finish"] = renderer.pg.Rect(
            panel.right - 120, panel.bottom - 38, 104, 30
        )
        self._hit_rects["back"] = renderer.pg.Rect(
            panel.x + 16, panel.bottom - 38, 104, 30
        )
        self._draw_button(renderer, self._hit_rects["back"], "Geri")
        self._draw_button(renderer, self._hit_rects["finish"], "Onayla", primary=True)

        renderer.footer(
            "İsim/Yaş yaz    ↑/↓ alan seç    ←/→ değiştir    "
            "Enter ilerle/onayla    Esc geri"
        )
