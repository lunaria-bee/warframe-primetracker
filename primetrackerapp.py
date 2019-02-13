#!/usr/bin/env python3

import kivy, certifi, urllib3
import primedb as db

from kivy.app import App
from kivy.uix.popup import Popup

class PrimeTrackerApp (App):
    pass

class DbPopulatePopup (Popup):
    def execute (self):
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        table = db.get_relic_drop_table(http)
        self.bar.max = len(table)
        for row in table:
            db.process_relic_drop_table_row(row, http)
            self.bar.value += 1
        db.calculate_required_part_quantities()
        self.dismiss()

    def update_bar (self):
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
