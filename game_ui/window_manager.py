"""Central management for the movable gameplay windows."""

from dataclasses import dataclass

from .input import InputState


@dataclass
class ManagedWindow:
    window_id: str
    screen: object
    bounds: object
    content_origin: tuple[int, int]
    title: str
    frame: bool = True
    close_offset: tuple[int, int] | None = None
    visible: bool = False
    dragging: bool = False
    drag_offset: tuple[int, int] = (0, 0)
    resizing: bool = False
    resize_edges: tuple[str, ...] = ()
    resize_origin: tuple[int, int] = (0, 0)
    resize_bounds: tuple[int, int, int, int] = (0, 0, 0, 0)


class WindowManager:
    """Own singleton gameplay windows, focus, z-order, and pointer capture."""

    TITLE_HEIGHT = 32
    CLOSE_SIZE = 24
    DRAG_THRESHOLD = 4
    RESIZE_BORDER = 8
    MIN_WIDTH = 420
    MIN_HEIGHT = 300

    def __init__(self, backend, width, height, on_result=None):
        self.pg = backend
        self.width = width
        self.height = height
        self.windows = {}
        self.z_order = []
        self.focused_id = None
        self._drag_origin = None
        self.on_result = on_result

    @property
    def open_ids(self):
        return tuple(
            window_id for window_id in self.z_order
            if self.windows[window_id].visible
        )

    def register(
        self, window_id, screen, bounds, *,
        content_origin=(24, 126), title=None, frame=True, close_offset=None,
    ):
        if window_id in self.windows:
            raise ValueError(f"Window already registered: {window_id}")
        self.windows[window_id] = ManagedWindow(
            window_id,
            screen,
            self.pg.Rect(bounds),
            content_origin,
            title or window_id,
            frame,
            close_offset,
        )

    def open(self, window_id):
        window = self._get(window_id)
        window.visible = True
        self.focus(window_id)
        return window

    def close(self, window_id):
        window = self._get(window_id)
        window.visible = False
        window.dragging = False
        if self.focused_id == window_id:
            self.focused_id = next(reversed(self.open_ids), None)

    def toggle(self, window_id):
        window = self._get(window_id)
        if window.visible:
            self.close(window_id)
        else:
            self.open(window_id)
        return window.visible

    def focus(self, window_id):
        window = self._get(window_id)
        if not window.visible:
            window.visible = True
        self.z_order = [item for item in self.z_order if item != window_id]
        self.z_order.append(window_id)
        self.focused_id = window_id

    def is_open(self, window_id):
        return self._get(window_id).visible

    def _get(self, window_id):
        try:
            return self.windows[window_id]
        except KeyError as error:
            raise KeyError(f"Unknown window: {window_id}") from error

    def _top_at(self, position):
        for window_id in reversed(self.z_order):
            window = self.windows[window_id]
            if window.visible and window.bounds.collidepoint(position):
                return window
        return None

    def _close_rect(self, window):
        if not window.frame and window.close_offset is not None:
            return self.pg.Rect(
                window.bounds.x + window.close_offset[0],
                window.bounds.y + window.close_offset[1],
                self.CLOSE_SIZE,
                self.CLOSE_SIZE,
            )
        return self.pg.Rect(
            window.bounds.right - self.CLOSE_SIZE - 4,
            window.bounds.y + 4,
            self.CLOSE_SIZE,
            self.CLOSE_SIZE,
        )

    def _title_rect(self, window):
        return self.pg.Rect(
            window.bounds.x,
            window.bounds.y,
            window.bounds.width,
            self.TITLE_HEIGHT if window.frame else 18,
        )

    def _content_destination(self, window):
        return (
            window.bounds.x,
            window.bounds.y + (self.TITLE_HEIGHT if window.frame else 0),
        )

    def _content_source_rect(self, window):
        return self.pg.Rect(
            window.content_origin[0],
            window.content_origin[1],
            window.bounds.width,
            max(0, window.bounds.height - (self.TITLE_HEIGHT if window.frame else 0)),
        )

    def _screen_position(self, window, position):
        destination_x, destination_y = self._content_destination(window)
        origin_x, origin_y = window.content_origin
        return (
            position[0] - destination_x + origin_x,
            position[1] - destination_y + origin_y,
        )

    def _clamp(self, window, x, y):
        return (
            max(0, min(x, self.width - window.bounds.width)),
            max(0, min(y, self.height - self.TITLE_HEIGHT)),
        )

    def _resize_edges_at(self, window, position):
        """Return the window edges close enough to the pointer to resize."""
        bounds = window.bounds
        x, y = position
        edges = []
        if x - bounds.x <= self.RESIZE_BORDER:
            edges.append("left")
        elif bounds.right - x <= self.RESIZE_BORDER:
            edges.append("right")
        if y - bounds.y <= self.RESIZE_BORDER:
            edges.append("top")
        elif bounds.bottom - y <= self.RESIZE_BORDER:
            edges.append("bottom")
        return tuple(edges)

    def _begin_resize(self, window, position, edges):
        window.resizing = True
        window.resize_edges = tuple(edges)
        window.resize_origin = position
        window.resize_bounds = (
            window.bounds.x, window.bounds.y,
            window.bounds.width, window.bounds.height,
        )
        window.dragging = False

    def _resize_window(self, window, position):
        origin_x, origin_y = window.resize_origin
        start_x, start_y, start_width, start_height = window.resize_bounds
        delta_x = position[0] - origin_x
        delta_y = position[1] - origin_y
        left = start_x
        top = start_y
        right = start_x + start_width
        bottom = start_y + start_height

        if "left" in window.resize_edges:
            left = max(0, min(start_x + delta_x, right - self.MIN_WIDTH))
        elif "right" in window.resize_edges:
            right = min(self.width, max(start_x + self.MIN_WIDTH, right + delta_x))
        if "top" in window.resize_edges:
            top = max(0, min(start_y + delta_y, bottom - self.MIN_HEIGHT))
        elif "bottom" in window.resize_edges:
            bottom = min(self.height, max(start_y + self.MIN_HEIGHT, bottom + delta_y))

        window.bounds.x = left
        window.bounds.y = top
        window.bounds.width = right - left
        window.bounds.height = bottom - top
        viewport = getattr(window.screen, "set_viewport", None)
        if viewport is not None:
            viewport(
                window.bounds.width,
                max(0, window.bounds.height - (self.TITLE_HEIGHT if window.frame else 0)),
            )

    def _dispatch(self, window, state):
        local_pos = None
        if state.mouse_pos is not None:
            local_pos = self._screen_position(window, state.mouse_pos)
        translated = InputState(
            actions=set(state.actions),
            text=state.text,
            quit_requested=state.quit_requested,
            mouse_pos=local_pos,
            mouse_clicked=state.mouse_clicked,
            mouse_right_clicked=state.mouse_right_clicked,
            mouse_button_down=state.mouse_button_down,
            mouse_button_up=state.mouse_button_up,
            mouse_motion=state.mouse_motion,
            mouse_wheel=state.mouse_wheel,
        )
        result = window.screen.handle(translated)
        if result is not None and self.on_result is not None:
            self.on_result(result, window.window_id)

    def handle_input(self, state):
        """Consume input destined for a window, returning whether it was consumed."""
        if "quest_log" in state.actions:
            state.actions.discard("quest_log")
            self.toggle("quest_log")
            return True

        if "dialogue_history" in state.actions:
            return False

        if "character" in state.actions:
            state.actions.discard("character")
            if self.is_open("character"):
                self.close("character")
            else:
                self.open("character")
            return True

        if "inventory" in state.actions:
            state.actions.discard("inventory")
            self.toggle("inventory")
            return True

        if "production" in state.actions:
            state.actions.discard("production")
            self.toggle("production")
            return True

        if "map" in state.actions:
            state.actions.discard("map")
            self.toggle("map")
            return True
        if self.focused_id is None and "character" in state.actions:
            self.open("character")
            state.actions.discard("character")
            return True

        if self.focused_id is not None and self.windows[self.focused_id].resizing:
            window = self.windows[self.focused_id]
            if state.mouse_button_up:
                window.resizing = False
                window.resize_edges = ()
            elif state.mouse_motion and state.mouse_pos is not None:
                self._resize_window(window, state.mouse_pos)
            state.mouse_clicked = False
            return True

        if self.focused_id is not None and self.windows[self.focused_id].dragging:
            window = self.windows[self.focused_id]
            if state.mouse_button_up:
                window.dragging = False
                self._drag_origin = None
            elif state.mouse_motion and state.mouse_pos is not None:
                x = state.mouse_pos[0] - window.drag_offset[0]
                y = state.mouse_pos[1] - window.drag_offset[1]
                window.bounds.topleft = self._clamp(window, x, y)
            state.mouse_clicked = False
            return True

        # Keep drag-release events routed to the window that owns the dragged item,
        # even when the pointer is released over another open window.
        if self.focused_id is not None:
            focused = self.windows[self.focused_id]
            if getattr(focused.screen, "pointer_capture", False) and (
                state.mouse_motion or state.mouse_button_up
            ):
                if state.mouse_button_up and state.mouse_pos is not None:
                    target = self._top_at(state.mouse_pos)
                    payload_getter = getattr(focused.screen, "dragged_item_payload", None)
                    cancel_drag = getattr(focused.screen, "cancel_drag", None)
                    payload = payload_getter() if payload_getter is not None else None
                    if (
                        target is not None
                        and target.window_id != focused.window_id
                        and payload is not None
                        and not self._title_rect(target).collidepoint(state.mouse_pos)
                        and not self._close_rect(target).collidepoint(state.mouse_pos)
                    ):
                        receiver = getattr(target.screen, "receive_external_item", None)
                        if receiver is not None:
                            receiver(payload["item_id"], payload["quantity"])
                            if cancel_drag is not None:
                                cancel_drag()
                            self.focus(target.window_id)
                            return True
                self._dispatch(focused, state)
                return True

        if state.mouse_pos is not None and state.mouse_wheel:
            window = self._top_at(state.mouse_pos)
            if window is not None:
                self.focus(window.window_id)
                self._dispatch(window, state)
                return True

        if state.mouse_pos is not None and (
            state.mouse_button_down or state.mouse_clicked
        ):
            window = self._top_at(state.mouse_pos)
            if window is not None:
                self.focus(window.window_id)
                if self._close_rect(window).collidepoint(state.mouse_pos):
                    self.close(window.window_id)
                else:
                    resize_edges = self._resize_edges_at(window, state.mouse_pos)
                    if resize_edges:
                        self._begin_resize(window, state.mouse_pos, resize_edges)
                    elif self._title_rect(window).collidepoint(state.mouse_pos):
                        window.dragging = True
                        window.drag_offset = (
                            state.mouse_pos[0] - window.bounds.x,
                            state.mouse_pos[1] - window.bounds.y,
                        )
                    else:
                        self._dispatch(window, state)
                state.mouse_clicked = False
                return True

        if self.focused_id is not None:
            window = self.windows[self.focused_id]
            pointer_capture = getattr(window.screen, "pointer_capture", False)
            inside = (
                state.mouse_pos is not None
                and window.bounds.collidepoint(state.mouse_pos)
            )
            if (
                state.mouse_motion
                or state.mouse_button_up
                or state.mouse_wheel
            ) and (
                inside or pointer_capture or (state.mouse_wheel and state.mouse_pos is None)
            ):
                self._dispatch(window, state)
                return True

        if self.focused_id is not None:
            window = self.windows[self.focused_id]
            if state.actions or state.text:
                self._dispatch(window, state)
                return True
        return False

    def render(self, renderer):
        original_surface = renderer.surface
        original_mouse_pos = renderer.mouse_pos
        for window_id in self.open_ids:
            window = self.windows[window_id]
            if window.frame:
                renderer.panel(window.bounds)
            if original_mouse_pos is not None:
                renderer.mouse_pos = self._screen_position(window, original_mouse_pos)
            source = self._render_content(renderer, window)
            if source is not None:
                renderer.surface.blit(
                    source,
                    self._content_destination(window),
                    self._content_source_rect(window),
                )
            renderer.surface = original_surface
            renderer.mouse_pos = original_mouse_pos
            if window.frame:
                renderer.text(window.title, window.bounds.x + 12, window.bounds.y + 6)
            close = self._close_rect(window)
            renderer.button(close, "X")
        renderer.mouse_pos = original_mouse_pos

    def _render_content(self, renderer, window):
        surface_type = getattr(self.pg, "Surface", type(renderer.surface))
        if surface_type is None:
            window.screen.render(renderer)
            return None
        try:
            source = surface_type((renderer.width, renderer.height))
        except TypeError:
            window.screen.render(renderer)
            return None
        old_surface = renderer.surface
        renderer.surface = source
        window.screen.render(renderer)
        renderer.surface = old_surface
        return source
