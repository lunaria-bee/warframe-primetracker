#!/usr/bin/env python3

import kivy, certifi, urllib3
import primedb as db

from threading import Thread
from functools import partial

from kivy.properties import *
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.logger import Logger

class PrimeTrackerApp (App):
    pass

class PhasedProgressBar (ProgressBar):
    # TOOD
    phase_percents = ListProperty()
    phase_maxes = ListProperty()

class ProgressLabel (Label):
    # TODO
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max = 100
        self.value = 0
        self.prefix = ""
        self.postfix = ""
        # self.show_percent = False # TODO

    def update (self, steps=1, prefix=None, postfix=None):
        if not prefix is None: self.prefix = prefix + " "
        if not postfix is None: self.postfix = " " + postfix
        self.text = "{}({}/{}){}".format(self.prefix,
                                           self.value, self.max,
                                           self.postfix))

class ProgressPopup (Popup):
    # TODO update to display phase info
    current_phase_max = NumericProperty(0)
    current_phase_percent = NumericProperty(0)
    current_phase_max = NumericProperty(0)
    _cumulative_max = NumericProperty(0)

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def new_phase (self, phase_max, phase_percent, prefix=None, postfix=None):
        percent = self.bar.value_normalized
        self.bar.max = int((self.cumulative_max + phase_max) / (percent + phase_percent))
        self.bar.value = int(self.bar.max * percent)
        self.current_phase_max = phase_max
        self.current_phase_percent = phase_percent
        self.cumulative_max += phase_max
        self.current_phase_value = 0
        # TODO update phase info

    def step (self, steps=1):
        self.bar.value += (steps / self.current_phase_max) * self.current_phase_percent * self.bar.max
        self.current_phase_value += steps
        # TODO update step info

class DbPopulatePopup (ProgressPopup):
    def start (self):
        self.execution = Thread(target=partial(DbPopulatePopup.populate, self)).start()

    def populate (self):
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        table = db.get_relic_drop_table(http)
        Clock.schedule_once(lambda _: self.new_phase(len(table), .9, "Processing Relic drops"))
        for row in table:
            db.process_relic_drop_table_row(row, http)
            Clock.schedule_once(lambda _: self.step())

        products = db.Item.select_all_products()
        Clock.schedule_once(lambda _: self.new_phase(len(products), .1,  "Processing build requirements"))
        for product in db.Item.select_all_products():
            db.calculate_product_requirement_quantities(product)
            Clock.schedule_once(lambda _: self.step())
        self.dismiss()

class InventoryInitPopup (Popup):
    def parts_init (self):
        self.parts = db.Item.select_all_products() + db.Item.select_all_components()
        self.next_part()

    def next_part (self):
        self.current_part = self.parts.pop(0)
        self.prime_prompt.text = "Do you have {}?".format(self.current_part.name)

def main ():
    PrimeTrackerApp().run()

if __name__ == '__main__': main()
