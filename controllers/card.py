import calendar
from datetime import date, datetime
from applications.bootup.forms.bootupform import BOOTUPFORM

def computedate(form):
    form.vars.expdate = date(int(str(request.now.year)[0:2]+form.vars.expdate_year), int(form.vars.expdate_month), calendar.monthrange(int(str(request.now.year)[0:2]+form.vars.expdate_year), int(form.vars.expdate_month))[1])


@auth.requires_login
def index():
    cards = db(db.card.userid==auth.user_id).select()
    return dict(cards=cards)

@auth.requires_login
def create():
    form = BOOTUPFORM(db.card)
    if form.process(onvalidation=computedate).accepted:
        redirect(URL('bootup','card','index'))

    return dict(form=form)

@auth.requires_login
def edit():
    cardid=request.args(0)

    if cardid is None:
        raise HTTP(404, "No card id is set")

    card = db((db.card.userid==auth.user_id) & (db.card.idcard == cardid)).select(db.card.ALL).first()

    if card is None:
        raise HTTP(404,"Card not found")

    form = BOOTUPFORM(db.card,card)
    if form.process(onvalidation=computedate).accepted:
        redirect(URL('bootup','card','index'))
    return dict(form=form)


def delete():
    cardid=request.args(0)

    if cardid is None:
        raise HTTP(404, "No card id is set")

    card = db((db.card.userid==auth.user_id) & (db.card.idcard == cardid)).select(db.card.ALL).first()

    if card is None:
        raise HTTP(404,"Card not found")

    form = FORM.confirm('Delete',{'Back':URL('bootup','card','index')})
    if form.process().accepted:
        db(db.card.idcard==cardid).delete()
        redirect(URL('bootup','card','index'))
    return dict(form=form)