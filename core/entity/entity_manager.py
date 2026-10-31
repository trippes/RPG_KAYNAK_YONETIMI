from core.entity.entity import Entity


class EntityManager:
    """
    Oyundaki Entity nesnelerini merkezi olarak yöneten sınıf.
    """

    def __init__(self):
        self.entities = {}

    def add(self, entity):
        """
        Entity'yi yönetime ekler.
        """

        if not isinstance(entity, Entity):
            raise TypeError(
                "Yalnızca Entity nesneleri yöneticiye eklenebilir."
            )

        if entity.entity_id in self.entities:
            raise ValueError(
                f"Bu Entity ID zaten kayıtlı: {entity.entity_id}"
            )

        self.entities[entity.entity_id] = entity

    def remove(self, entity_id):
        """
        Entity'yi yönetimden çıkarır.
        """

        if entity_id not in self.entities:
            raise KeyError(
                f"Entity bulunamadı: {entity_id}"
            )

        del self.entities[entity_id]

    def get(self, entity_id):
        """
        ID üzerinden Entity döndürür.
        """

        return self.entities.get(entity_id)

    def exists(self, entity_id):
        """
        Entity ID'sinin kayıtlı olup olmadığını döndürür.
        """

        return entity_id in self.entities

    def get_all(self):
        """
        Yönetilen tüm Entity'lerin listesini döndürür.

        İç koleksiyonun kendisini dışarı vermez.
        """

        return list(self.entities.values())

    def count(self):
        """
        Yönetilen Entity sayısını döndürür.
        """

        return len(self.entities)

    def activate(self, entity_id):
        """
        Belirtilen Entity'yi aktif hale getirir.
        """

        entity = self.get(entity_id)

        if entity is None:
            raise KeyError(
                f"Entity bulunamadı: {entity_id}"
            )

        entity.activate()

    def deactivate(self, entity_id):
        """
        Belirtilen Entity'yi pasif hale getirir.
        """

        entity = self.get(entity_id)

        if entity is None:
            raise KeyError(
                f"Entity bulunamadı: {entity_id}"
            )

        entity.deactivate()

    def kill(self, entity_id):
        """
        Belirtilen Entity'yi öldürür.
        """

        entity = self.get(entity_id)

        if entity is None:
            raise KeyError(
                f"Entity bulunamadı: {entity_id}"
            )

        entity.kill()

    def revive(self, entity_id):
        """
        Belirtilen Entity'yi diriltir.
        """

        entity = self.get(entity_id)

        if entity is None:
            raise KeyError(
                f"Entity bulunamadı: {entity_id}"
            )

        entity.revive()

    def get_by_type(self, entity_type):
        """
        Belirli bir Entity türündeki tüm Entity'leri döndürür.
        """

        return [
            entity
            for entity in self.entities.values()
            if entity.entity_type == entity_type
        ]

    def get_by_status(self, status):
        """
        Belirli durumdaki tüm Entity'leri döndürür.
        """

        return [
            entity
            for entity in self.entities.values()
            if entity.state.get_status() == status
        ]

    def get_alive(self):
        """
        Canlı olan tüm Entity'leri döndürür.
        """

        return [
            entity
            for entity in self.entities.values()
            if entity.is_alive()
        ]

    def get_active(self):
        """
        Aktif olan tüm Entity'leri döndürür.
        """

        return [
            entity
            for entity in self.entities.values()
            if entity.is_active()
        ]

    def get_by_name(self, name):
        """
        Belirli ada sahip tüm Entity'leri döndürür.
        """

        return [
            entity
            for entity in self.entities.values()
            if entity.name == name
        ]