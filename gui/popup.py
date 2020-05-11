import certifi, urllib3
import db.primedb as db

from functools import partial
from threading import Thread

from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.uix.popup import Popup

from kivy.properties import *


Builder.load_file('gui/popup.kv')


class ProgressPopup(Popup):
    '''Popup window to provide information about multi-step tasks.

    This window will show a heading about the task, a progress bar, and additional
    information about the current step of the task.

    If this task is broken into multiple subtasks, hereafter called "phases," the progress
    bar can show which phase of the task is currently being comleted, independently of
    other phases.

    PROPERTIES
    phase_count: the total number of phases in the task
    current_phase: which of the phases is currently being completed
    step_prefix: text at the beginning of the information for each step
    step_postfix: text at the end of the information for each step

    '''

    phase_count = NumericProperty()
    '''Total number of phases in the task.'''

    current_phase = NumericProperty()
    '''Currently running phrase.'''

    step_prefix = StringProperty()
    '''Text at the beginning of the information for each step'''

    step_postfix = StringProperty()
    '''Text at the end of the information for each step'''


    def new_phase(self, phase_steps, phase_info,
                   step_prefix="", step_postfix=""):
        '''Start a new phase of the task.

        Even for single-phase tasks, this method must be used to initiate the first (and
        only) phase.

        Must be called asynchronously (e.g. via a Clock) for the popup to update
        correctly.

        PARAMETERS
        phase_steps: Number of steps in this phase.
        phase_info: Heading with information about what the task is doing.
        step_prefix: Updates the step_prefix property.
        step_postfix: Updates the step_postfix property.

        '''
        self.bar.max = phase_steps
        self.bar.value = 0
        self.current_phase += 1
        self.phase_info.text = ("{} ({} / {})"
                                .format(phase_info, self.current_phase, self.phase_count))
        self.step_prefix = step_prefix
        self.step_postfix = step_postfix

    def step(self, step_info="", steps=1):
        '''Indicate that some number of task steps have been completed.

        Must be called asynchronously (e.g. via Clock) for the popup to update correctly.

        PARAMETERS
        step_info: Information about this particular step.
        steps: Number of steps that have been completed since the last update.

        '''
        self.bar.value += 1
        self.step_info.text = ("{} {} {} ({:.0%})"
                               .format(self.step_prefix, step_info, self.step_postfix,
                                       self.bar.value / self.bar.max))


class DbPopulatePopup(ProgressPopup):
    '''Populates the Prime database.'''

    def start(self):
        '''Initialize database population.

        Called automatically when the popup opens.

        '''
        self.phase_count = 2
        self.execution = Thread(target=partial(DbPopulatePopup.populate, self)).start()

    def populate(self):
        '''Populate the database.'''

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


class InventoryInitPopup(Popup):
    '''Initializes inventory of primes, parts, and relics.'''

    def parts_init(self):
        '''Initialize inventory input.

        Called automatically when the popup opens.

        '''
        self.spin_counter.text_input.text_validate_unfocus = False # TODO set in kv file
        self.spin_counter.text_input.bind(on_text_validate=self.process_next)
        self.spin_counter.set_min(0)
        self.parts = list(db.Item.select_all_products() + db.Item.select_all_components())
        self.next_part()

    def process_next(self, instance):
        '''Process the next part in the database.'''
        if self.spin_counter.check_input():
            self.current_part.owned = int(self.spin_counter.text_input.text)
            self.current_part.save()
            if len(self.parts) <= 0: # if no parts left
                self.dismiss()
                return
            self.next_part()
            self.spin_counter.reset()
        self.spin_counter.focus = True

    def next_part(self):
        '''Get the next part to process.'''
        self.current_part = self.parts.pop(0)
        self.prime_prompt.text = "Enter number of {} in inventory:".format(self.current_part.name)
