"""Movable window for inspecting and transferring container contents."""

from ..renderer import GOLD, TEXT_SOFT, MUTED, GOOD, WARN
from application import GameplayServiceError


class ContainerScreen:
    """Two-pane container window with capacity indicators and safe transfers."""

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
        self.message = "Sandık açıldı."

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
        return (
            self._container_items(view)
            if self.active_side == "container"
            else self._player_items(inventory_id)
        )

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
        return (
            f"{verdict} — d20: {result.roll}  +  {result.modifier}  =  {result.total}  /  DC {result.difficulty_class}"
        )
    def handle(self, state):
        if self.container_id is None:
            return None
        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(
                    actor_id, inventory_id, self.container_id
                )
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
                    if self.service.unlock_with_key(actor_id, inventory_id, lock.lock_id, lock.required_key_id):
                        self.message = "Kilit anahtarla açıldı."
                    else:
                        self.message = "Uygun anahtar bulunamadı veya anahtar size ait değil."
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
                self.active_side = (
                    "player" if self.active_side == "container" else "container"
                )
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
                    self.service.transfer_actor_item_from_container(
                        actor_id, inventory_id, self.container_id, item_id, 1
                    )
                    self.message = "Eşya çantaya aktarıldı."
                else:
                    self.service.transfer_actor_item_to_container(
                        actor_id, inventory_id, self.container_id, item_id, 1
                    )
                    self.message = "Eşya konteynere aktarıldı."
                self.selected_index = 0
        except (KeyError, ValueError, RuntimeError) as error:
            self.message = f"İşlem yapılamadı: {error}"
        return None

    def render(self, renderer):
        renderer.panel(
            renderer.pg.Rect(24, 126, renderer.width - 48, 420),
            (25, 31, 43), (145, 118, 70),
        )
        if self.container_id is None:
            renderer.text("Bir konteyner seçilmedi.", 52, 154, MUTED)
            return

        try:
            actor_id, inventory_id = self._actor_context()
            lock = self.service.container_lock_state(self.container_id)
            try:
                view = self.service.open_container(
                    actor_id, inventory_id, self.container_id
                )
            except GameplayServiceError:
                renderer.text("Kilitli konteyner", 52, 154, GOLD, title=True)
                if lock is None:
                    renderer.text("Konteyner açılamıyor.", 52, 210, WARN)
                else:
                    status = "Sıkışmış" if lock.jammed else "Kırık" if lock.broken else "Kilitli"
                    renderer.text(f"Durum: {status}", 52, 214, WARN)
                    if lock.required_key_id:
                        renderer.text(
                            f"Anahtar: {lock.required_key_id} — Enter: anahtarla aç",
                            52, 252, TEXT_SOFT,
                        )
                    if lock.lockpick_profile_id:
                        renderer.text("Maymuncuk profili mevcut.", 52, 290, TEXT_SOFT)
                    if lock.force_profile_id:
                        renderer.text("Zorlama profili mevcut.", 52, 322, TEXT_SOFT)
                renderer.text(self.message, 52, 490, WARN)
                renderer.footer("Enter: anahtarı kullan   X: pencereyi kapat")
                return

            player_items = self._player_items(inventory_id)
            container_items = self._container_items(view)
            renderer.text(view.name, 52, 142, GOLD, title=True)
            renderer.text(
                f"Ağırlık {view.contents_weight_kg:.1f} kg"
                + (
                    f" / {view.max_contents_weight_kg:.1f} kg"
                    if view.max_contents_weight_kg is not None else " / sınırsız"
                ),
                52, 188, TEXT_SOFT,
            )
            renderer.text(
                f"Slot {view.contents_slots}"
                + (f" / {view.max_slots}" if view.max_slots is not None else " / sınırsız"),
                52, 216, TEXT_SOFT,
            )
            renderer.text(
                f"Hacim {view.contents_volume_liters:.1f} L"
                + (
                    f" / {view.max_contents_volume_liters:.1f} L"
                    if view.max_contents_volume_liters is not None else " / sınırsız"
                ),
                52, 244, TEXT_SOFT,
            )
            renderer.panel(renderer.pg.Rect(52, 282, 390, 205), (32, 40, 54))
            renderer.panel(renderer.pg.Rect(500, 282, 390, 205), (32, 40, 54))
            renderer.text("Konteyner", 68, 292, GOLD)
            renderer.text("Karakter çantası", 516, 292, GOLD)
            self._row_rects = []
            for side, entries, left in (
                ("container", container_items, 68),
                ("player", player_items, 516),
            ):
                for index, (item_id, amount) in enumerate(entries[:5]):
                    rect = renderer.pg.Rect(left, 326 + index * 30, 350, 26)
                    if side == self.active_side and index == self.selected_index:
                        renderer.panel(rect, (55, 75, 105), GOLD)
                    else:
                        renderer.panel(rect, (39, 49, 64))
                    item = self.service.item(item_id)
                    name = item.name if item is not None else item_id
                    renderer.text(f"{name}  x{amount}", rect.x + 8, rect.y + 4, TEXT_SOFT)
                    if side == self.active_side:
                        self._row_rects.append(rect)
            renderer.text(self.message, 52, 500, GOOD)
            renderer.footer("Sol/Sağ: taraf değiştir   Yukarı/Aşağı: seç   Enter: 1 adet taşı")
        except (KeyError, ValueError, RuntimeError, GameplayServiceError) as error:
            renderer.text(f"Konteyner görüntülenemedi: {error}", 52, 170, WARN)


__all__ = ["ContainerScreen"]
