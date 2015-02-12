"""
Y8142984

The address controller is used to edit addresses when a user is logged in.
All methods are guarded by auth.requires_login.

The address is loaded from the @loadaddress decorator
Where @loadaddress is used, the pretty_errors decorator is also used which catches HTTP errors (like 404) and displays
a pretty error message
"""

from bootupform import BOOTUPFORM
from error import pretty_errors
from decorators import loadaddress


@auth.requires_login
def index():
    addresses = db(myaddresses & joincountry).select(
        db.address.ALL, db.country.ALL)
    return dict(addresses=addresses)


@auth.requires_login
def create():
    form = BOOTUPFORM(db.address)
    if form.process().accepted:
        redirect(URL('address', 'index'))

    return dict(form=form)


@pretty_errors
@auth.requires_login
@loadaddress
def edit():
    address = request.vars['address']

    form = BOOTUPFORM(db.address, address)

    if form.process().accepted:
        redirect(URL('address', 'index'))

    return dict(form=form)


@pretty_errors
@auth.requires_login
@loadaddress
def delete():
    address = request.vars['address']

    form = BOOTUPFORM.confirm('Delete', 'btn-danger', {'Back': URL('card', 'index')})
    if form.accepted:
        db(db.address.idaddress == address.idaddress).delete()
        redirect(URL('address', 'index'))

    return dict(form=form)


