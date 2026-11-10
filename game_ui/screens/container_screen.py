"""Movable fantasy-style window for inspecting and transferring container contents."""

from ..renderer import (
    GOLD, TEXT, TEXT_SOFT, MUTED, GOOD, WARN, BAD,
    PANEL_BORDER, STRIP_BORDER,
)
from application import GameplayServiceError


class ContainerScreen:
    """Compact two-pane container window with capacity bars and safe transfers."""

    def __init__(self, service):
        self.service = service
        self.container_id = None
        self.active_side = "container"
        self.selected_index = 0
        self.message = "Bir eşya seçin. Enter: taşı"
        self._row_rects = ()
        self._action_rects = {}

    def set_container(self, container_id):
        if not isinstance(container_id, str) or not container_id.strip():
            raise ValueError("container_id is required.")
        self.container_id = container_id
        self.active_side = "container"
        self.selected_index = 0
        self.message = "Sandık incelenmeye hazır."

    def _actor_context(self):
        actors = self.service.state().actors
        if not actors:
            raise GameplayServiceError("Aktif bir karakter bulunamadı.")
        actor = actors[0]
        if actor.inventory_id is None:
            raise GameplayServiceError("Karakterin envanteri henüz bağlanmamış.")
        return actor.actor_id, actor.inventory_id

    def _player_items(self, inventory_id):
        return self.service.inventory(inventory_id).items

    def _container_items(self, view):
        return view.items

    def _items_for_side(self, view, inventory_id):
        return self._container_items(view) if self.active_side == "container" else self._player_items(inventory_id)

    def _find_tool(self, inventory_id, allowed_tags):
        if not allowed_tags:
            return None
        for item_id, quantity in self._player_items(inventory_id):
            if quantity < 1:
                continue
            item = self.service.item(item_id)
            if item is not None and set(item.tags).intersection(allowed_tags):
                return item_id
        return None

    @staticmethod
    def _format_attempt(result):
        if not result.attempted:
            return result.message
        verdict = "BAŞARILI" if result.success else "BAŞARISIZ"
        return f"{verdict} — d20: {result.roll} + {result.modifier} = {result.total} / DC {result.difficulty_class}"

    @staticmethod
    def _draw_chest_emblem(renderer, x, y):
        """Draw a small chest motif using native UI primitives (no external asset)."""
        pg = renderer.pg
        body = pg.Rect(x, y + 18, 66, 42)
        pg.draw.rect(renderer.surface, (91, 57, 31), body, border_radius=6)
        pg.draw.rect(renderer.surface, (181, 132, 69), body, 3, border_radius=6)
        lid = pg.Rect(x - 3, y + 8, 72, 22)
        pg.draw.rect(renderer.surface, (126, 82, 42), lid, border_radius=7)
        pg.draw.rect(renderer.surface, (205, 163, 91), lid, 2, border_radius=7)
        pg.draw.line(renderer.surface, (207, 174, 111), (x + 32, y + 12), (x + 32, y + 58), 3)
        pg.draw.rect(renderer.surface, (222, 190, 112), pg.Rect(x + 27, y + 30, 12, 16), border_radius=3)
        pg.draw.circle(renderer.surface, (65, 45, 28), (x + 33, y + 37), 2)

    @staticmethod
    def _capacity_bar(renderer, x, y, width, label, current, maximum, unit):
        renderer.text(label, x, y, TEXT_SOFT)
        if maximum is None:
            ratio, value = 0.0, f"{current:.1f} {unit} / Sınırsız"
        else:
            ratio = current / maximum if maximum > 0 else (1.0 if current > 0 else 0.0)
            value = f"{current:.1f} / {maximum:.1f} {unit}"
        renderer.text(value, x, y + 22, MUTED, max_width=width)
        color = BAD if maximum is not None and ratio >= 1 else GOLD
        renderer.bar(renderer.pg.Rect(x, y + 47, width, 9), ratio, color)

    def handle(self, state):
        if self.container_id is None:
            return None
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(actor_id, inventory_id, self.container_id)
            except GameplayServiceError:
                action = None
                if state.mouse_clicked and state.mouse_pos is not None:
                    for action_name, rect in self._action_rects.items():
                        if rect.collidepoint(state.mouse_pos):
                            action = action_name
                            break
                if state.pressed("lockpick"):
                    action = "lockpick"
                elif state.pressed("force_lock"):
                    action = "force"
                elif state.pressed("confirm") and lock is not None and lock.required_key_id:
                    action = "key"
                if lock is not None and lock.locked and action == "key":
                    self.message = (
                        "Kilit anahtarla açıldı."
                        if self.service.unlock_with_key(actor_id, inventory_id, lock.lock_id, lock.required_key_id)
                        else "Uygun anahtar bulunamadı veya anahtar size ait değil."
                    )
                elif lock is not None and lock.locked and not lock.jammed and not lock.broken and action == "lockpick":
                    tool_id = self._find_tool(inventory_id, lock.lockpick_allowed_tool_tags)
                    result = self.service.resolve_lockpick(actor_id, inventory_id, lock.lock_id, tool_item_id=tool_id)
                    self.message = self._format_attempt(result)
                elif lock is not None and lock.locked and not lock.jammed and not lock.broken and action == "force":
                    tool_id = self._find_tool(inventory_id, lock.force_required_tool_tags)
                    result = self.service.resolve_force_lock(actor_id, inventory_id, lock.lock_id, tool_item_id=tool_id)
                    self.message = self._format_attempt(result)
                elif lock is not None and lock.jammed:
                    self.message = "Kilit sıkışmış. Önce kilidin durumunu çözmelisiniz."
                elif lock is not None and lock.broken and lock.locked:
                    self.message = "Kilit hasarlı ve kapalı durumda."
                elif action is None:
                    self.message = "Konteyner kilitli."
                return None

            items = self._items_for_side(view, inventory_id)
            if state.pressed("left") or state.pressed("right"):
                self.active_side = "player" if self.active_side == "container" else "container"
                self.selected_index = 0
                items = self._items_for_side(view, inventory_id)
            if items and state.pressed("up"):
                self.selected_index = (self.selected_index - 1) % len(items)
            if items and state.pressed("down"):
                self.selected_index = (self.selected_index + 1) % len(items)
            if state.mouse_clicked and state.mouse_pos is not None:
                for index, rect in enumerate(self._row_rects):
                    if rect.collidepoint(state.mouse_pos):
                        self.selected_index = index
                        break
            if state.pressed("confirm") and items:
                item_id, _quantity = items[self.selected_index]
                if self.active_side == "container":
                    self.service.transfer_actor_item_from_container(actor_id, inventory_id, self.container_id, item_id, 1)
                    self.message = "Eşya çantaya aktarıldı."
                else:
                    self.service.transfer_actor_item_to_container(actor_id, inventory_id, self.container_id, item_id, 1)
                    self.message = "Eşya sandığa yerleştirildi."
                self.selected_index = 0
        except (KeyError, ValueError, RuntimeError) as error:
            self.message = f"İşlem yapılamadı: {error}"
        return None

    def _render_locked(self, renderer, lock):
        self._action_rects = {}
        renderer.panel(renderer.pg.Rect(40, 140, 724, 350), (29, 36, 49), (130, 102, 61))
        self._draw_chest_emblem(renderer, 680, 155)
        renderer.text("KİLİTLİ SANDIK", 62, 158, GOLD, title=True)
        status = "Sıkışmış" if lock and lock.jammed else "Hasarlı" if lock and lock.broken else "Kilitli"
        renderer.chip(62, 210, f"Durum: {status}", WARN)
        renderer.wrapped_text(
            "İçindekiler kilit açılana kadar gizli. Sandığı açmak için uygun bir yöntem seçin.",
            62, 252, 570, TEXT_SOFT, line_height=25, max_lines=2,
        )
        if lock is not None and lock.required_key_id:
            renderer.text("Anahtar", 62, 318, GOLD)
            renderer.text(f"Gerekli anahtar: {lock.required_key_id}", 62, 346, TEXT_SOFT)
            key_rect = renderer.pg.Rect(62, 386, 210, 44)
            renderer.action_button(key_rect, "ENTER", "Anahtarla aç")
            self._action_rects["key"] = key_rect
        if lock is not None and lock.lockpick_profile_id:
            renderer.text(
                f"Maymunculuk  •  Beceri {lock.lockpick_minimum_skill}+  •  DC {lock.lockpick_difficulty_class}",
                300, 318, TEXT_SOFT, max_width=440,
            )
            pick_rect = renderer.pg.Rect(300, 386, 210, 44)
            renderer.action_button(pick_rect, "T", "Maymunculuk dene")
            self._action_rects["lockpick"] = pick_rect
        if lock is not None and lock.force_profile_id:
            renderer.text(
                f"Zorlama  •  Güç {lock.force_minimum_strength}+  •  DC {lock.force_difficulty_class}",
                300, 350, TEXT_SOFT, max_width=440,
            )
            force_rect = renderer.pg.Rect(526, 386, 210, 44)
            renderer.action_button(force_rect, "F", "Kilidi zorla")
            self._action_rects["force"] = force_rect
        renderer.text(self.message, 62, 456, GOOD if "BAŞARILI" in self.message or "açıldı" in self.message else WARN)
        renderer.footer("Enter: anahtar   T: maymuncuk   F: zorla   X: pencereyi kapat")

    def render(self, renderer):
        if self.container_id is None:
            renderer.text("Bir sandık seçilmedi.", 52, 154, MUTED)
            return
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(actor_id, inventory_id, self.container_id)
            except GameplayServiceError:
                self._render_locked(renderer, lock)
                return

            player_items = self._player_items(inventory_id)
            container_items = self._container_items(view)
            outer = renderer.pg.Rect(40, 140, 724, 410)
            renderer.panel(outer, (25, 20, 18), (166, 119, 61))
            inner = renderer.pg.Rect(46, 146, 712, 398)
            renderer.panel(inner, (34, 29, 27), (91, 68, 45))
            self._draw_chest_emblem(renderer, 680, 151)
            renderer.text(view.name.upper(), 62, 154, GOLD, title=True, max_width=560)
            renderer.chip(62, 205, "AÇIK", GOOD)
            renderer.text("SANDIK KAPASİTESİ", 62, 239, GOLD)

            self._capacity_bar(renderer, 62, 267, 205, "Ağırlık", view.contents_weight_kg, view.max_contents_weight_kg, "kg")
            slot_max = float(view.max_slots) if view.max_slots is not None else None
            self._capacity_bar(renderer, 292, 267, 205, "Yuvalar", float(view.contents_slots), slot_max, "slot")
            self._capacity_bar(renderer, 522, 267, 205, "Hacim", view.contents_volume_liters, view.max_contents_volume_liters, "L")

            left_panel = renderer.pg.Rect(54, 344, 338, 200)
            right_panel = renderer.pg.Rect(412, 344, 338, 200)
            renderer.panel(left_panel, (27, 23, 22), GOLD if self.active_side == "container" else (105, 82, 59))
            renderer.panel(right_panel, (27, 23, 22), GOLD if self.active_side == "player" else (105, 82, 59))
            renderer.text("SANDIK", 68, 352, GOLD if self.active_side == "container" else TEXT_SOFT)
            renderer.text("KARAKTER ÇANTASI", 426, 352, GOLD if self.active_side == "player" else TEXT_SOFT)
            renderer.text(str(len(container_items)), 354, 352, MUTED)
            renderer.text(str(len(player_items)), 716, 352, MUTED)

            self._row_rects = []
            slot_size, gap, columns = 48, 7, 5
            for side, entries, origin_x in (
                ("container", container_items, 68),
                ("player", player_items, 426),
            ):
                for index, (item_id, amount) in enumerate(entries[:15]):
                    row, column = divmod(index, columns)
                    x = origin_x + column * (slot_size + gap)
                    y = 380 + row * (slot_size + gap)
                    rect = renderer.pg.Rect(x, y, slot_size, slot_size)
                    selected = side == self.active_side and index == self.selected_index
                    renderer.panel(
                        rect,
                        (76, 52, 34) if selected else (42, 34, 29),
                        GOLD if selected else (104, 77, 51),
                    )
                    item = self.service.item(item_id)
                    name = item.name if item is not None else item_id
                    icon_color = (154, 112, 67)
                    if item is not None and getattr(item, "tags", None):
                        icon_color = (91, 119, 94)
                    icon_rect = renderer.pg.Rect(x + 8, y + 5, 32, 30)
                    renderer.pg.draw.rect(renderer.surface, icon_color, icon_rect, border_radius=5)
                    renderer.pg.draw.rect(renderer.surface, (205, 166, 103), icon_rect, 1, border_radius=5)
                    glyph = name[:1].upper() if name else "?"
                    renderer.text(glyph, x + 19, y + 10, (245, 225, 184))
                    renderer.text(str(amount), x + 31, y + 34, GOLD)
                    if side == self.active_side:
                        self._row_rects.append(rect)
            if not container_items:
                self._draw_chest_emblem(renderer, 84, 398)
                renderer.text("Sandık henüz boş.", 164, 402, TEXT_SOFT)
                renderer.text("Eşyalar buraya yerleştirildiğinde görünecek.", 164, 430, MUTED, max_width=210)
            if not player_items:
                renderer.text("Çantada eşya yok.", 430, 402, TEXT_SOFT)
                renderer.text("Taşınabilir eşya bulunmuyor.", 430, 430, MUTED, max_width=280)

            renderer.text(self.message, 62, 555, GOOD if "aktarıldı" in self.message else TEXT_SOFT, max_width=680)
            renderer.footer("Sol/Sağ: taraf değiştir   Slot seç + Enter: 1 adet taşı")
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            renderer.text(f"Sandık görüntülenemedi: {error}", 52, 170, WARN)



__all__ = ["ContainerScreen"]
