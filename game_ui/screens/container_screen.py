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

    @property
    def pointer_capture(self):
        return self._drag_item_id is not None

    def _take_all(self, actor_id, inventory_id):
        view = self.service.open_container(actor_id, inventory_id, self.container_id)
        moved = 0
        blocked = False
        for item_id, quantity in tuple(view.items):
            try:
                self.service.transfer_actor_item_from_container(actor_id, inventory_id, self.container_id, item_id, quantity)
                moved += quantity
            except (ValueError, RuntimeError, GameplayServiceError):
                blocked = True
        self.message = (f"{moved} eşya alındı; kapasite nedeniyle kalanlar sandıkta." if blocked
                        else f"{moved} eşya envantere aktarıldı." if moved else "Sandık boş.")

    def handle(self, state):
        if self.container_id is None:
            return None
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(actor_id, inventory_id, self.container_id)
            except GameplayServiceError:
                action = next((name for name, rect in self._action_rects.items()
                               if state.mouse_clicked and state.mouse_pos and rect.collidepoint(state.mouse_pos)), None)
                if state.pressed("lockpick"): action = "lockpick"
                elif state.pressed("force_lock"): action = "force"
                elif state.pressed("confirm") and lock and lock.required_key_id: action = "key"
                if lock and lock.locked and action == "key":
                    self.message = ("Kilit anahtarla açıldı." if self.service.unlock_with_key(actor_id, inventory_id, lock.lock_id, lock.required_key_id) else "Uygun anahtar bulunamadı.")
                elif lock and lock.locked and not lock.jammed and not lock.broken and action == "lockpick":
                    tool = self._find_tool(inventory_id, lock.lockpick_allowed_tool_tags)
                    self.message = self._format_attempt(self.service.resolve_lockpick(actor_id, inventory_id, lock.lock_id, tool_item_id=tool))
                elif lock and lock.locked and not lock.jammed and not lock.broken and action == "force":
                    tool = self._find_tool(inventory_id, lock.force_required_tool_tags)
                    self.message = self._format_attempt(self.service.resolve_force_lock(actor_id, inventory_id, lock.lock_id, tool_item_id=tool))
                return None

            entries = tuple(view.items)
            if state.mouse_clicked and state.mouse_pos:
                if self._take_all_rect and self._take_all_rect.collidepoint(state.mouse_pos):
                    self._take_all(actor_id, inventory_id)
                    self._drag_item_id = None
                    return None
                for i, rect in enumerate(self._row_rects):
                    if rect.collidepoint(state.mouse_pos) and i < len(entries):
                        self.selected_index = i
                        self._drag_item_id = entries[i][0]
                        break
            if state.mouse_button_up and self._drag_item_id:
                item_id, self._drag_item_id = self._drag_item_id, None
                quantity = next((amount for key, amount in entries if key == item_id), 0)
                if quantity:
                    self.service.transfer_actor_item_from_container(actor_id, inventory_id, self.container_id, item_id, quantity)
                    self.message = "Eşya envantere aktarıldı."
            if state.pressed("confirm") and entries:
                item_id, quantity = entries[min(self.selected_index, len(entries)-1)]
                self.service.transfer_actor_item_from_container(actor_id, inventory_id, self.container_id, item_id, quantity)
                self.message = "Eşya envantere aktarıldı."
            self.selected_index = min(self.selected_index, max(0, len(entries)-1))
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            self._drag_item_id = None
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

    @staticmethod
    def _grid_slot_rects(renderer, origin_x, origin_y):
        return tuple(renderer.pg.Rect(origin_x+(i%5)*78, origin_y+(i//5)*78, 64, 64) for i in range(15))

    @staticmethod
    def _draw_empty_slot(renderer, rect, selected=False, hovered=False):
        pg=renderer.pg
        border=GOLD if selected else (130,99,61) if hovered else (78,66,54)
        pg.draw.rect(renderer.surface,(15,14,14),rect,border_radius=7)
        pg.draw.rect(renderer.surface,(37,32,28),rect.inflate(-5,-5),border_radius=5)
        pg.draw.rect(renderer.surface,border,rect,2,border_radius=7)
        cx,cy=rect.center
        pg.draw.line(renderer.surface,(65,55,45),(cx,cy-8),(cx+7,cy),1)
        pg.draw.line(renderer.surface,(65,55,45),(cx+7,cy),(cx,cy+8),1)
        pg.draw.line(renderer.surface,(65,55,45),(cx,cy+8),(cx-7,cy),1)
        pg.draw.line(renderer.surface,(65,55,45),(cx-7,cy),(cx,cy-8),1)

    @staticmethod
    def _draw_item_icon(renderer,item,rect):
        pg,surface=renderer.pg,renderer.surface
        category=str(getattr(item,"category","misc")).lower()
        tags={str(tag).lower() for tag in getattr(item,"tags",())}
        name=str(getattr(item,"name","")).lower()
        cx,cy=rect.center
        if tags.intersection({"weapon","melee"}) or any(w in category or w in name for w in ("weapon","sword","blade")):
            pg.draw.polygon(surface,(225,213,185),[(cx,cy-20),(cx+7,cy+4),(cx,cy+12),(cx-7,cy+4)])
            pg.draw.line(surface,GOLD,(cx,cy+8),(cx,cy+23),4)
            pg.draw.line(surface,(113,76,43),(cx-10,cy+12),(cx+10,cy+12),4)
        elif tags.intersection({"consumable","potion"}) or any(w in category or w in name for w in ("potion","elixir","drink")):
            pg.draw.rect(surface,(106,157,181),pg.Rect(cx-8,cy-13,16,28),border_radius=5)
            pg.draw.rect(surface,GOLD,pg.Rect(cx-5,cy-21,10,9),border_radius=2)
            pg.draw.rect(surface,(185,82,72),pg.Rect(cx-6,cy+2,12,10),border_radius=3)
        elif tags.intersection({"armor","armour"}) or any(w in category or w in name for w in ("armor","shield")):
            pg.draw.polygon(surface,(117,143,151),[(cx-18,cy-17),(cx+18,cy-17),(cx+14,cy+5),(cx,cy+21),(cx-14,cy+5)])
            pg.draw.polygon(surface,GOLD,[(cx,cy-11),(cx+9,cy-7),(cx+7,cy+4),(cx,cy+13),(cx-7,cy+4),(cx-9,cy-7)],2)
        else:
            pg.draw.polygon(surface,(122,137,151),[(cx,cy-19),(cx+16,cy-2),(cx+9,cy+17),(cx-9,cy+17),(cx-16,cy-2)])
            pg.draw.polygon(surface,GOLD,[(cx,cy-11),(cx+9,cy-1),(cx+5,cy+11),(cx-5,cy+11),(cx-9,cy-1)],2)

    def render(self,renderer):
        if self.container_id is None: return
        try:
            actor_id,inventory_id=self._actor_context()
            lock=self.service.container_lock_state(self.container_id)
            try: view=self.service.open_container(actor_id,inventory_id,self.container_id)
            except GameplayServiceError:
                self._render_locked(renderer,lock)
                return
            pg=renderer.pg
            renderer.panel(pg.Rect(52,145,816,478),(25,21,19),(163,119,64))
            renderer.panel(pg.Rect(59,152,802,464),(35,29,25),(89,67,47))
            self._draw_chest_emblem(renderer,776,158)
            renderer.text(view.name.upper(),84,169,GOLD,title=True,max_width=660)
            renderer.text("SANDIK İÇERİĞİ",84,224,TEXT_SOFT)
            renderer.text(f"{len(view.items)} eşya türü",720,224,MUTED)
            self._row_rects=[]
            for index,rect in enumerate(self._grid_slot_rects(renderer,150,270)):
                entry=view.items[index] if index<len(view.items) else None
                selected=index==self.selected_index
                self._draw_empty_slot(renderer,rect,selected and entry is None,renderer.hovered(rect))
                if entry is None: continue
                item_id,amount=entry
                item=self.service.item(item_id)
                if selected:
                    pg.draw.rect(renderer.surface,(75,51,32),rect,border_radius=7)
                    pg.draw.rect(renderer.surface,GOLD,rect,3,border_radius=7)
                self._draw_item_icon(renderer,item,rect.inflate(-12,-12))
                badge=pg.Rect(rect.right-25,rect.bottom-21,21,17)
                pg.draw.rect(renderer.surface,(12,12,13),badge,border_radius=4)
                pg.draw.rect(renderer.surface,(158,119,65),badge,1,border_radius=4)
                renderer.text(str(amount),badge.x+3,badge.y,GOLD,max_width=15)
                self._row_rects.append(rect)
            self._take_all_rect=pg.Rect(650,568,184,38)
            renderer.action_button(self._take_all_rect,"T","Tümünü Al")
            renderer.text(self.message,84,575,GOOD if "aktarıldı" in self.message else TEXT_SOFT,max_width=540)
        except (KeyError,ValueError,RuntimeError,GameplayServiceError) as error:
            renderer.text(f"Sandık görüntülenemedi: {error}",72,180,WARN)

__all__ = ["ContainerScreen"]
