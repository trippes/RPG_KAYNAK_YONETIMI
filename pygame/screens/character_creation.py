from character import Attribute

from ..renderer import GOOD, GOLD, MUTED, TEXT_SOFT, WARN


class CharacterCreationScreen:
    """Interactive RPG character creation used by Eren's opening question."""

    ATTRIBUTES = (
        (Attribute.STRENGTH, "Güç", "Yakın dövüş ve taşıma kapasitesi"),
        (Attribute.DEXTERITY, "Çeviklik", "Hız, isabet ve savunma"),
        (Attribute.CONSTITUTION, "Dayanıklılık", "Can puanı ve direnç"),
        (Attribute.INTELLIGENCE, "Zeka", "Bilgi, üretim ve büyü"),
        (Attribute.WISDOM, "Bilgelik", "Algı ve irade"),
        (Attribute.CHARISMA, "Karizma", "İkna ve ilişkiler"),
    )
    BASE_SCORE = 10
    POINTS = 12
    MIN_SCORE = 8
    MAX_SCORE = 15

    def __init__(self, service):
        self.service = service
        self.focus = 0
        self.selected_attribute = 0
        self.name = ""
        self.age = ""
        self.message = "Eren seni dikkatle inceliyor. Önce kendini tanıt."
        self.scores = {attribute: self.BASE_SCORE for attribute, _label, _help in self.ATTRIBUTES}
        self.name_entry_active = True
        races, classes = self._factory_options()
        character = self._character()
        self.races = races
        self.classes = classes
        self.race_index = next(
            (index for index, item in enumerate(races)
             if character is not None and item.race_id == character.race.race_id),
            0,
        )
        self.class_index = next(
            (index for index, item in enumerate(classes)
             if character is not None and item.class_id == character.character_class.class_id),
            0,
        )

    def _character(self):
        return self.service.application.holder.current.characters.get("hero")

    def _factory_options(self):
        factory = self.service._character_factory
        if factory is None:
            return (), ()
        return tuple(factory.races.values()), tuple(factory.classes.values())

    def _remaining_points(self):
        return self.POINTS - sum(score - self.BASE_SCORE for score in self.scores.values())

    def _reset(self):
        self.__init__(self.service)

    def handle(self, state):
        self.name_entry_active = self.focus < 2
        if self.focus == 0:
            if state.pressed("backspace"):
                self.name = self.name[:-1]
            if state.text:
                self.name = (self.name + state.text)[:24]
        elif self.focus == 1:
            if state.pressed("backspace"):
                self.age = self.age[:-1]
            if state.text:
                self.age = "".join(char for char in self.age + state.text if char.isdigit())[:3]

        if state.pressed("back"):
            if getattr(self.service, "_creation_from_eren", False):
                self.message = "Eren'e cevap vermeden önce karakterini oluşturmalısın."
                return None
            return "world"

        if self.focus == 4:
            if state.pressed("up"):
                self.selected_attribute = (self.selected_attribute - 1) % len(self.ATTRIBUTES)
            if state.pressed("down"):
                self.selected_attribute = (self.selected_attribute + 1) % len(self.ATTRIBUTES)
            attribute = self.ATTRIBUTES[self.selected_attribute][0]
            if state.pressed("left") and self.scores[attribute] > self.MIN_SCORE:
                self.scores[attribute] -= 1
            if state.pressed("right") and self.scores[attribute] < self.MAX_SCORE and self._remaining_points() > 0:
                self.scores[attribute] += 1
            if state.pressed("confirm"):
                return self._finish()
            return None

        if self.focus == 2 and self.races:
            if state.pressed("left") or state.pressed("up"):
                self.race_index = (self.race_index - 1) % len(self.races)
            if state.pressed("right") or state.pressed("down"):
                self.race_index = (self.race_index + 1) % len(self.races)
        elif self.focus == 3 and self.classes:
            if state.pressed("left") or state.pressed("up"):
                self.class_index = (self.class_index - 1) % len(self.classes)
            if state.pressed("right") or state.pressed("down"):
                self.class_index = (self.class_index + 1) % len(self.classes)

        if state.pressed("up") and self.focus not in (2, 3):
            self.focus = (self.focus - 1) % 5
        if state.pressed("down") and self.focus not in (2, 3):
            self.focus = (self.focus + 1) % 5
        if state.pressed("left") and self.focus not in (2, 3):
            self.focus = (self.focus - 1) % 5
        if state.pressed("right") and self.focus not in (2, 3):
            self.focus = (self.focus + 1) % 5
        if state.pressed("confirm"):
            if self.focus < 4:
                self.focus += 1
            else:
                return self._finish()
        return None

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
            self.message = f"Dağıtılmamış {self._remaining_points()} puanın var."
            self.focus = 4
            return None
        try:
            self.service.application.customize_character(
                "hero", self.name, age, self.scores,
                race=self.races[self.race_index] if self.races else None,
                character_class=self.classes[self.class_index] if self.classes else None,
            )
        except (KeyError, TypeError, ValueError, RuntimeError) as error:
            self.message = str(error)
            return None
        from_eren = getattr(self.service, "_creation_from_eren", False)
        self.service._player_name_confirmed = True
        self.service._creation_from_eren = False
        self.message = f"{self.name}, Eldoria'ya hoş geldin."
        return "dialogue" if from_eren else "world"

    def render(self, renderer):
        renderer.frame("Karakter Oluştur")
        renderer.panel(renderer.pg.Rect(40, 100, renderer.width - 80, 430))
        renderer.text("Kendini tanıt", 70, 120, title=True)
        renderer.wrapped_text(
            "Klasik RPG başlangıcı: isim, yaş ve altı temel niteliğini belirle. "
            "Nitelik puanları oynayış tarzını şekillendirir.",
            70, 170, renderer.width - 140, TEXT_SOFT, max_lines=2,
        )
        character = self._character()
        race_name = character.race.name if character else "—"
        class_name = character.character_class.name if character else "—"
        selected_race = self.races[self.race_index] if self.races else None
        selected_class = self.classes[self.class_index] if self.classes else None
        race_name = selected_race.name if selected_race else "Seçenek yok"
        class_name = selected_class.name if selected_class else "Seçenek yok"
        fields = (
            f"İsim: {self.name or '...'}",
            f"Yaş: {self.age or '...'}",
            f"Irk: {race_name} ({self.race_index + 1}/{len(self.races)})",
            f"Sınıf: {class_name} ({self.class_index + 1}/{len(self.classes)})",
            f"Nitelikler  (kalan puan: {self._remaining_points()})",
        )
        for index, label in enumerate(fields):
            color = GOLD if self.focus == index else TEXT_SOFT
            renderer.text(("> " if self.focus == index else "  ") + label, 75, 235 + index * 34, color)

        if self.focus == 4:
            y = 235
            for index, (_attribute, label, help_text) in enumerate(self.ATTRIBUTES):
                color = GOOD if index == self.selected_attribute else TEXT_SOFT
                score = self.scores[_attribute]
                renderer.text(f"{label:<12} {score:>2}  {help_text}", 430, y, color)
                y += 34
        elif self.focus == 2 and selected_race:
            renderer.text(
                "  ".join(
                    f"{attribute.value[:3].upper()} {value:+d}"
                    for attribute, value in selected_race.attribute_modifiers.items()
                ) or "Irk modifiyeri yok",
                430, 305, TEXT_SOFT,
            )
            for index, ability in enumerate(selected_race.abilities):
                renderer.text(f"Yetenek: {ability.name}", 430, 335 + index * 24, GOOD)
        elif self.focus == 3 and selected_class:
            renderer.text(f"Temel HP: {selected_class.hit_points}", 430, 305, TEXT_SOFT)
            for index, (skill, rank) in enumerate(selected_class.skill_ranks.items()):
                renderer.text(f"Beceri: {skill} +{rank}", 430, 335 + index * 24, GOOD)
            for index, ability in enumerate(selected_class.abilities):
                renderer.text(f"Yetenek: {ability.name}", 430, 365 + index * 24, GOOD)
        renderer.text(self.message, 70, 495, WARN if self.message.startswith(("Yaş", "İsim", "Dağıt")) else MUTED)
        renderer.footer("Yaz: İsim/Yaş   ↑/↓: Alan veya nitelik   ←/→: Puan   Enter: İlerle/Onayla   Esc: Geri")
