"""
Y8142984

The card controller is used to set a users cards.
All methods are guarded by auth.requires_login.

The custom CARDREGISTERFROM is used by both the creation of a card and the registration form.

The loadcard is loaded from the @loadcard decorator
Where @loadcard is used, the pretty_errors decorator is also used which catches HTTP errors (like 404) and displays
a pretty error message
"""

from bootupform import BOOTUPFORM
from userform import CARDREGISTERFORM, computedate
from error import pretty_errors
from decorators import loadcard

@auth.requires_login
def index():
    cards = db(db.card.userid == auth.user_id).select()
    return dict(cards=cards)


@auth.requires_login
def create():
    form = CARDREGISTERFORM.factory(redirect_url=URL('card', 'index'))
    if form.process().accepted:
        pass

    return dict(form=form)


@auth.requires_login
def register():
    form = CARDREGISTERFORM.factory(redirect_url=URL('project', 'index'))
    if form.process().accepted:
        pass

    return dict(form=form)


@pretty_errors
@auth.requires_login
@loadcard
def edit():
    card = request.vars['address']

    form = BOOTUPFORM(db.card, card)
    if form.process(onvalidation=computedate).accepted:
        redirect(URL('card', 'index'))
    return dict(form=form)


@pretty_errors
@auth.requires_login
@loadcard
def delete():
    card = request.vars['card']

    form = BOOTUPFORM.confirm('Delete', 'btn-danger', {'Back': URL('card', 'index')})
    if form.accepted:
        db(db.card.idcard == card.idcard).delete()

        redirect(URL('card', 'index'))
    return dict(form=form)