"""
Y8142984

The view method here loads a category. The view enumerates the list of projects in category.projects()

The menu method returns a list of categories that is shown in a controller that is called from the global template
"""

from error import pretty_errors
from decorators import loadcategory


@pretty_errors
@loadcategory
def view():
    return dict(category=request.vars['category'], projects=request.vars['category'].projects())


def menu():
    return dict(categories=db().select(db.category.ALL))