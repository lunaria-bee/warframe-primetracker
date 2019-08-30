#!/usr/bin/env python3

import kivy, certifi, urllib3
import primedb as db

from threading import Thread
from functools import partial

from kivy.properties import *
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.logger import Logger

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

class ProgressPopup (Popup):
    '''Popup window to provide information about multi-step tasks

    This window will show a heading about the task, a progress bar, and
    additional information about the current step of the task.

    If this task is broken into multiple subtasks, hereafter called "phases,"
    the progress bar can show which phase of the task is currently being
    comleted, independently of other phases.

    PROPERTIES
    phase_count: the total number of phases in the task
    current_phase: which of the phases is currently being completed
    step_prefix: text at the beginning of the information for each step
    step_postfix: text at the end of the information for each step

    '''
    phase_count = NumericProperty()
    current_phase = NumericProperty()
    step_prefix = StringProperty()
    step_postfix = StringProperty()

    def new_phase (self, phase_steps, phase_info,
                   step_prefix="", step_postfix=""):
        '''Start a new phase of the task

        Even for single-phase tasks, this method must be used to initiate the
        first (and only) phase.

        Must be called asynchronously (e.g. via a Clock) for the popup to update
        correctly.

        PARAMETERS
        phase_steps: the number of steps in this phase
        phase_info: heading with information about what the task is doing
        step_prefix: updates the step_prefix property
        step_postfix: updates the step_postfix property

        '''
        self.bar.max = phase_steps
        self.bar.value = 0
        self.current_phase += 1
        self.phase_info.text = ("{} ({} / {})"
                                .format(phase_info, self.current_phase, self.phase_count))
        self.step_prefix = step_prefix
        self.step_postfix = step_postfix

    def step (self, step_info="", steps=1):
        '''Indicate that some number of task steps have been completed

        Must be called asynchronously (e.g. via Clock) for the popup to update
        correctly.

        PARAMETERS
        step_info: information about this particular step
        steps: the number of steps that have been completed since the last update

        '''
        self.bar.value += 1
        self.step_info.text = ("{} {} {} ({:.0%})"
                               .format(self.step_prefix, step_info, self.step_postfix,
                                       self.bar.value / self.bar.max))

class DbPopulatePopup (ProgressPopup):
    '''Populates the Prime database'''
    def start (self):
        '''Initialize database population

        Called automatically when the popup opens.

        '''
        self.phase_count = 2
        self.execution = Thread(target=partial(DbPopulatePopup.populate, self)).start()

    def populate (self):
        # Initial Setup #
        db.population_setup()
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        table = db.get_relic_drop_table(http)

        # Process Table of Relic Drops and Build DB Accordingly #
        Clock.schedule_once(lambda _: self.new_phase(len(table),"Processing Relic drops"))
        for row in table:
            db.process_relic_drop_table_row(row, http)
            Clock.schedule_once(lambda _: self.step())

        # Determine Build Requirements for Each Product #
        products = db.Item.select_all_products()
        Clock.schedule_once(lambda _: self.new_phase(len(products), "Processing build requirements"))
        for product in db.Item.select_all_products():
            db.calculate_product_requirement_quantities(product)
            Clock.schedule_once(lambda _: self.step())
        db.population_teardown()
        self.dismiss()

class InventoryInitPopup (Popup):
    '''Initializes inventory of primes, parts, and relics'''
    def parts_init (self):
        '''Initialize inventory input

        Called automatically when the popup opens.

        '''
        self.spin_counter.text_input.text_validate_unfocus = False # TODO set in kv file
        self.spin_counter.text_input.bind(on_text_validate=self.process_next)
        self.spin_counter.set_min(0)
        self.parts = list(db.Item.select_all_products() + db.Item.select_all_components())
        self.next_part()

    def process_next (self, instance):
        if self.spin_counter.check_input():
            self.current_part.owned = int(self.spin_counter.text_input.text)
            self.current_part.save()
            if len(self.parts) <= 0: # if no parts left
                self.dismiss()
                return
            self.next_part()
            self.spin_counter.reset()
        self.spin_counter.focus = True

    def next_part (self):
        self.current_part = self.parts.pop(0)
        self.prime_prompt.text = "Enter number of {} in inventory:".format(self.current_part.name)

