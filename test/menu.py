import test

from kivy.lang.builder import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


Builder.load_file('test/menu.kv')


class TestingButton(Button):
    '''A button ideal for testing new features.'''
    def on_release(self):
        if not len(self.get_property_observers('on_release')):
            Logger.warning("UI Testing: {} Test not implemented!".format(self.text))
        super().on_release()


class TestHeading(Label):
    pass


class TestingMenu(BoxLayout):
    def test(self, root):
        test.gui.test_relic_view(root)


class AutoScreenManagerTestingMenu(BoxLayout):
    pass
