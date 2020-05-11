import db.primedb as db

from kivy.lang.builder import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.widget import Widget

from kivy.properties import *


Builder.load_file('gui/dbentry.kv')


class DbEntryListing(BoxLayout):
    '''Image, name and information about an database entry.

    Base class, not intended for direct instantiation.

    '''

    image_path = StringProperty()
    '''Path to the image to display alongside the listing.'''

    entry = ObjectProperty()
    '''Database entry to display information about.'''

    text = StringProperty()
    '''Text describing the database entry.'''

    def __init__(self, type_filter=None, **kwargs):
        # Check Type #
        if not type_filter is None\
           and 'entry' in kwargs.keys()\
           and not isinstance(kwargs['entry'], type_filter):
            Logger.error("GUI-DbEntry: Tried to create {} from {}"
                         .format(type(self).__name__, repr(kwargs['entry'])))
            raise TypeError("Argument to {} must be an instance of {}, not {}"
                            .format(type(self).__name__, type_filter, type(kwargs['entry'])))

        # if type check passes, proceed through MRO
        super().__init__(**kwargs)


class DbItemListing(DbEntryListing):
    '''Entry listing for Item records.'''

    def __init__(self, item, **kwargs):
        super().__init__(entry=item, type_filter=db.Item, **kwargs)


class DbRelicListing(DbEntryListing):
    '''Entry listing for Relic records/'''

    def __init__(self, relic, **kwargs):
        super().__init__(entry=relic, type_filter=db.Relic, **kwargs)


class DbContainmentListing(DbEntryListing):
    '''Entry listing for Containment records.

    Base class, not intended for direct instantiation.

    '''

    def __init__(self, containment, **kwargs):
        super().__init__(entry=containment,
                         type_filter=db.Containment, **kwargs)


class DbContainmentForContentsListing(DbContainmentListing):
    '''Entry listing for showing which Items a Relic contains.'''
    pass


class DbContainmentForRelicListing(DbContainmentListing):
    '''Entry listing for showing which Relics contain an Item.'''
    pass


class DbEntryList(BoxLayout):
    '''Container for DbEntryListings.'''

    def add(self, listing):
        '''Add a new DbEntryListing to the list.'''

        # Check type #
        if not isinstance(listing, DbEntryListing):
            Logger.error("GUI-DbEntry: Tried to add {} to DbEntryList"
                         .format(listing))
            raise TypeError("Argument to DbEntryList.add must be an instance of DbEntryListing, not {}"
                            .format(type(listing).__name__))

        # Add listing and rebuild list #
        self.remove_widget(self.children[0]) # 
        self.add_widget(listing)
        self.add_widget(Widget())
        return listing # TODO remove once no longer required


class DbEntryListTab(TabbedPanelItem):
    '''Tab for containing a DbEntryList.'''

    def add(self, item):
        '''Add a new DbEntryListing to the contained DbEntryList.'''
        self.ids.item_list.add(item)


class DbEntryDetailView(BoxLayout):
    '''Shows detailed information about a database entry.

    A DbEntryDetailView consists primarily of DbEntryListings, with a prominently
    displayed head listing for the displayed Item, and a sublist for related items.

    '''

    item_count = NumericProperty(1)


class ProductView(DbEntryDetailView):
    '''Shows information about a product (e.g. a built prime).'''

    def __init__(self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.entry = product
        self.ids.component_tab = DbEntryListTab(text = "Components")
        self.ids.sublist_tabs.add_widget(self.ids.component_tab)
        self.ids.sublist_tabs.default_tab = self.ids.component_tab
        for component in product.needs:
            self.ids.component_tab.add(DbItemListing(component))


class ComponentView(DbEntryDetailView):
    '''Shows information about a component (e.g. a prime part).'''

    def __init__(self, component, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.entry = component

        # Create and populate Relics tab #
        self.ids.relic_tab = DbEntryListTab(text = "Relics")
        self.ids.sublist_tabs.add_widget(self.ids.relic_tab)
        for containment in component.containments:
            self.ids.relic_tab.add(DbContainmentForRelicListing(containment))

        # Create and populate Products tab #
        self.ids.product_tab = DbEntryListTab(text = "Products")
        self.ids.sublist_tabs.add_widget(self.ids.product_tab)
        for product in component.builds:
            self.ids.product_tab.add(DbItemListing(product))
        self.ids.sublist_tabs.default_tab = self.ids.product_tab


class RelicView(DbEntryDetailView):
    '''Shows information about a relic.'''

    def __init__(self, relic, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.heading.entry = relic

        # Create and populate Contents tab #
        self.ids.contents_tab = DbEntryListTab(text = "Contents")
        self.ids.sublist_tabs.add_widget(self.ids.contents_tab)
        for containment in relic.containments.order_by(db.Containment.rarity):
            self.ids.contents_tab.add(DbContainmentForContentsListing(containment))
        self.ids.sublist_tabs.default_tab = self.ids.contents_tab
