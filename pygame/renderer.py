"""Retained-style renderer plus the shared UI chrome used by every screen.

Besides the primitive drawing helpers, the renderer owns the parts of the
interface that stay constant while playing:

* a clickable navigation tab bar (``nav_current`` / ``nav_enabled``),
* a status strip with an HP bar, gold and location (``hud``),
* a resource bar showing the player's stockpile (``resource_bar``),
* hover highlighting (``mouse_pos``) and timed toast notices (``toast``).

``GameWindow`` feeds ``mouse_pos``, ``nav_current`` and ``nav_enabled`` in
before each frame; screens only call the drawing helpers.
"""

# --- palette ---------------------------------------------------------------
BACKGROUND = (18, 22, 32)
TEXT = (235, 238, 245)
TEXT_SOFT = (190, 202, 220)
MUTED = (155, 172, 196)
DISABLED = (110, 120, 135)
GOLD = (220, 190, 120)
GOOD = (140, 220, 160)
WARN = (230, 190, 110)
BAD = (230, 130, 120)

PANEL_FILL = (31, 39, 55)
PANEL_BORDER = (76, 92, 120)
STRIP_FILL = (25, 33, 47)
STRIP_BORDER = (62, 78, 101)
BUTTON_FILL = (38, 49, 69)
BUTTON_HOVER = (50, 66, 94)
BUTTON_SELECTED = (55, 75, 105)
BUTTON_BORDER = (110, 135, 170)
HIGHLIGHT = (245, 210, 120)

# --- resources ---------------------------------------------------------------
RESOURCE_NAMES = {
    "wood": "Odun",
    "plank": "Tahta",
    "stone": "Taş",
    "ore": "Cevher",
    "iron": "Demir",
    "gold": "Altın",
    "food": "Yiyecek",
    "bread": "Ekmek",
    "water": "Su",
}

RESOURCE_COLORS = {
    "wood": (150, 105, 60),
    "plank": (200, 160, 100),
    "stone": (140, 146, 158),
    "ore": (130, 105, 150),
    "iron": (165, 180, 200),
    "gold": (235, 195, 80),
    "food": (120, 180, 95),
    "bread": (205, 155, 90),
    "water": (90, 165, 220),
}
DEFAULT_RESOURCE_COLOR = (120, 140, 170)


UNIT_LABELS = {"item": "adet", "kg": "kg", "liter": "litre"}


def unit_label(unit):
    """Turkish label for a ResourceUnit / unit code ("item" -> "adet")."""
    code = getattr(unit, "value", str(unit))
    return UNIT_LABELS.get(code, code)


def resource_id(resource):
    """Return the plain string id of an enum-or-string resource."""
    return getattr(resource, "value", str(resource))


def resource_name(resource):
    rid = resource_id(resource)
    return RESOURCE_NAMES.get(rid, rid.replace("_", " ").capitalize())


def resource_color(resource):
    return RESOURCE_COLORS.get(resource_id(resource), DEFAULT_RESOURCE_COLOR)


ACTIVITY_LABELS = {
    "dialogue": "Diyalog",
    "market": "Pazar",
    "gather": "Toplama",
    "combat": "Savaş",
    "travel": "Seyahat",
}


# --- navigation ----------------------------------------------------------------
NAV_TABS = (
    ("world", "Yerel"),
    ("inventory", "Çanta"),
    ("production", "Üretim"),
    ("character", "Karakter"),
    ("quest_log", "Görevler"),
    ("market", "Pazar"),
    ("map", "Harita"),
)
# Screens that highlight another screen's tab.
NAV_ALIASES = {"local_map": "world"}


