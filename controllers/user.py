"""
Y8142984

User controller allows registration, login and editing account and listing expected rewards and dashboard projects
"""

from bootupform import BOOTUPFORM
from userform import REGISTRATIONFORM, LOGINFORM, CHANGEPASSWORDFORM, computebirthdate


def register():
    form = REGISTRATIONFORM.factory()

    message = ""

    if form.process().accepted:
        redirect(URL('card', 'register'))
    return dict(form=form, message=message)


def login():
    form = LOGINFORM.factory()

    if form.process().accepted:
        redirect(URL('user', 'index'))

    return dict(form=form)


@auth.requires_login
def logout():
    auth.logout()
    redirect(URL('project', 'index'))


@auth.requires_login
def index():
    projects = db(db.user.iduser == auth.user_id).select().first().expectedrewards()
    return dict(projects=projects)


@auth.requires_login
def projects():
    qry = myprojects

    #Fitler the projects on dashboard if request args allow
    if (request.args(0) == "not_started"):
        qry &= notstartedprojects
    elif (request.args(0) == "opened"):
        qry &= openprojects
    elif (request.args(0) == "not_funded"):
        qry &= closedprojects & notfundedprojects
    elif (request.args(0) == "funded"):
        qry &= closedprojects & fundedprojects

    projects = db(qry & joinprojectstats).select(db.project.ALL, db.projectstat.ALL)
    return dict(projects=projects)


@auth.requires_login
def edit():
    user = db(db.user.iduser == auth.user_id).select(db.user.ALL).first()
    form = BOOTUPFORM(db.user, user)

    if form.process(onvalidation=computebirthdate).accepted:
        redirect(URL('user', 'index'))
    return dict(form=form)


@auth.requires_login
def password():
    form = CHANGEPASSWORDFORM.factory()

    if form.process().accepted:
        redirect(URL('user', 'index'))
    return dict(form=form)