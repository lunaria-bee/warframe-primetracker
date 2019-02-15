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

class DbPopulatePopup (Popup):
    def start (self):
        self.http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        self.table = db.get_relic_drop_table(self.http)
        self.bar.max = len(self.table)
        # self.updater = Clock.schedule_interval(partial(DbPopulatePopup.update, self), 0.5)
        Thread(target=partial(DbPopulatePopup.populate, self)).start()

    def populate (self):
        for row in self.table:
            db.process_relic_drop_table_row(row, self.http)
            Clock.schedule_once(lambda _: self.update())
        db.calculate_required_part_quantities()
        self.dismiss()

    def update (self):
        self.bar.value += 1

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
