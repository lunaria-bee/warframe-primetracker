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

class ItemListing (BoxLayout):
    '''Image, name and information about an database entry'''
    image_path = StringProperty()
    item_name = StringProperty()

class ItemView (BoxLayout):
    '''Shows detailed information about a database entry

    An ItemView consists primarily of ItemListings, with a prominently displayed
    head listing for the displayed Item, and a sublist for related items.

    '''
    item_count = NumericProperty(1)

    def add_sublist_item (self, item):
        '''TODO'''
        self.item_count += 1
        item_listing = ItemListing(item_name = item.name)
        self.ids.sublist.add_widget(item_listing)
        self.ids.heading.size_hint_y = 1.5 / self.item_count
        return item_listing

class ProductView (ItemView):
    '''Shows information about a product (e.g. a built prime)'''
    def __init__ (self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.ids.label.text = product.name
        for component in product.needs:
            self.add_sublist_item(component)

class ComponentView (ItemView):
    '''Shows information about a component (e.g. a prime part)'''
    def __init__ (self, component, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.item_name = component.name
        for product in component.builds:
            self.add_sublist_item(product)

class RelicView (ItemView):
    '''Shows information about a relic'''
    def __init__ (self, relic, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.item_name = relic.name
        for containment in relic.containments.order_by(db.Containment.rarity):
            self.add_sublist_item(containment)

    def add_sublist_item (self, containment):
        item_listing = super().add_sublist_item(containment.contains)
        item_listing.item_name += "\n{}".format(containment.rarity)

class TestingMenu (BoxLayout):
    def _test_item_view (self):
        item_view = ItemView()
        item_view.add_sublist_item(db.Item.get(name='Volt Prime'))
        self.clear_widgets()
        self.add_widget(item_view)

    def _test_product_view (self, product_name):
        self.clear_widgets()
        self.add_widget(ProductView(db.Item.get(name=product_name)))

    def _test_component_view (self, component_name):
        self.clear_widgets()
        self.add_widget(ComponentView(db.Item.get(name=component_name)))

    def _test_relic_view (self):
        self.clear_widgets()
        self.add_widget(RelicView(db.Relic.select()[0]))

def main ():
    PrimeTrackerApp().run()

if __name__ == '__main__': main()
