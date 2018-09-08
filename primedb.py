from peewee import *
from bs4 import BeautifulSoup, SoupStrainer
import urllib3

DB_PATH = 'primedb.sqlite'
WIKI_HOME = 'http://warframe.wikia.com/'

_primedb = SqliteDatabase(DB_PATH)

class BaseModel (Model):
    class Meta:
        database = _primedb

class DataModel (BaseModel):
    name = CharField()

    def __str__ (self):
        return self.name

class RelationModel (BaseModel):
    pass

# Data Tables #
class ItemType (DataModel):
    pass

class Item (DataModel):
    type_ = ForeignKeyField(ItemType, backref='items')
    needed = IntegerField(default=0)
    page = TextField(null = True)
    # ducats = IntegerField(default=0)

    @property
    def soup (self):
        return BeautifulSoup(self.page)

class RelicTier (DataModel):
    ordinal = SmallIntegerField(unique=True)

class Rarity (DataModel):
    ordinal = SmallIntegerField(unique=True)

class Relic (DataModel):
    tier = ForeignKeyField(RelicTier)
    code = CharField(max_length=2)
    vaulted = BooleanField(default=False)

    class Meta:
        indexes = ( (('tier', 'code'), True), )

    @property
    def name (self):
        return "{} {}".format(self.tier, self.code)

# class MissionSector (BaseModel):
#     pass

# class Mission (DataModel):
#     sector = ForeignKeyField(MissionSector)


# Relation Tables #
class BuildRequirement (RelationModel):
    needs = ForeignKeyField(Item, backref='products')
    builds = ForeignKeyField(Item, backref='components')
    need_count = IntegerField(default=1)
    build_count = IntegerField(default=1)
    class Meta:
        indexes = ( (('needs', 'builds'), True), )

class Containment (RelationModel):
    contains = ForeignKeyField(Item, backref='relics')
    inside = ForeignKeyField(Relic, backref='contents')
    rarity = ForeignKeyField(Rarity)
    # class Meta:
    #     indexes = ( (('contains', 'inside'), True), )

# class Drop (RelationModel):
#     drops = ForeignKeyField(Relic)
#     location = ForeignKeyField(Mission)


# Initialization Code #
def setup ():
    _primedb.create_tables([ItemType, Item, RelicTier, Relic, Rarity,
                            BuildRequirement, Containment])

    RelicTier(name='Lith', ordinal=0).save()
    RelicTier(name='Meso', ordinal=1).save()
    RelicTier(name='Neo',  ordinal=2).save()
    RelicTier(name='Axi',  ordinal=3).save()

    Rarity(name='Common', ordinal=0).save()
    Rarity(name='Uncommon', ordinal=1).save()
    Rarity(name='Rare', ordinal=2).save()

    ItemType(name='Prime').save()

def open_ ():
    needs_setup = not os.path.isfile(DB_PATH)
    _primedb.connect()
    if needs_setup: setup()

def close ():
    _primedb.close()


# Population Code #
def populate (list_all=False):
    http = urllib3.PoolManager()
    r = http.request('GET', 'http://warframe.wikia.com/wiki/Void_Relic/ByRewards/SimpleTable')
    tablerows = BeautifulSoup(r.data, parse_only=SoupStrainer('tr'))
    tier_records={tier.name: tier for tier in
                  [RelicTier.get(ordinal=n) for n in range(4)]}
    rarity_records={rarity.name: rarity for rarity in
                    [Rarity.get(ordinal=n) for n in range(3)]}
    prime_type = ItemType.get(name='Prime')

    for row in tablerows.contents[2:]:
        contents = row.contents
        
        # Parse Row #
        product_name = contents[1].text.strip()
        product_url = WIKI_HOME + contents[1].a['href']
        part_name = contents[2].text.strip()
        full_name = product_name + ' ' + part_name
        relic_tier = tier_records[contents[3].text.strip()]
        relic_code = contents[4].text.strip()
        rarity = rarity_records[contents[5].text.strip()]
        valuted = contents[6].text.strip() == 'Yes'

        if list_all: print("={}=".format(full_name))

        # Identify Product and Create if Needed #
        product_selection = Item.select().where(Item.name == product_name)
        if product_selection.count() == 0:
            product = Item.create(name=product_name, type_=prime_type,
                                  page=http.request('GET', product_url).data)
            # print("! {}".format(product))
        else:
            product = product_selection[0]

        # Identify Relic and Create if Needed #
        relic_selection = Relic.select().where(Relic.tier == relic_tier)\
                                        .where(Relic.code == relic_code)
        # print("{}".format([r.name for r in relic_selection]))
        if relic_selection.count() == 0:
            relic = Relic.create(tier=relic_tier, code=relic_code)
            # print("! {}".format(relic))
        else:
            relic = relic_selection[0]

        # Identify Item and Create if Needed #
        item_selection = Item.select().where(Item.name == full_name)
        if item_selection.count() == 0:
            item = Item.create(name=full_name, type_=prime_type)
            # print("! {}".format(item))
            BuildRequirement(needs=item, builds=product).save()
        else:
            item = item_selection[0]

        # Create Relic Containment Relation #
        # print("{} in {}".format(item, relic))
        Containment(contains=item, inside=relic, rarity=rarity).save()


# Testing Code #
try:
    os.remove(DB_PATH)
    print("Removed {}", DB_PATH)
except Exception:
    print("{} not found", DB_PATH)
    pass

print("==POPULATING==")
open_()
populate(True)
close()
print("==DONE==")
