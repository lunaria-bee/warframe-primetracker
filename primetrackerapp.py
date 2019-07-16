#!/usr/bin/env python3

import kivy, certifi, urllib3
import primedb as db

from threading import Thread
from functools import partial

from kivy.properties import *
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.logger import Logger

class PrimeTrackerApp (App):
    def build (self):
        return TestingMenu()

class DynamicTextInput (TextInput):
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
        if value and self.autohighlight:
            Clock.schedule_once(lambda _: self.select_all())

    def text_dispatch (self, *args):
        self.dispatch('on_text', self, self.text)

    def on_text (self, *args):
        pass

class TestingButton (Button):
    def on_release (self):
        if not len(self.get_property_observers('on_release')):
            Logger.warning("UI Testing: {} not implemented!".format(self.text))
        super().on_release()

class SpinCounter (BoxLayout):
    default = NumericProperty(0)
    value = BoundedNumericProperty(0, min=None, max=None)

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()

    def set_max (self, max_):
        self.property('value').set_max(self, max_)

    def set_min (self, min_):
        self.property('value').set_min(self, min_)

    def reset (self):
        self.value = self.default

    def adjust (self, change):
        try:
            self.value += change
        except ValueError:
            pass

    def check_input (self):
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
        self.text_input.text = str(self.value)

# TODO finished phased progress bars
class ProgressPopup (Popup):
    # TODO update to display phase info
    phase_count = NumericProperty()
    current_phase = NumericProperty()
    step_prefix = StringProperty()
    step_postfix = StringProperty()

    def new_phase (self, phase_steps, phase_info,
                   step_prefix="", step_postfix=""):
        self.bar.max = phase_steps
        self.bar.value = 0
        self.current_phase += 1
        self.phase_info.text = ("{} ({} / {})"
                                .format(phase_info, self.current_phase, self.phase_count))
        self.step_prefix = step_prefix
        self.step_postfix = step_postfix

    def step (self, step_info="", steps=1):
        self.bar.value += 1
        self.step_info.text = ("{} {} {} ({:.0%})"
                               .format(self.step_prefix, step_info, self.step_postfix,
                                       self.bar.value / self.bar.max))

class DbPopulatePopup (ProgressPopup):
    def start (self):
        self.phase_count = 2
        self.execution = Thread(target=partial(DbPopulatePopup.populate, self)).start()

    def populate (self):
        db.population_setup()
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        table = db.get_relic_drop_table(http)
        Clock.schedule_once(lambda _: self.new_phase(len(table),"Processing Relic drops"))
        for row in table:
            db.process_relic_drop_table_row(row, http)
            Clock.schedule_once(lambda _: self.step())

        products = db.Item.select_all_products()
        Clock.schedule_once(lambda _: self.new_phase(len(products), "Processing build requirements"))
        for product in db.Item.select_all_products():
            db.calculate_product_requirement_quantities(product)
            Clock.schedule_once(lambda _: self.step())
        db.population_teardown()
        self.dismiss()

class InventoryInitPopup (Popup):
    def parts_init (self):
        self.spin_counter.text_input.text_validate_unfocus = False
        self.spin_counter.text_input.bind(on_text_validate=self.process_next)
        self.spin_counter.set_min(0)
        self.parts = db.Item.select_all_products() + db.Item.select_all_components()
        self.next_part()

    def process_next(self, instance):
        if self.spin_counter.check_input():
            self.next_part()
            self.spin_counter.reset()
        self.spin_counter.focus = True

    def next_part (self):
        self.current_part = self.parts.pop(0)
        self.prime_prompt.text = "Enter number of {} in inventory:".format(self.current_part.name)

class TestingMenu (BoxLayout):
    pass

def main ():
    PrimeTrackerApp().run()

if __name__ == '__main__': main()