class Renderer:
    NAV_TOP = 18
    NAV_HEIGHT = 34
    NAV_TAB_WIDTH = 88
    NAV_GAP = 4
    RESOURCE_BAR_Y = 566

    def __init__(self, backend, surface, width: int, height: int) -> None:
        self.pg = backend
        self.surface = surface
        self.width = width
        self.height = height
        self.font = backend.font.Font(None, 24)
        self.title_font = backend.font.Font(None, 42)

        # Frame state, updated by GameWindow before every render.
        self.mouse_pos = None
        self.nav_current = None      # tab id to highlight; None hides the chrome
        self.nav_enabled = {}        # tab id -> bool

    # ------------------------------------------------------------------ text
    def text_width(self, value, *, title=False):
        font = self.title_font if title else self.font
        return font.size(str(value))[0]

    def fit_text(self, value, max_width, *, title=False):
        """Shorten ``value`` with "..." so it fits in ``max_width`` pixels."""
        value = str(value)
        if self.text_width(value, title=title) <= max_width:
            return value
        while value and self.text_width(value + "...", title=title) > max_width:
            value = value[:-1]
        return value + "..." if value else ""

    def text(self, value, x, y, color=TEXT, *, title=False, max_width=None):
        font = self.title_font if title else self.font
        value = str(value)
        if max_width is None:
            max_width = max(0, self.width - x - 12)
        if max_width:
            value = self.fit_text(value, max_width, title=title)
        self.surface.blit(font.render(value, True, color), (x, y))

    def wrapped_text(self, value, x, y, max_width, color=TEXT, *, line_height=30, max_lines=None):
        """Render word-wrapped text and return the next y position."""
        lines = []
        for paragraph in str(value).splitlines() or [""]:
            words = paragraph.split()
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if current and self.font.size(candidate)[0] > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = self.fit_text(lines[-1] + " ...", max_width)
        for line in lines:
            self.text(line, x, y, color, max_width=max_width)
            y += line_height
        return y

    # ----------------------------------------------------------------- hover
    def hovered(self, rect):
        return self.mouse_pos is not None and rect.collidepoint(self.mouse_pos)

    # ------------------------------------------------------------ primitives
    def clear(self, color=BACKGROUND):
        self.surface.fill(color)

    def panel(self, rect, color=PANEL_FILL, border=PANEL_BORDER):
        shadow = self.pg.Rect(rect.x + 4, rect.y + 5, rect.width, rect.height)
        self.pg.draw.rect(self.surface, (10, 13, 21), shadow, border_radius=8)
        self.pg.draw.rect(self.surface, color, rect, border_radius=8)
        self.pg.draw.rect(self.surface, border, rect, 2, border_radius=8)
        inner = self.pg.Rect(rect.x + 5, rect.y + 5, max(0, rect.width - 10), 1)
        if inner.width:
            self.pg.draw.rect(self.surface, (115, 130, 155), inner)

    def button(self, rect, label, selected=False):
        if selected:
            fill = BUTTON_SELECTED
        elif self.hovered(rect):
            fill = BUTTON_HOVER
        else:
            fill = BUTTON_FILL
        self.panel(rect, fill)
        if selected:
            self.text("›", rect.x + 14, rect.y + 10, HIGHLIGHT)
        self.text(
            label, rect.x + 34 if selected else rect.x + 16,
            rect.y + 11, max_width=rect.width - 48 if selected else rect.width - 32,
        )

    def vertical_menu(self, title, options, selected, *, width=340, row_height=48):
        """Draw a centered, top-to-bottom RPG-style menu and return its rects."""
        total_height = 78 + len(options) * (row_height + 10)
        panel = self.pg.Rect(
            (self.width - width) // 2,
            max(70, (self.height - total_height) // 2),
            width,
            total_height,
        )
        self.panel(panel, (23, 29, 43), (145, 118, 70))
        self.text(
            title, panel.centerx - self.text_width(title, title=True) // 2,
            panel.y + 20, GOLD, title=True, max_width=width - 32,
        )
        rects = []
        top = panel.y + 68
        for index, label in enumerate(options):
            rect = self.pg.Rect(
                panel.x + 24, top + index * (row_height + 10),
                panel.width - 48, row_height,
            )
            self.button(rect, label, index == selected)
            rects.append(rect)
        return rects

    def action_button(self, rect, key, label, *, enabled=True, selected=False):
        """Render a discoverable action button while preserving keyboard hints."""
        if not enabled:
            color, border, text_color = (35, 39, 48), (60, 66, 78), DISABLED
        else:
            if selected:
                color = BUTTON_SELECTED
            elif self.hovered(rect):
                color = BUTTON_HOVER
            else:
                color = BUTTON_FILL
            border = HIGHLIGHT if self.hovered(rect) else BUTTON_BORDER
            text_color = TEXT
        self.panel(rect, color, border)
        suffix = "" if enabled else " — yok"
        label_text = self.fit_text(f"[{key}] {label}{suffix}", rect.width - 16)
        self.text(label_text, rect.x + 10, rect.y + (rect.height - 18) // 2, text_color)

    def bar(self, rect, ratio, color):
        """Horizontal progress bar; ``ratio`` is clamped to 0..1."""
        ratio = max(0.0, min(1.0, ratio))
        self.pg.draw.rect(self.surface, (14, 18, 26), rect, border_radius=5)
        if ratio > 0:
            fill = self.pg.Rect(rect.x, rect.y, max(4, int(rect.width * ratio)), rect.height)
            self.pg.draw.rect(self.surface, color, fill, border_radius=5)
        self.pg.draw.rect(self.surface, STRIP_BORDER, rect, 1, border_radius=5)

    def resource_icon(self, x, y, resource, size=16):
        """Small coloured tile that identifies a resource at a glance."""
        rect = self.pg.Rect(x, y, size, size)
        self.pg.draw.rect(self.surface, resource_color(resource), rect, border_radius=4)
        self.pg.draw.rect(self.surface, (14, 18, 26), rect, 1, border_radius=4)

    def chip_flow(self, items, x, y, max_x, *, color=GOLD, gap=6, row_height=25):
        """Lay chips out left-to-right, wrapping at ``max_x``; returns the next y."""
        cursor = x
        for label in items:
            width = self.text_width(label) + 16
            if cursor > x and cursor + width > max_x:
                cursor, y = x, y + row_height
            cursor += self.chip(cursor, y, label, color) + gap
        return y + row_height

    def chip(self, x, y, label, color=GOLD, *, height=22):
        """Rounded tag; returns its width so callers can flow chips."""
        width = self.text_width(label) + 16
        rect = self.pg.Rect(x, y, width, height)
        self.pg.draw.rect(self.surface, (24, 31, 45), rect, border_radius=11)
        self.pg.draw.rect(self.surface, STRIP_BORDER, rect, 1, border_radius=11)
        self.text(label, x + 8, y + 3, color)
        return width

    # ------------------------------------------------------------ navigation
    def nav_rects(self):
        total = len(NAV_TABS) * self.NAV_TAB_WIDTH + (len(NAV_TABS) - 1) * self.NAV_GAP
        left = self.width - 24 - total
        return {
            tab: self.pg.Rect(
                left + index * (self.NAV_TAB_WIDTH + self.NAV_GAP),
                self.NAV_TOP,
                self.NAV_TAB_WIDTH,
                self.NAV_HEIGHT,
            )
            for index, (tab, _label) in enumerate(NAV_TABS)
        }

    def nav_hit(self, pos):
        """Return the tab id under ``pos`` (or None)."""
        if pos is None:
            return None
        for tab, rect in self.nav_rects().items():
            if rect.collidepoint(pos):
                return tab
        return None

    def _draw_nav(self):
        rects = self.nav_rects()
        for tab, label in NAV_TABS:
            rect = rects[tab]
            enabled = self.nav_enabled.get(tab, True)
            current = tab == self.nav_current
            if current:
                fill, border, color = BUTTON_SELECTED, HIGHLIGHT, (245, 220, 155)
            elif not enabled:
                fill, border, color = (30, 34, 43), (52, 58, 70), DISABLED
            elif self.hovered(rect):
                fill, border, color = BUTTON_HOVER, HIGHLIGHT, TEXT
            else:
                fill, border, color = BUTTON_FILL, STRIP_BORDER, TEXT_SOFT
            self.panel(rect, fill, border)
            self.text(
                label,
                rect.centerx - self.text_width(label) // 2,
                rect.y + (rect.height - 18) // 2,
                color,
            )

    # ----------------------------------------------------------------- frame
    def frame(self, title, tick=None):
        self.clear()
        self.pg.draw.line(
            self.surface, (122, 96, 55), (24, 66), (self.width - 24, 66), 2,
        )
        if self.nav_current is not None:
            title = self.fit_text(title, self.nav_rects()["world"].x - 28 - 16, title=True)
            self.text(title, 28, 22, title=True)
            self._draw_nav()
        else:
            self.text(title, 28, 22, title=True)
            if tick is not None:
                self.text(f"Tick {tick}", self.width - 150, 34, MUTED)

    def hud(self, service, actor_id="hero"):
        """Status strip shared by gameplay screens (+ resource bar on main ones)."""
        snapshot = service.state()
        stats = service.actor_stats(actor_id)
        location = "Bilinmeyen konum"
        if stats is not None:
            actor = service.actor(actor_id)
            if actor is not None and actor.location_id:
                world_map = service.application.holder.current.movement.map_for(actor.world_id)
                if world_map is not None and world_map.get(actor.location_id) is not None:
                    location = world_map.get(actor.location_id).name
        try:
            gold = service.balance(actor_id, "gold").amount
        except (KeyError, ValueError):
            gold = 0

        self.panel(self.pg.Rect(24, 72, self.width - 48, 42), STRIP_FILL, STRIP_BORDER)

        x = 40
        name = self.fit_text(stats["name"] if stats else actor_id, 170)
        self.text(name, x, 82, TEXT)
        x += self.text_width(name) + 16

        if stats is not None:
            current, maximum = stats["current_hit_points"], stats["max_hit_points"]
            ratio = current / maximum if maximum else 0
            color = GOOD if ratio > 0.5 else WARN if ratio > 0.25 else BAD
            self.bar(self.pg.Rect(x, 87, 110, 14), ratio, color)
            x += 120
            hp_text = f"{current}/{maximum}"
            self.text(hp_text, x, 82, MUTED)
            x += self.text_width(hp_text) + 18
        else:
            self.text("HP —", x, 82, MUTED)
            x += self.text_width("HP —") + 18

        self.pg.draw.circle(self.surface, RESOURCE_COLORS["gold"], (x + 7, 94), 7)
        self.pg.draw.circle(self.surface, (150, 120, 40), (x + 7, 94), 7, 2)
        gold_text = f"{gold}"
        self.text(gold_text, x + 20, 82, GOLD)
        x += 20 + self.text_width(gold_text) + 24

        right = self.fit_text(
            f"{location}  •  Tick {snapshot.simulation_tick}",
            self.width - 40 - x,
        )
        self.text(right, self.width - 40 - self.text_width(right), 82, (170, 185, 205))

        if self.nav_current is not None:
            self.resource_bar(service)

    def resource_bar(self, service, inventory_id="player"):
        """Stockpile strip at the bottom of the management screens."""
        rect = self.pg.Rect(24, self.height - 74, self.width - 48, 36)
        self.panel(rect, STRIP_FILL, STRIP_BORDER)
        try:
            stocks = list(service.inventory(inventory_id).stocks)
        except (KeyError, ValueError, RuntimeError, AttributeError):
            stocks = []
        if not stocks:
            self.text("Çanta boş", rect.x + 16, rect.y + 9, MUTED)
            return
        x = rect.x + 16
        limit = rect.right - 16
        for position, (resource, amount, _unit) in enumerate(stocks):
            label = f"{resource_name(resource)} {amount}"
            needed = 22 + self.text_width(label) + 18
            remaining = len(stocks) - position
            if x + needed > limit - (50 if remaining > 1 else 0):
                self.text(f"+{remaining}", x, rect.y + 9, MUTED)
                return
            self.resource_icon(x, rect.y + 10, resource)
            self.text(label, x + 22, rect.y + 9, TEXT_SOFT)
            x += needed

    def footer(self, value):
        self.text(value, 28, self.height - 28, MUTED, max_width=self.width - 56)

    def quest_panel(self, service, rect):
        self.panel(rect, (27, 35, 50), (86, 105, 135))
        quests = service.application.holder.current.quest_log.active()
        self.text("Görev Takibi", rect.x + 16, rect.y + 14, GOLD)
        if not quests:
            self.text("Aktif görev yok.", rect.x + 16, rect.y + 54, MUTED)
            return
        quest = quests[0]
        self.text(self.fit_text(quest.title, rect.width - 32), rect.x + 16, rect.y + 52, TEXT)
        y = rect.y + 82
        max_objectives = 4 if rect.height >= 250 else 2
        for objective in quest.objectives[:max_objectives]:
            marker = "[x]" if objective.completed else "[ ]"
            line = f"{marker} {objective.description} ({objective.progress}/{objective.required})"
            self.wrapped_text(
                line, rect.x + 16, y, rect.width - 32, TEXT_SOFT,
                line_height=20, max_lines=1,
            )
            y += 24
        target = next((item.target_id for item in quest.objectives if item.target_id), None)
        if target:
            target_name = target
            bundle = service.application.holder.current
            actors = service.state().actors
            if actors:
                world = bundle.movement.map_for(actors[0].world_id)
                location = world.get(target) if world is not None else None
                if location is not None:
                    target_name = location.name
            if target_name == target:
                npc = bundle.social.npcs.get(target)
                if npc is not None:
                    target_name = npc.name
            self.text(self.fit_text(f"Hedef: {target_name}", rect.width - 32), rect.x + 16, y + 4, MUTED)
            y += 26
        reward = quest.reward
        reward_text = f"Ödül: {reward.currency} altın"
        if reward.experience:
            reward_text += f", {reward.experience} XP"
        self.text(reward_text, rect.x + 16, y + 4, GOLD, max_width=rect.width - 32)
        self.text(
            f"Durum: {quest.state.value}", rect.x + 16, rect.bottom - 28, GOOD,
            max_width=rect.width - 32,
        )

    # ------------------------------------------------------------------ toast
    TOAST_COLORS = {
        "info": ((38, 60, 88), (110, 135, 170), (225, 235, 250)),
        "ok": ((34, 72, 52), (110, 200, 140), (215, 245, 225)),
        "error": ((88, 42, 48), (200, 110, 110), (255, 220, 220)),
    }

    def toast(self, message, level="info"):
        fill, border, color = self.TOAST_COLORS.get(level, self.TOAST_COLORS["info"])
        rect = self.pg.Rect(24, self.height - 70, self.width - 48, 42)
        self.panel(rect, fill, border)
        self.text(message, rect.x + 16, rect.y + 11, color, max_width=rect.width - 32)

    def error(self, message):
        self.toast(message, "error")

    # -------------------------------------------------------------------- maps
    def map_edge(self, start, end, color=PANEL_BORDER, width=4):
        self.pg.draw.line(self.surface, color, start, end, width)

    def map_node(self, position, color=BUTTON_SELECTED, *, selected=False, current=False):
        radius = 23 if selected else 18
        self.pg.draw.circle(self.surface, color, position, radius)
        border = HIGHLIGHT if current else MUTED
        self.pg.draw.circle(self.surface, border, position, radius, 3)

    def world_map(self, world_map, current_location_id=None, selected_location_id=None, rect=None):
        """Draw a location graph inside a panel using content-defined positions."""
        rect = rect or self.pg.Rect(24, 130, 620, 350)
        locations = world_map.locations()
        positions = {}
        for index, location in enumerate(locations):
            raw = location.position or (150 + index * 180, 220)
            positions[location.location_id] = (rect.x + 16 + raw[0], rect.y - 18 + raw[1])
        drawn = set()
        for location in locations:
            for neighbor in world_map.neighbors(location.location_id):
                edge = tuple(sorted((location.location_id, neighbor.location_id)))
                if edge in drawn:
                    continue
                self.map_edge(positions[location.location_id], positions[neighbor.location_id])
                drawn.add(edge)
        for location in locations:
            position = positions[location.location_id]
            self.map_node(
                position,
                selected=location.location_id == selected_location_id,
                current=location.location_id == current_location_id,
            )
            self.text(location.name, position[0] - 34, position[1] + 30, TEXT)
        return positions
