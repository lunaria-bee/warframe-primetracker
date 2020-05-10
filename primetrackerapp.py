#!/usr/bin/env python3

import primedb as db

from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from kivy.properties import *

from guilib.dbview import *
from guilib.input import *
from guilib.popup import *


class PrimeTrackerApp (App):
    def build (self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(TestingMenu())
        return root


class TestingButton (Button):
    '''A button ideal for testing new features'''
    def on_release (self):
        if not len(self.get_property_observers('on_release')):
            Logger.warning("UI Testing: {} Test not implemented!".format(self.text))
        super().on_release()


class TestingMenu (BoxLayout):
    # TODO TestingMenu should be restorable after a test

    def _test_product_view (self, product_name):
        self.clear_widgets()
        self.add_widget(ProductView(db.Item.get(name=product_name)))

    def _test_component_view (self, component_name):
        self.clear_widgets()
        self.add_widget(ComponentView(db.Item.get(name=component_name)))

    def _test_relic_view (self):
        self.clear_widgets()
        self.add_widget(RelicView(db.Relic.select()[0]))

    def _test_DbEntryListing_subclasses (self):
        # Create Dummy DB Entries #
        test_product = db.Item(name="Product Two Prime", owned=2)
        test_component = db.Item(name="Component Zero Prime", owned=0)
        test_relic_tier_low = db.RelicTier(name="TestLow", ordinal=5)
        test_relic_tier_high = db.RelicTier(name="TestHigh", ordinal=6)
        test_relic_low = db.Relic(tier=test_relic_tier_low,
                                  code="T5", vaulted=True)
        test_relic_high = db.Relic(tier=test_relic_tier_high,
                                   code="T6", vaulted=False)
        test_rarity_common = db.Rarity(name="Common", ordinal=-1)
        test_rarity_rare = db.Rarity(name="Rare", ordinal=1)
        test_build_requirement = db.BuildRequirement(needs=test_component,
                                                     builds=test_product,
                                                     need_count=2,
                                                     build_count=1)
        test_containment_low = db.Containment(inside=test_relic_low,
                                              contains=test_component,
                                              rarity=test_rarity_rare)
        test_containment_high = db.Containment(inside=test_relic_high,
                                               contains=test_component,
                                               rarity=test_rarity_common)

        # Run Tests #
        print(DbItemListing(test_product).ids.label.text)
        print("===")
        print(DbItemListing(test_component).ids.label.text)
        print("===")
        print("Attempt to generate error...")
        try:
            DbItemListing(db.ItemType())
            print("...failure! DbItemListing failed to reject incorrect type.")
        except TypeError as e:
            print(e)
            print("...success!")
        print("===")
        print(DbRelicListing(test_relic_low).ids.label.text)
        print("===")
        print(DbRelicListing(test_relic_high).ids.label.text)
        print("===")
        print("Attempt to generate error...")
        try:
            DbRelicListing(db.ItemType())
            print("...failure! DbRelicListing failed to reject incorrect type.")
        except TypeError as e:
            print(e)
            print("...success!")
        print("===")
        print(DbContainmentForRelicListing(test_containment_low).ids.label.text)
        print(DbContainmentForContentsListing(test_containment_low).ids.label.text)
        print("===")
        print(DbContainmentForRelicListing(test_containment_high).ids.label.text)
        print(DbContainmentForContentsListing(test_containment_high).ids.label.text)
        print("===")

def main ():
    db.open_()
    PrimeTrackerApp().run()
    db.close()

if __name__ == '__main__': main()
