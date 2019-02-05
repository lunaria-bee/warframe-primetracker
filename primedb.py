from peewee import *
from bs4 import BeautifulSoup, SoupStrainer
from kivy.logger import Logger
import certifi, urllib3

DB_PATH = 'primedb.sqlite'
WIKI_HOME = 'http://warframe.fandom.com'

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
    page = TextField(null = True)
    # ducats = IntegerField(default=0)

    @staticmethod
    def select_all_products ():
        return [p for p in Item.select() if # TODO do in one query
                BuildRequirement.select().where(BuildRequirement.builds==p)]

    @staticmethod
    def select_all_components ():
        return [p for p in Item.select() if # TODO do in one query
                BuildRequirement.select().where(BuildRequirement.needs==p)]

    @property
    def soup (self):
        return BeautifulSoup(self.page, 'lxml')

    @property
    def relics (self):
        return [c.inside for c in self.containments]

    @property
    def builds (self):
        return [b.builds for b in self.requirements]

    @property
    def requires (self):
        return [b.requires for b in self.requirements]

    @property
    def vaulted (self):
        return all([r.vaulted for r in self.relics])

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

    @property
    def contents (self):
        return [c.contains for c in self.containments]

# class MissionSector (BaseModel):
#     pass

# class Mission (DataModel):
#     sector = ForeignKeyField(MissionSector)


# Relation Tables #
class BuildRequirement (RelationModel):
    needs = ForeignKeyField(Item, backref='requirements')
    builds = ForeignKeyField(Item, backref='requirements')
    need_count = IntegerField(default=1)
    build_count = IntegerField(default=1)
    class Meta:
        indexes = ( (('needs', 'builds'), True), )

    def __str__ (self):
        return "{} <- {}".format(self.needs, self.builds)

class Containment (RelationModel):
    contains = ForeignKeyField(Item, backref='containments')
    inside = ForeignKeyField(Relic, backref='containments')
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
    Logger.info("Database: Population: Started")

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                               ca_certs=certifi.where())
    r = http.request('GET', WIKI_HOME + '/wiki/Void_Relic/ByRewards/SimpleTable')
    tablerows = BeautifulSoup(r.data, 'lxml', parse_only=SoupStrainer('tr'))
    tier_records={tier.name: tier for tier in
                  [RelicTier.get(ordinal=n) for n in range(4)]}
    rarity_records={rarity.name: rarity for rarity in
                    [Rarity.get(ordinal=n) for n in range(3)]}
    prime_type = ItemType.get(name='Prime')

    # Initial Population #
    for row in tablerows.contents[2:]:
        contents = row.contents

        # Parse Row #
        product_name = contents[1].text.strip()
        product_url = WIKI_HOME + contents[1].a['href']
        part_name = contents[2].text.strip()       # e.g. "Chassis"
        full_name = product_name + ' ' + part_name # e.g. "Volt Prime Chassis"
        relic_tier = tier_records[contents[3].text.strip()]
        relic_code = contents[4].text.strip()
        rarity = rarity_records[contents[5].text.strip()]
        vaulted = contents[6].text.strip() == 'Yes'

        Logger.debug("Database: Population: Processing {} in {} {}"
                     .format(full_name, relic_tier, relic_code))

        # Identify Product and Create if Needed #
        product_selection = Item.select().where(Item.name == product_name)
        if product_selection.count() == 0:
            product = Item.create(name=product_name, type_=prime_type,
                                  page=http.request('GET', product_url).data)
        else:
            product = product_selection[0]

        # Identify Relic and Create if Needed #
        relic_selection = Relic.select().where(Relic.tier == relic_tier)\
                                        .where(Relic.code == relic_code)
        if relic_selection.count() == 0:
            relic = Relic.create(tier=relic_tier, code=relic_code, vaulted=vaulted)
        else:
            relic = relic_selection[0]

        # Identify Item and Create if Needed #
        item_selection = Item.select().where(Item.name == full_name)
        if item_selection.count() == 0:
            item = Item.create(name=full_name, type_=prime_type)
            Logger.debug("Database: entry ({}, {}) created"
                        .format(item, product))
            BuildRequirement(needs=item, builds=product).save()
        else:
            item = item_selection[0]

        # Create Relic Containment Relation #
        Containment(contains=item, inside=relic, rarity=rarity).save()

    # Calculate Required Part Quantities #
    for product in Item.select_products():
        foundry_table = BeautifulSoup(product.page, 'lxml',
                                      parse_only=SoupStrainer(class_='foundrytable'))
        # manually access the table row with build requirements
        for req in [r for r in foundry_table.contents[1].contents[3].find_all('td') if r.a]:
            count = req.text.strip()
            part_name = req.a['title'].strip()
            part_query = Item.select().where(Item.name.contains(product.name)
                                             & Item.name.contains(part_name))
            if part_query:
                part = part_query[0]
                relation = (BuildRequirement.select()
                            .where((BuildRequirement.builds==product)
                                   & (BuildRequirement.needs==part)))
                if relation and count:
                    relation[0].need_count=count
                    relation[0].save()
                    Logger.debug("Database: {} needs {} {}"
                                 .format(product.name, count, part.name))

    Logger.info("Database: Population: Completed")


# Testing Code #
def __test_population (log_level='DEBUG'):
    Logger.setLevel(log_level)
    try:
        os.remove(DB_PATH)
        Logger.info("Database: {} deleted".format(DB_PATH))
    except Exception:
        Logger.info("Database: {} not found".format(DB_PATH))

    open_()
    populate(True)
    close()
    
