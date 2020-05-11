import db.primedb as db
from gui.dbentry import\
    ComponentView, ProductView, RelicView,\
    DbContainmentForContentsListing, DbContainmentForRelicListing, DbItemListing, DbRelicListing


class TestDb:
    '''TODO'''
    def __init__(self):
        self.product = db.Item(name="Product Two Prime", owned=2)
        self.component = db.Item(name="Component Zero Prime", owned=0)
        self.relic_tier_low = db.RelicTier(name="TestLow", ordinal=5)
        self.relic_tier_high = db.RelicTier(name="TestHigh", ordinal=6)
        self.relic_low = db.Relic(tier=self.relic_tier_low,
                                  code="T5", vaulted=True)
        self.relic_high = db.Relic(tier=self.relic_tier_high,
                                   code="T6", vaulted=False)
        self.rarity_common = db.Rarity(name="Common", ordinal=-1)
        self.rarity_rare = db.Rarity(name="Rare", ordinal=1)
        self.build_requirement = db.BuildRequirement(needs=self.component,
                                                     builds=self.product,
                                                     need_count=2,
                                                     build_count=1)
        self.containment_low = db.Containment(inside=self.relic_low,
                                              contains=self.component,
                                              rarity=self.rarity_rare)
        self.containment_high = db.Containment(inside=self.relic_high,
                                               contains=self.component,
                                               rarity=self.rarity_common)


def test_product_view (product_name, parent_widget):
    parent_widget.clear_widgets()
    parent_widget.add_widget(ProductView(db.Item.get(name=product_name)))


def test_component_view (component_name, parent_widget):
    parent_widget.clear_widgets()
    parent_widget.add_widget(ComponentView(db.Item.get(name=component_name)))


def test_relic_view (parent_widget):
    parent_widget.clear_widgets()
    parent_widget.add_widget(RelicView(db.Relic.select()[0]))


def test_DbEntryListing_subclasses ():
    test_db = TestDb()

    print("===")
    print(DbItemListing(test_db.product).ids.label.text)
    print("===")
    print(DbItemListing(test_db.component).ids.label.text)
    print("===")
    print("Attempt to generate error...")
    try:
        DbItemListing(db.ItemType())
        print("...failure! DbItemListing failed to reject incorrect type.")
    except TypeError as e:
        print(e)
        print("...success!")
    print("===")
    print(DbRelicListing(test_db.relic_low).ids.label.text)
    print("===")
    print(DbRelicListing(test_db.relic_high).ids.label.text)
    print("===")
    print("Attempt to generate error...")
    try:
        DbRelicListing(db.ItemType())
        print("...failure! DbRelicListing failed to reject incorrect type.")
    except TypeError as e:
        print(e)
        print("...success!")
    print("===")
    print(DbContainmentForRelicListing(test_db.containment_low).ids.label.text)
    print(DbContainmentForContentsListing(test_db.containment_low).ids.label.text)
    print("===")
    print(DbContainmentForRelicListing(test_db.containment_high).ids.label.text)
    print(DbContainmentForContentsListing(test_db.containment_high).ids.label.text)
    print("===")
