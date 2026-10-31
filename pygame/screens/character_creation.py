class CharacterCreationScreen:
    def __init__(self, service):
        self.service = service
        self.message = "N karakter oluşturma ekranını açar."

    def handle(self, state):
        if state.pressed("confirm"):
            factory = self.service._character_factory
            if factory is None:
                self.message = "Karakter factory tanımlı değil."
            else:
                try:
                    index = len(self.service.application.holder.current.characters) + 1
                    race_id = next(iter(factory.races))
                    class_id = next(iter(factory.classes))
                    self.service.application.karakter_olustur(
                        factory, f"hero_{index}", f"Kahraman {index}", race_id, class_id
                    )
                    self.message = "Karakter oluşturuldu ve actor bağlandı."
                except (KeyError, ValueError, RuntimeError) as error:
                    self.message = str(error)
        if state.pressed("back") or state.pressed("world"):
            return "world"
        return None

    def render(self, renderer):
        renderer.frame("Karakter Oluştur")
        renderer.panel(renderer.pg.Rect(70, 110, 820, 390))
        renderer.text("Varsayılan insan savaşçı", 100, 180, title=True)
        renderer.text(self.message, 100, 240)
        renderer.text("[Enter] Oluştur   [Esc] Dünya", 70, 550, (155, 172, 196))
