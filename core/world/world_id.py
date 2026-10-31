class WorldIDGenerator:
    """
    World nesneleri için benzersiz ID üreten sınıf.
    """

    def __init__(self):
        self._counter = 0

    def generate(self):
        """Yeni ve benzersiz bir World ID üretir."""
        self._counter += 1
        return f"world_{self._counter:06d}"

    def reset(self):
        """ID sayacını sıfırlar."""
        self._counter = 0
