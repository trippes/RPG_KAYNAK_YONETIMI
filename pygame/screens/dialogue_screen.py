
class DialogueScreen:
    def __init__(self, service):
        self.service = service
        self.target_npc_id = None
        self.reason_choices = (
            "Yeni yerler görmek için yollara düştüm.",
            "Kendime bir iş ve yeni bir hayat arıyorum.",
            "Yolum buraya düştü. Biraz dinlenmek istiyorum.",
        )

        self.reason_responses = {
            0: (
                "Demek yeni yerler görmek istiyorsun. "
                "Bu topraklarda keşfedilecek çok şey var."
            ),
            1: (
                "Yeni bir hayat arıyorsun demek. "
                "Belki köyümüzde sana uygun bir iş bulunabilir."
            ),
            2: (
                "Uzun bir yolculuktan sonra dinlenmek iyi gelir. "
                "Köyümüzde biraz soluklanabilirsin."
            ),
        }
        self._reset_dialogue()

    def _reset_dialogue(self):
        """Prepare a fresh conversation when the screen is opened again."""
        self.target_npc_id = None
        self.node = None
        self.message = "Konuşmak istediğin NPC'nin üzerine gelip Enter'a bas."
        self.context = None
        self.selected = 0

        self.name_entry_active = False
        self.character_name = ""
        self.intro_complete = False
        self.custom_text = None

        self.opening_stage = "start"
        self.selected_reason = None

    def set_target_npc(self, npc_id):
        self.target_npc_id = npc_id
        bundle = self.service.application.holder.current
        npc = bundle.social.npcs.get(npc_id) if npc_id else None
        if npc is not None:
            self.message = f"{npc.name} ile konuşmak için Enter tuşuna bas."

    def _close_dialogue(self):
        self._reset_dialogue()
        return "local_map"

    def _visible_choices(self):
        """Only show Hilmi actions that match the current quest state."""
        if self.node is None:
            return ()
        choices = tuple(self.node.choices)
        if self.context is not None:
            actor_id, npc_id, dialogue_id = self.context
            dialogue = self.service.application.holder.current.social.dialogues.get(dialogue_id)
            if dialogue is not None:
                choices = dialogue.available_choices(
                    self.node.node_id,
                    self.service._dialogue_context(actor_id, npc_id),
                )
        if self.context is None or self.context[1] != "village_carpenter":
            return choices
        quest = getattr(self.service, "carpenter_quest", None)
        inn_quest = getattr(self.service, "inn_quest", None)
        state = getattr(getattr(quest, "state", None), "value", None)
        inn_state = getattr(getattr(inn_quest, "state", None), "value", None)
        inventory = self.service.inventory("player")
        wood_amount = next(
            (amount for resource, amount, _unit in inventory.stocks if str(resource) == "wood"),
            0,
        )
        visible = []
        for choice in choices:
            if choice.choice_id == "accept_carpenter_quest" and state != "available":
                continue
            if choice.choice_id == "decline_carpenter_quest" and state != "available":
                continue
            if choice.choice_id == "deliver_carpenter_wood":
                collect = next(
                    (
                        item for item in quest.objectives
                        if item.objective_id == "collect_wood"
                    ),
                    None,
                ) if quest is not None else None
                if state != "active" or collect is None or not collect.completed or wood_amount < 3:
                    continue
            if choice.choice_id == "accept_inn_quest" and (
                state != "completed" or inn_state != "available"
            ):
                continue
            if choice.choice_id == "deliver_inn_supplies":
                objectives = {
                    item.objective_id: item
                    for item in inn_quest.objectives
                } if inn_quest is not None else {}
                bread_amount = next(
                    (amount for resource, amount, _unit in inventory.stocks if str(resource) == "bread"),
                    0,
                )
                water_amount = next(
                    (amount for resource, amount, _unit in inventory.stocks if str(resource) == "water"),
                    0,
                )
                if (
                    inn_state != "active"
                    or bread_amount < 1
                    or water_amount < 1
                    or not objectives.get("buy_bread", ()).completed
                    or not objectives.get("buy_water", ()).completed
                ):
                    continue
            visible.append(choice)
        return tuple(visible)

    def _open_default(self):
        bundle = self.service.application.holder.current
        actors = bundle.actors.actors()
        npcs = bundle.social.npcs.all()
        dialogues = tuple(sorted(bundle.social.dialogues))

        if not actors or not npcs or not dialogues:
            self.message = "Konuşulacak NPC veya diyalog bulunamadı."
            return

        try:
            actor = next(
                (item for item in actors if item.actor_id == "hero"),
                actors[0],
            )
            npc = next(
                (item for item in npcs if item.npc_id == self.target_npc_id),
                next(
                    (item for item in npcs if item.npc_id == "warden_lyra"),
                    npcs[0],
                ),
            )

            dialogue_id = next(
                (
                    dialogue_id
                    for dialogue_id in dialogues
                    if npc.npc_id in bundle.social.dialogues[dialogue_id].speakers
                ),
                dialogues[0],
            )

            self.context = (
                actor.actor_id,
                npc.npc_id,
                dialogue_id,
            )

            self.node = self.service.talk_to_npc(*self.context)
            self.selected = 0

            if (
                self.node is not None
                and dialogue_id == "warden_intro"
                and self.node.node_id == "start"
                and not getattr(
                    self.service,
                    "_player_name_confirmed",
                    False,
                )
            ):
                self.opening_stage = "name"
                self.name_entry_active = True
                self.character_name = ""
                self.message = (
                    "Bir dakika! Seni bu köyde daha önce görmedim. "
                    "Adın ne yabancı?"
                )
            else:
                self.opening_stage = "dialogue"
                npc_name = npc.name
                self.message = f"{npc_name} ile konuşuyorsun."

        except (KeyError, ValueError, RuntimeError) as error:
            self.message = str(error)

    def handle(self, state):
        if self.opening_stage == "start":
            if state.pressed("confirm") and self.node is None:
                self._open_default()
            elif state.pressed("back") or state.pressed("world"):
                return self._close_dialogue()
            return None

        if self.name_entry_active:
            if state.pressed("back"):
                self.message = (
                    "Köye girmek için önce adını söylemelisin."
                )
                return None

            if state.pressed("backspace"):
                self.character_name = self.character_name[:-1]

            if state.text:
                remaining = 40 - len(self.character_name)
                if remaining > 0:
                    self.character_name += state.text[:remaining]

            if state.pressed("confirm"):
                name = self.character_name.strip()

                if not name:
                    self.message = "Lütfen bir isim yaz."
                elif len(name) > 40:
                    self.message = "İsim en fazla 40 karakter olabilir."
                else:
                    bundle = self.service.application.holder.current
                    character = bundle.characters.get("hero")

                    if character is None:
                        self.message = "Oyuncu karakteri bulunamadı."
                    else:
                        character.name = name
                        self.service._player_name_confirmed = True
                        self.character_name = name
                        self.name_entry_active = False
                        self.custom_text = (
                            f"Memnun oldum, {name}. "
                            "Peki, buralara hangi amaçla geldin?"
                        )
                        self.opening_stage = "ask_reason"

            return None

        if self.opening_stage == "ask_reason":
            if state.pressed("up"):
                self.selected = (
                    self.selected - 1
                ) % len(self.reason_choices)

            if state.pressed("down"):
                self.selected = (
                    self.selected + 1
                ) % len(self.reason_choices)

            if state.pressed("confirm"):
                self.selected_reason = self.selected
                self.custom_text = self.reason_responses[
                    self.selected_reason
                ]
                self.opening_stage = "response"

            return None

        if self.opening_stage == "response":
            if state.pressed("confirm"):
                if self.context is not None and self.context[1] == "village_carpenter":
                    self.opening_stage = "welcome"
                    return None
                self.custom_text = (
                    f"Anladım, {self.character_name}. "
                    "Köyümüze hoş geldin. İçeri girebilirsin."
                )
                self.opening_stage = "welcome"

            return None

        if self.opening_stage == "welcome":
            if state.pressed("confirm"):
                self.intro_complete = True
                self.opening_stage = "complete"
                return self._close_dialogue()
            return None

        if self.intro_complete:
            if (
                state.pressed("confirm")
                or state.pressed("back")
                or state.pressed("world")
            ):
                return self._close_dialogue()
            return None

        visible_choices = self._visible_choices()
        if self.node is not None and visible_choices:
            self.selected %= len(visible_choices)
            if state.pressed("up"):
                self.selected = (
                    self.selected - 1
                ) % len(visible_choices)

            if state.pressed("down"):
                self.selected = (
                    self.selected + 1
                ) % len(visible_choices)

            if state.pressed("confirm"):
                actor_id, npc_id, dialogue_id = self.context

                try:
                    choice = visible_choices[self.selected]
                    if (
                        npc_id == "village_carpenter"
                        and choice.choice_id == "accept_carpenter_quest"
                    ):
                        self.service.accept_carpenter_quest(actor_id, "player")
                        self.custom_text = (
                            "Harika. Kuzey Ormanı'ndaki ağaçlardan 3 odun "
                            "topla ve bana geri getir."
                        )
                        self.opening_stage = "response"
                        self.message = "Marangoz Hilmi görevi verdi."
                        return None
                    if (
                        npc_id == "village_carpenter"
                        and choice.choice_id == "deliver_carpenter_wood"
                    ):
                        self.service.deliver_carpenter_wood(
                            actor_id, npc_id, "player",
                        )
                        self.custom_text = (
                            "İşte böyle! Bu odunlarla köyün çatısını "
                            "onarabileceğim. Ödülün burada."
                        )
                        self.opening_stage = "welcome"
                        self.message = "Odunlar Hilmi'ye teslim edildi."
                        return None
                    if (
                        npc_id == "village_carpenter"
                        and choice.choice_id == "accept_inn_quest"
                    ):
                        self.service.accept_inn_quest(actor_id, "player")
                        self.custom_text = (
                            "Köy hanına gidip bir ekmek ve bir su al. "
                            "Bunları bana getirirsen işimiz tamamlanır."
                        )
                        self.opening_stage = "response"
                        self.message = "Hilmi ikinci görevi verdi."
                        return None
                    if (
                        npc_id == "village_carpenter"
                        and choice.choice_id == "deliver_inn_supplies"
                    ):
                        self.service.deliver_inn_supplies(
                            actor_id, npc_id, "player",
                        )
                        self.custom_text = (
                            "Harika iş çıkardın. Ekmek ve su tam zamanında "
                            "geldi. Marangoz atölyesi sana minnettar."
                        )
                        self.opening_stage = "welcome"
                        self.message = "İkinci görev tamamlandı, ödülünü aldın."
                        return None
                    self.node = self.service.choose_dialogue(
                        actor_id,
                        npc_id,
                        dialogue_id,
                        self.node.node_id,
                        choice.choice_id,
                    )
                    self.selected = 0
                    if self.node is None:
                        if choice.action == "open_market":
                            self.message = "Han ürünleri açıldı."
                            return "market"
                        return self._close_dialogue()
                    self.message = "Seçim yapıldı."

                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = str(error)

        elif self.node is not None and self.node.choices and state.pressed("confirm"):
            self.message = (
                "Hilmi'nin şu anda vereceği veya teslim alacağı başka bir iş yok."
            )
            return self._close_dialogue()

        elif (
            self.node is not None
            and not self.node.choices
            and state.pressed("confirm")
        ):
            return self._close_dialogue()

        elif state.pressed("back") or state.pressed("world"):
            return self._close_dialogue()

        return None

    def render(self, renderer):
        renderer.frame("Diyalog")
        renderer.hud(self.service)
        panel = renderer.pg.Rect(
            70, 130, renderer.width - 140, min(350, renderer.height - 220),
        )
        renderer.panel(panel)
        text_width = panel.width - 60

        npc_name = "Eren"
        if self.context is not None:
            npc = self.service.application.holder.current.social.npcs.get(
                self.context[1],
            )
            if npc is not None:
                npc_name = npc.name

        if self.opening_stage == "name":
            renderer.text(npc_name, 100, 170, title=True)
            renderer.wrapped_text(
                "Bir dakika! Seni bu köyde daha önce görmedim. "
                "Adın ne yabancı?",
                100,
                225,
                text_width,
            )

        elif self.opening_stage == "ask_reason":
            renderer.text(npc_name, 100, 170, title=True)
            renderer.wrapped_text(
                self.custom_text or "",
                100,
                205,
                text_width,
            )

            for index, choice in enumerate(self.reason_choices):
                marker = "=> " if index == self.selected else "   "
                color = (
                    (220, 225, 235)
                    if index == self.selected
                    else (170, 185, 205)
                )
                renderer.text(
                    f"{marker}{choice}",
                    120,
                    290 + index * 36,
                    color,
                )

        elif self.opening_stage in ("response", "welcome"):
            renderer.text(npc_name, 100, 170, title=True)
            renderer.wrapped_text(
                self.custom_text or "",
                100,
                225,
                text_width,
            )
            renderer.text(
                "Enter: Devam et",
                100,
                330,
                (170, 185, 205),
            )

        elif self.intro_complete:
            renderer.text(npc_name, 100, 170, title=True)
            renderer.wrapped_text(
                self.custom_text or "",
                100,
                225,
                text_width,
            )

        elif self.node is None:
            renderer.wrapped_text(
                self.message,
                100,
                190,
                text_width,
            )

        else:
            renderer.text(npc_name, 100, 170, title=True)
            renderer.wrapped_text(
                self.node.text,
                100,
                225,
                text_width,
            )

            for index, choice in enumerate(self._visible_choices()):
                marker = "=> " if index == self.selected else "   "
                color = (
                    (220, 225, 235)
                    if index == self.selected
                    else (170, 185, 205)
                )
                renderer.text(
                    renderer.fit_text(f"{marker}{choice.text}", text_width - 40),
                    120,
                    310 + index * 36,
                    color,
                )

        if self.name_entry_active:
            entry_rect = renderer.pg.Rect(
                panel.x + 30, min(390, panel.bottom - 120), text_width, 120,
            )
            renderer.panel(entry_rect)
            renderer.text("Adın nedir?", entry_rect.x + 20, entry_rect.y + 10, title=True)
            renderer.text(
                self.character_name + "|",
                entry_rect.x + 20,
                entry_rect.y + 58,
                max_width=entry_rect.width - 40,
            )
            renderer.text(
                "Enter: Onayla   Esc: İsim girmeden devam edemezsin",
                entry_rect.x + 20,
                entry_rect.y + 88,
                max_width=entry_rect.width - 40,
            )

        if self.opening_stage == "name":
            renderer.footer(
                "Yaz: İsim   Backspace: Sil   Enter: Onayla"
            )
        elif self.opening_stage == "ask_reason":
            renderer.footer(
                "Yukarı/Aşağı: Cevap seç   Enter: Onayla"
            )
        elif self.opening_stage in ("response", "welcome"):
            renderer.footer("Enter: Devam et")
        elif self.intro_complete:
            renderer.footer("Enter: Köye gir")
        else:
            renderer.footer(
                "Enter: Konuş/Seç   Yukarı/Aşağı: Seçim   Esc: Dünya"
            )
