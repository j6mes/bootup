"""
Y8142984

The project controller is used to display and edit a project
All private methods are guarded by auth.requires_login and additional constraints in LoadProject
"""

from bootupform import BOOTUPFORM
from error import pretty_errors
from decorators import LoadProject

#Used to download the image from the uploads folder
def img():
    return response.download(request, db)



#Limiting by 6 instead of 5 here because projects are displayed in a 2x3 grid (hope you dont mind)
def index():
    closest = db(openprojects & notfundedprojects & joinprojectstats & joinopenproject & joinmanager) \
        .select(db.project.ALL, db.projectstat.ALL, db.openproject.ALL, db.user.ALL,
                orderby=~db.projectstat.progress, limitby=(0, 6))

    newest = db(openprojects & notfundedprojects & joinprojectstats & joinopenproject & joinmanager) \
        .select(db.project.ALL, db.projectstat.ALL, db.openproject.ALL, db.user.ALL,
                orderby=~db.openproject.opendate, limitby=(0, 6))

    return dict(closest=closest, newest=newest)

#use the query string ?q={query} rather than python request args here as this is semantically correct
def search():
    if (request.vars['q'] is None or len(request.vars['q'].strip()) == 0):
        return dict()
    else:
        q = request.vars['q'].strip()

    qry = searchableprojects & (
    db.project.title.like('%' + q + '%') | (db.project.shortdescription.like('%' + q + '%'))) \
          & joinprojectstats & joinopenproject & joinmanager

    projects = db(qry).select(db.project.ALL, db.projectstat.ALL, db.openproject.ALL, db.user.ALL)

    return dict(projects=projects, query=q)


@pretty_errors
@LoadProject(allow_preview=True)
def view():
    return dict(record=request.vars['project'], preview=request.vars['preview'])


@pretty_errors
@auth.requires_login
@LoadProject(requires_pledge=True)
def pledge():
    addresses = db(db.address.userid == auth.user_id).count()
    cards = db(db.card.userid == auth.user_id).count()

    if addresses == 0 or cards == 0:
        raise HTTP(400, "Your profile is incomplete. Please add an address and a credit card")

    return dict(record=request.vars['project'])


@auth.requires_login
def create():
    form = BOOTUPFORM(db.project)
    message = ""
    if form.process().accepted:
        redirect(URL('user', 'projects'))
    return dict(form=form, message=message)


@pretty_errors
@auth.requires_login
@LoadProject(allow_preview=True, requires_edit=True)
def edit():
    project = request.vars['project']

    form = BOOTUPFORM(db.project, project.project, upload=URL(img))
    message = ""
    if form.process().accepted:
        redirect(URL('project', 'view', args=[project.project.idproject]))

    return dict(form=form, message=message, projectid=project.project.idproject)


@pretty_errors
@auth.requires_login
@LoadProject(allow_preview=True, requires_open=True)
def open():
    project = request.vars['project']

    form = BOOTUPFORM.confirm('Open', 'btn-primary', {'Back': URL('user', 'projects')})
    if form.accepted:
        # If the project has previously been opened, we delete the projectclosed record, otherwise create an openproject
        #record
        if db(db.openproject.projectid == project.project.idproject).count() > 0:
            db(db.closedproject.openprojectid == project.project.idproject).delete()
        else:
            db.openproject.insert(projectid=project.project.idproject)

        redirect(URL('project', 'view', args=[project.project.idproject]))

    return dict(project=project, form=form)


@pretty_errors
@auth.requires_login
@LoadProject(requires_close=True)
def close():
    project = request.vars['project']

    form = BOOTUPFORM.confirm('Close', 'btn-warning', {'Back': URL('user', 'projects')})
    if form.accepted:
        db.closedproject.insert(openprojectid=project.project.idproject)
        redirect(URL('user', 'projects'))

    return dict(record=project, form=form)


@pretty_errors
@auth.requires_login
@LoadProject(allow_preview=True, requires_delete=True)
def delete():
    project = request.vars['project']
    form = BOOTUPFORM.confirm('Delete', 'btn-danger', {'Back': URL('user', 'projects')})

    if form.accepted:
        project.project.rawdelete()
        redirect(URL('user', 'projects'))

    return dict(project=project, form=form)