class DbEntryListing (BoxLayout):
    '''Image, name and information about an database entry'''
    image_path = StringProperty()
    entry = ObjectProperty()
    text = StringProperty()

    def __init__ (self, type_filter=None, **kwargs):
        # Check Type #
        if not type_filter is None\
           and 'entry' in kwargs.keys()\
           and not isinstance(kwargs['entry'], type_filter):
            Logger.error("GUI: Tried to create {} from {}"
                         .format(type(self).__name__, repr(kwargs['entry'])))
            raise TypeError("Argument to {} must be an instance of {}, not {}"
                            .format(type(self).__name__, type_filter, type(kwargs['entry'])))

        # if type check passes, proceed through MRO
        super().__init__(**kwargs)

class DbItemListing (DbEntryListing):
    def __init__ (self, item, **kwargs):
        super().__init__(entry=item, type_filter=db.Item, **kwargs)

class DbRelicListing (DbEntryListing):
    def __init__ (self, relic, **kwargs):
        super().__init__(entry=relic, type_filter=db.Relic, **kwargs)

class DbContainmentListing (DbEntryListing):
    def __init__ (self, containment, **kwargs):
        super().__init__(entry=containment,
                         type_filter=db.Containment, **kwargs)

class DbContainmentForContentsListing (DbContainmentListing):
    pass # see primetracker.kv

class DbContainmentForRelicListing (DbContainmentListing):
    pass # see primetracker.kv

class DbEntryList (BoxLayout):
    '''TODO'''
    def add (self, listing):
        '''TODO'''
        # Check Type #
        if not isinstance(listing, DbEntryListing):
            Logger.error("GUI: Tried to add {} to DbEntryList"
                         .format(listing))
            raise TypeError("Argument to DbEntryList.add must be an instance of DbEntryListing, not {}"
                            .format(type(listing).__name__))

        self.remove_widget(self.children[0])
        self.add_widget(listing)
        self.add_widget(Widget())
        return listing # TODO remove once no longer required

class DbEntryListTab (TabbedPanelItem):
    '''TODO'''
    def add (self, item):
        self.ids.item_list.add(item)

class DbEntryDetailView (BoxLayout):
    '''Shows detailed information about a database entry

    An DbEntryDetailView consists primarily of DbEntryListings, with a prominently
    displayed head listing for the displayed Item, and a sublist for related
    items.

    '''
    item_count = NumericProperty(1)

class ProductView (DbEntryDetailView):
    '''Shows information about a product (e.g. a built prime)'''
    def __init__ (self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.entry = product
        self.ids.component_tab = DbEntryListTab(text = "Components")
        self.ids.sublist_tabs.add_widget(self.ids.component_tab)
        self.ids.sublist_tabs.default_tab = self.ids.component_tab
        for component in product.needs:
            self.ids.component_tab.add(DbItemListing(component))

class ComponentView (DbEntryDetailView):
    '''Shows information about a component (e.g. a prime part)'''
    def __init__ (self, component, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.entry = component

        # Create and Populate Relics Tab #
        self.ids.relic_tab = DbEntryListTab(text = "Relics")
        self.ids.sublist_tabs.add_widget(self.ids.relic_tab)
        for containment in component.containments:
            self.ids.relic_tab.add(DbContainmentForRelicListing(containment))

        # Create and Populate Products Tab #
        self.ids.product_tab = DbEntryListTab(text = "Products")
        self.ids.sublist_tabs.add_widget(self.ids.product_tab)
        for product in component.builds:
            self.ids.product_tab.add(DbItemListing(product))
        self.ids.sublist_tabs.default_tab = self.ids.product_tab

class RelicView (DbEntryDetailView):
    '''Shows information about a relic'''
    def __init__ (self, relic, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.entry = relic

        # Create and Populate Contents Tab #
        self.ids.contents_tab = DbEntryListTab(text = "Contents")
        self.ids.sublist_tabs.add_widget(self.ids.contents_tab)
        for containment in relic.containments.order_by(db.Containment.rarity):
            self.ids.contents_tab.add(DbContainmentForContentsListing(containment))
        self.ids.sublist_tabs.default_tab = self.ids.contents_tab

class MainNavigator (BoxLayout):
    '''TODO'''
    pass

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
    PrimeTrackerApp().run()

if __name__ == '__main__': main()
