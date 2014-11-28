from applications.bootup.forms.bootupform import BOOTUPFORM
from applications.bootup.modules.error import onerror


def setuserid(form):
    form.vars.userid = auth.user_id


@auth.requires_login
def create():
    form = BOOTUPFORM(db.address)
    if form.process(onvalidation=setuserid).accepted:
        redirect(URL('bootup', 'address', 'index'))

    return dict(form=form)


@onerror
@auth.requires_login
def edit():
    addressid = request.args(0)

    if addressid is None:
        raise HTTP(404, 'No address id specified')

    address = db((db.address.idaddress == addressid) & (db.address.userid == auth.user_id)).select(
        db.address.ALL).first()

    if address is None:
        raise HTTP(404, 'Address not found')

    form = BOOTUPFORM(db.address, address)

    if form.process().accepted:
        redirect(URL('bootup', 'address', 'index'))

    return dict(form=form)


@onerror
@auth.requires_login
def delete():
    addressid = request.args(0)

    if addressid is None:
        raise HTTP(404, 'No address id specified')

    address = db((db.address.idaddress == addressid) & (db.address.userid == auth.user_id)).select(
        db.address.ALL).first()

    if address is None:
        raise HTTP(404, 'Address not found')

    form = FORM.confirm('Delete', {'Back': URL('bootup', 'address', 'index')})

    if form.accepted:
        db(db.address.idaddress == addressid).delete()
        redirect(URL('bootup', 'address', 'index'))

    return dict(form=form)


@auth.requires_login
def index():
    addresses = db((db.address.userid == auth.user_id) & (db.country.code == db.address.countrycode)).select(
        db.address.ALL, db.country.ALL)
    return dict(addresses=addresses)