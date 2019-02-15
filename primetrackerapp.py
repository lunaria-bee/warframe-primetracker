#!/usr/bin/env python3

import kivy, certifi, urllib3
import primedb as db

from threading import Thread
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup

class PrimeTrackerApp (App):
    pass

class ProgressPopup (Popup):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_phase_max = 0
        self.cumulative_max = 0
        self.current_phase_value = 0
        self.description_message = self.description.text

    def new_phase (self, phase_max, phase_percent, message=None):
        percent = self.bar.value_normalized
        self.bar.max = int((self.cumulative_max + phase_max) / (percent + phase_percent))
        self.bar.value = int(self.bar.max * percent)
        self.current_phase_max = phase_max
        self.cumulative_max += phase_max
        self.current_phase_value = 0
        self.update_description(message)

    def update_bar (self, steps=1, message=None):
        self.bar.value += steps
        self.current_phase_value += steps
        self.update_description(description)

    def update_description(self, message=None):
        if not message is None: self.description_message = message
        self.description.text = ("{} {(:.0f}/{:.0f})..."
                                 .format(self.description_message,
                                         self.current_phase_value,
                                         self.current_phase_max))

class DbPopulatePopup (Popup):
    def start (self):
        self.http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        self.table = db.get_relic_drop_table(self.http)
        self.bar.max = len(self.table)
        # self.updater = Clock.schedule_interval(partial(DbPopulatePopup.update, self), 0.5)
        self.execution = Thread(target=partial(DbPopulatePopup.populate, self)).start()

    def populate (self):
        for row in self.table:
            db.process_relic_drop_table_row(row, self.http)
            Clock.schedule_once(lambda _: self.update("Processing Relic drops"))
        for product in db.Item.select_all_products():
            db.calculate_product_requirement_quantities(product)
            Clock.schedule_once(lambda _: self.update("Processing build requirements"))
        self.dismiss()

    def update (self, description):
        self.bar.value += 1
        self.description.text = ("{} ({:.0f}/{:.0f})..."
                                 .format(description, self.bar.value, self.bar.max))

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
