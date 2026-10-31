from ..renderer import RESOURCE_NAMES, duration_label, resource_name, unit_label


class ProductionScreen:
    VISIBLE_RECIPES = 5

    RESOURCE_NAMES = RESOURCE_NAMES

    def __init__(self, service, inventory_id="player"):
        self.service = service
        self.inventory_id = inventory_id
        self.selected_index = 0
        self.message = ""

    @staticmethod
    def _resource_id(resource):
        return getattr(resource, "value", str(resource))

    @classmethod
    def _resource_name(cls, resource):
        return resource_name(resource)

    @staticmethod
    def _recipe_title(recipe):
        title = getattr(recipe, "name", None) or recipe.recipe_id
        return str(title).replace("_", " ").capitalize()

    def _get_recipes(self):
        bundle = self.service.application.holder.current
        return sorted(
            bundle.recipes.values(),
            key=lambda recipe: recipe.recipe_id,
        )

    def _get_facility(self, recipe):
        bundle = self.service.application.holder.current

        facilities = sorted(
            bundle.facilities.facilities(),
            key=lambda facility: facility.facility_id,
        )

        for facility in facilities:
            if not facility.active:
                continue

            if (
                recipe.facility_type is not None
                and recipe.facility_type != facility.facility_type
            ):
                continue

            if not set(recipe.required_capabilities).issubset(
                set(facility.capabilities)
            ):
                continue

            if (
                facility.capacity.reserved
                >= facility.capacity.capacity
            ):
                continue

            return facility

        return None

    # Real job states: planned -> running -> completed/cancelled/failed.
    # "planned" counts as active, otherwise a freshly started job (still
    # planned until the first tick) would let the recipe be started twice.
    ACTIVE_JOB_STATES = ("planned", "running")

    _frame_snapshot = None

    def _snapshot(self):
        """State snapshot built once per frame, not once per recipe row."""
        if self._frame_snapshot is not None:
            return self._frame_snapshot
        return self.service.state()

    def _active_jobs(self, recipe):
        return [
            job
            for job in self._snapshot().jobs
            if job.recipe_id == recipe.recipe_id
            and job.inventory_id == self.inventory_id
            and job.state in self.ACTIVE_JOB_STATES
        ]

    def _job_progress(self, job):
        """Return (elapsed_ticks, total_ticks) of a job."""
        total = max(1, job.end_tick - job.start_tick)
        elapsed = max(0, min(total, self._snapshot().simulation_tick - job.start_tick))
        return elapsed, total

    def _inventory_stocks(self):
        inventory = self.service.inventory(self.inventory_id)
        return {
            resource: (amount, unit)
            for resource, amount, unit in inventory.stocks
        }

    def _missing_inputs(self, recipe):
        stocks = self._inventory_stocks()
        missing = []

        for resource, quantity in recipe.inputs:
            resource_id = self._resource_id(resource)
            amount = stocks.get(resource_id, (0, quantity.unit.value))[0]

            if amount < quantity.value:
                missing.append(
                    f"{self._resource_name(resource)} "
                    f"(gerekli: {quantity.value}, mevcut: {amount})"
                )

        return missing

    def _can_start(self, recipe):
        if self._active_jobs(recipe):
            return False, "Bu tarif için üretim zaten devam ediyor."

        missing = self._missing_inputs(recipe)
        if missing:
            return False, "Eksik kaynak: " + ", ".join(missing)

        if self._get_facility(recipe) is None:
            return False, "Uygun ve boş bir tesis bulunamadı."

        return True, ""

    def _start_production(self, recipe):
        can_start, reason = self._can_start(recipe)

        if not can_start:
            self.message = reason
            return

        facility = self._get_facility(recipe)

        try:
            self.service.start_production(
                recipe.recipe_id,
                self.inventory_id,
                facility.facility_id,
            )
            self.message = (
                f"{self._recipe_title(recipe)} üretimi başlatıldı. "
                "Space ile zamanı ilerlet."
            )
        except (KeyError, ValueError, RuntimeError) as error:
            self.message = f"Üretim başarısız: {error}"

    def handle(self, state):
        self._frame_snapshot = None
        recipes = self._get_recipes()

        if state.pressed("back"):
            return "world"

        if not recipes:
            self.message = "Kullanılabilir tarif bulunamadı."
            return None

        self.selected_index = max(
            0,
            min(self.selected_index, len(recipes) - 1),
        )

        if state.pressed("up"):
            self.selected_index = (
                self.selected_index - 1
            ) % len(recipes)
            self.message = ""

        if state.pressed("down"):
            self.selected_index = (
                self.selected_index + 1
            ) % len(recipes)
            self.message = ""

        # Fareyle tarif satiri secimi.
        if state.mouse_clicked and state.mouse_pos is not None:
            mouse_x, mouse_y = state.mouse_pos

            list_x_min, list_x_max = 60, 330
            list_y_min = 190
            row_height = 38

            first_visible = max(
                0,
                min(
                    self.selected_index,
                    len(recipes) - self.VISIBLE_RECIPES,
                ),
            )

            if (
                list_x_min <= mouse_x <= list_x_max
                and list_y_min <= mouse_y
                < list_y_min + self.VISIBLE_RECIPES * row_height
            ):
                row = (mouse_y - list_y_min) // row_height
                clicked_index = first_visible + row

                if clicked_index < len(recipes):
                    self.selected_index = clicked_index
                    self.message = ""

            # Fareyle uretimi baslat.
            if 600 <= mouse_x <= 880 and 425 <= mouse_y <= 467:
                self._start_production(recipes[self.selected_index])

            # Fareyle dunyaya don.
            if 60 <= mouse_x <= 280 and 420 <= mouse_y <= 462:
                return "world"

        # Klavyeyle uretimi baslat.
        if state.pressed("confirm"):
            self._start_production(recipes[self.selected_index])

        return None

    def render(self, renderer):
        self._frame_snapshot = self.service.state()
        recipes = self._get_recipes()

        renderer.frame("Üretim")
        renderer.hud(self.service)

        renderer.panel(renderer.pg.Rect(50, 130, 290, 350))
        renderer.panel(renderer.pg.Rect(350, 130, 560, 350))
        renderer.quest_panel(self.service, renderer.pg.Rect(50, 500, 860, 110))

        renderer.text("Tarifler", 70, 150, title=True)

        if not recipes:
            renderer.text(
                "Tarif bulunamadı.",
                75, 205, (230, 130, 120),
            )
            renderer.footer("Esc: Dünyaya dön")
            return

        self.selected_index = max(
            0,
            min(self.selected_index, len(recipes) - 1),
        )

        first_visible = max(
            0,
            min(
                self.selected_index,
                len(recipes) - self.VISIBLE_RECIPES,
            ),
        )

        visible_recipes = recipes[
            first_visible:first_visible + self.VISIBLE_RECIPES
        ]

        for row, recipe in enumerate(visible_recipes):
            index = first_visible + row
            selected = index == self.selected_index
            rect = renderer.pg.Rect(
                62, 188 + row * 38, 266, 34
            )

            renderer.panel(
                rect,
                (55, 75, 105) if selected else (38, 49, 69),
                (245, 210, 120) if selected else (62, 78, 101),
            )

            startable, _why = self._can_start(recipe)
            busy = bool(self._active_jobs(recipe))
            dot = (110, 170, 230) if busy else (140, 220, 160) if startable else (230, 130, 120)
            renderer.pg.draw.circle(renderer.surface, dot, (rect.x + 14, rect.centery), 6)
            renderer.text(
                renderer.fit_text(self._recipe_title(recipe), rect.width - 40),
                rect.x + 28, rect.y + 8,
                (245, 220, 155) if selected else (220, 225, 235),
            )

        if len(recipes) > self.VISIBLE_RECIPES:
            renderer.text(
                f"{self.selected_index + 1}/{len(recipes)} tarif",
                75, 390, (155, 172, 196),
            )

        renderer.action_button(
            renderer.pg.Rect(60, 420, 220, 42),
            "ESC",
            "Dünyaya dön",
        )

        recipe = recipes[self.selected_index]
        renderer.text(
            renderer.fit_text(self._recipe_title(recipe), 520, title=True),
            375, 150,
            title=True,
        )

        renderer.text("Girdiler", 375, 205, (170, 195, 230))

        stocks = self._inventory_stocks()
        y = 235

        for resource, quantity in recipe.inputs:
            resource_id = self._resource_id(resource)
            available = stocks.get(
                resource_id, (0, quantity.unit.value)
            )[0]
            enough = available >= quantity.value

            renderer.resource_icon(378, y + 2, resource)
            renderer.text(
                f"{self._resource_name(resource)}: "
                f"{quantity.value} {unit_label(quantity.unit)} "
                f"(envanter: {available})",
                402, y,
                (140, 220, 160) if enough else (230, 130, 120),
            )
            y += 28

        renderer.text("Çıktılar", 375, y + 5, (170, 195, 230))
        y += 35

        for resource, quantity in recipe.outputs:
            renderer.resource_icon(378, y + 2, resource)
            renderer.text(
                f"{self._resource_name(resource)}: "
                f"{quantity.value} {unit_label(quantity.unit)}",
                402, y,
            )
            y += 28

        renderer.text(
            f"Süre: {duration_label(recipe.processing_time.value)}",
            375, min(y + 5, 385),
        )

        facility = self._get_facility(recipe)
        facility_text = (
            f"Tesis: {facility.facility_id}"
            if facility is not None
            else "Uygun ve boş tesis yok"
        )
        renderer.text(
            facility_text,
            375, 395,
            (140, 220, 160) if facility else (230, 130, 120),
        )

        can_start, reason = self._can_start(recipe)

        running = self._active_jobs(recipe)
        if running:
            elapsed, total = self._job_progress(running[0])
            renderer.text(
                f"Üretiliyor: {duration_label(elapsed)} / {duration_label(total)}", 375, 421, (130, 180, 235),
            )
            renderer.bar(
                renderer.pg.Rect(375, 443, 200, 14), elapsed / total, (110, 170, 230),
            )

        renderer.action_button(
            renderer.pg.Rect(600, 425, 280, 42),
            "ENTER",
            "Üretimi başlat",
            enabled=can_start,
            selected=True,
        )

        if self.message:
            renderer.text(
                renderer.fit_text(self.message, 540),
                355, 485,
                (230, 190, 110),
            )
        elif not can_start:
            renderer.text(
                renderer.fit_text(reason, 540),
                355, 485,
                (230, 130, 120),
            )

        renderer.footer(
            "Tarife tıkla: Seç   Enter / Buton: Üret   Esc: Dön"
        )
