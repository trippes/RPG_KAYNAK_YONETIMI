import math


class Position:
    """
    Entity'nin dünya üzerindeki konumunu temsil eder.
    """

    def __init__(self, x=0, y=0):
        self._validate_coordinate(x, "x")
        self._validate_coordinate(y, "y")

        self.x = x
        self.y = y

    @staticmethod
    def _validate_coordinate(value, name):
        """
        Koordinat değerinin geçerli olup olmadığını kontrol eder.
        """

        if isinstance(value, bool) or not isinstance(
            value,
            (int, float)
        ):
            raise TypeError(
                f"{name} koordinatı int veya float olmalıdır."
            )

    @staticmethod
    def _validate_movement(value, name):
        """
        Hareket değerinin geçerli olup olmadığını kontrol eder.
        """

        if isinstance(value, bool) or not isinstance(
            value,
            (int, float)
        ):
            raise TypeError(
                f"{name} hareket değeri int veya float olmalıdır."
            )

    def set_position(self, x, y):
        """
        Entity'nin konumunu doğrudan değiştirir.
        """

        self._validate_coordinate(x, "x")
        self._validate_coordinate(y, "y")

        self.x = x
        self.y = y

    def get_position(self):
        """
        Mevcut konumu tuple olarak döndürür.
        """

        return (self.x, self.y)

    def move(self, dx=0, dy=0):
        """
        Entity'yi verilen miktarda hareket ettirir.
        """

        self._validate_movement(dx, "dx")
        self._validate_movement(dy, "dy")

        self.x += dx
        self.y += dy

    def distance_to(self, other):
        """
        Başka bir Position nesnesine olan Öklid mesafesini döndürür.
        """

        if not isinstance(other, Position):
            raise TypeError(
                "Mesafe hesaplamak için Position nesnesi gereklidir."
            )

        return math.hypot(
            self.x - other.x,
            self.y - other.y
        )

    def same_as(self, other):
        """
        Başka bir Position nesnesiyle aynı konumda olup olmadığını döndürür.
        """

        if not isinstance(other, Position):
            return False

        return (
            self.x == other.x
            and self.y == other.y
        )

    def copy(self):
        """
        Position nesnesinin bağımsız bir kopyasını döndürür.
        """

        return Position(
            self.x,
            self.y
        )

    def to_dict(self):
        """
        Konumu sözlük olarak döndürür.
        """

        return {
            "x": self.x,
            "y": self.y,
        }