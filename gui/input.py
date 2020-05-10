from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput

from kivy.properties import *


Builder.load_file('gui/input.kv')


class DynamicTextInput (TextInput):
    '''TextInput with additional features for interacting with other elements

    A DynamicTextInput is ideal for text that needs to modify or be modified by
    other elements of the App.

    PROPERTIES
    autohighlight: If True, the entire text field will be highlighted whn the
                   gains focus

    '''
    autohighlight = BooleanProperty(True)

    def __init__ (self, *args, **kwargs):
        self.register_event_type('on_text')
        self.register_event_type('on_focus')
        super().__init__(*args, **kwargs)
        self.bind(focus=self.focus_dispatch)
        self.bind(text=self.text_dispatch)

    def focus_dispatch (self, *args):
        self.dispatch('on_focus', self, self.focus)

    def on_focus (self, instance, value):
        '''Callback for when the input gains focus'''
        if value and self.autohighlight:
            Clock.schedule_once(lambda _: self.select_all())

    def text_dispatch (self, *args):
        self.dispatch('on_text', self, self.text)

    def on_text (self, *args):
        '''Callback for when the text changes'''
        pass


class SpinCounter (BoxLayout):
    '''Widget for entering integer values

    A SpinCounter consists of a small text input box, a pair of buttons for
    increasing and decreasing the number in the box, and a third "Ok" button to
    accept the value. The user may enter a number either by typing or by using
    the + and - to seek the desired value. Even when manually typed, only
    integers will be accepted as valid input.

    PROPERTIES
    default: default value for the input
    value: the current value of the input

    '''
    default = NumericProperty(0)
    value = BoundedNumericProperty(0, min=None, max=None)

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()

    def set_max (self, max_):
        '''Set the maximum valid input value'''
        self.property('value').set_max(self, max_)

    def set_min (self, min_):
        '''Set the minimum valid input value'''
        self.property('value').set_min(self, min_)

    def reset (self):
        '''Reset `value` to the default'''
        self.value = self.default

    def adjust (self, change):
        '''Modify the value of the input

        If the attempted change would place the value out of range, do nothing.

        PARAMETERS
        change: amount to increase or decrease the value by

        '''
        try:
            self.value += change
        except ValueError:
            pass

    def check_input (self):
        '''Check whether the current input is valid'''
        try:
            self.value = int(self.text_input.text)
            return True
        except ValueError:
            min_ = self.property('value').get_min(self)
            max_ = self.property('value').get_max(self)
            if not min_ is None and max_ is None:
                Logger.error("GUI: Value must be greater than {}".format(min_))
            elif min_ is None and not max_ is None:
                Logger.error("GUI: Value must be less than {}".format(max_))
            else:
                Logger.error("GUI: Value must be between {} and {}".format(max_, min_))
            return False

    def on_value (self, instance, value):
        '''Callback for when the input value changes'''
        self.text_input.text = str(self.value)
