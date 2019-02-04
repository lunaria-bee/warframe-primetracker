import primedb as db

def initialize_collection ():
    for product in db.Item.select_products():
        requirements = (db.BuildRequirement.select()
                      .where(db.BuildRequirement.builds==product))

        owned = input("Do you have {}? (y/n):  ".format(product))
        while not owned in 'YyNn':
            owned = input("Please enter 'y' or 'n':  ")

        if owned in 'Nn':
            product.needed = 1
            for req in requirements:
                component = req.needs
                comp_owned = input("Enter # of owned {}:  ".format(component))
                while True:
                    try:
                        comp_owned = int(comp_owned)
                        if comp_owned < 0: raise ValueError("Must be positive")
                        break # TODO rewrite w/o break
                    except ValueError (e):
                        comp_owned = input("Please enter a positive number:  ")
                
