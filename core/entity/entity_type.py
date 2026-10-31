class EntityType:
    """
    Oyundaki temel Entity türlerini tanımlar.
    """

    KARAKTER = "karakter"
    NPC = "npc"
    ESYA = "esya"
    HAYVAN = "hayvan"
    YAPI = "yapi"
    KAYNAK = "kaynak"
    ARAC = "arac"

    @classmethod
    def all(cls):
        """Tanımlı tüm Entity türlerini döndürür."""
        return [
            cls.KARAKTER,
            cls.NPC,
            cls.ESYA,
            cls.HAYVAN,
            cls.YAPI,
            cls.KAYNAK,
            cls.ARAC,
        ]

    @classmethod
    def is_valid(cls, entity_type):
        """Entity türünün geçerli olup olmadığını kontrol eder."""
        return entity_type in cls.all()