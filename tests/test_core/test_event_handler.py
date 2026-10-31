import unittest

from core.events import Event
from core.event_handler import EventHandler


class TestEventHandler(unittest.TestCase):

    def test_handler_olusturma(self):
        def callback(event):
            pass

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        self.assertEqual(
            handler.event_type,
            "test"
        )

        self.assertIs(
            handler.callback,
            callback
        )

    def test_handler_olayi_isler(self):
        sonuc = []

        def callback(event):
            sonuc.append(event)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        event = Event(
            tur="test"
        )

        isledi = handler.handle(event)

        self.assertTrue(isledi)
        self.assertEqual(
            len(sonuc),
            1
        )

        self.assertIs(
            sonuc[0],
            event
        )

    def test_farkli_olay_islenmez(self):
        sonuc = []

        def callback(event):
            sonuc.append(event)

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        event = Event(
            tur="baska_olay"
        )

        isledi = handler.handle(event)

        self.assertFalse(isledi)
        self.assertEqual(
            len(sonuc),
            0
        )

    def test_gecersiz_event_type(self):
        def callback(event):
            pass

        with self.assertRaises(TypeError):
            EventHandler(
                event_type=123,
                callback=callback
            )

    def test_bos_event_type(self):
        def callback(event):
            pass

        with self.assertRaises(ValueError):
            EventHandler(
                event_type="   ",
                callback=callback
            )

    def test_gecersiz_callback(self):
        with self.assertRaises(TypeError):
            EventHandler(
                event_type="test",
                callback="gecersiz"
            )

    def test_gecersiz_event(self):
        def callback(event):
            pass

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        with self.assertRaises(TypeError):
            handler.handle("gecersiz")

    def test_repr(self):
        def callback(event):
            pass

        handler = EventHandler(
            event_type="test",
            callback=callback
        )

        sonuc = repr(handler)

        self.assertIn(
            "EventHandler",
            sonuc
        )

        self.assertIn(
            "test",
            sonuc
        )


if __name__ == "__main__":
    unittest.main()
