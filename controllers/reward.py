from applications.bootup.forms.bootupform import BOOTUPFORM
from applications.bootup.modules.error import onerror


@onerror
@auth.requires_login
def view():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404, "No project specified")

    project = db(myprojects & (db.project.idproject == projectid)).select(db.project.ALL).first()

    if project is None:
        raise HTTP(404, "Project does not exist")

    if not project.canedit():
        raise HTTP(403, "Cannot edit this project")

    return dict(project=project, projectid=projectid)


@onerror
@auth.requires_login
def create():
    projectid = request.args(0)

    if projectid is None:
        raise HTTP(404, "No project specified")

    project = db(myprojects & (db.project.idproject == projectid)).select(db.project.ALL).first()

    if project is None:
        raise HTTP(404, "Project does not exist")

    if not project.canedit():
        raise HTTP(403, "Cannot edit this project")

    form = BOOTUPFORM.factory(db.reward)
    if ( form.process().accepted):
        db.reward.insert(description=form.vars.description, projectid=projectid)
        redirect(URL('reward', 'view', args=[projectid]))
    return dict(project=project, form=form, projectid=projectid)


@onerror
@auth.requires_login
def edit():
    rewardid = request.args(0)

    if rewardid is None:
        raise HTTP(404, "No project specified")

    reward = db((db.reward.idreward == rewardid) & myprojects & (db.project.idproject == db.reward.projectid)).select(
        db.project.ALL, db.reward.ALL).first()

    if reward is None:
        raise HTTP(404, "Reward does not exist")

    if not reward.project.canedit():
        raise HTTP(403, "Cannot edit this project")

    form = BOOTUPFORM(db.reward, record=reward.reward)
    if ( form.process().accepted):
        redirect(URL('reward', 'view', args=[reward.reward.projectid]))
    return dict(form=form, projectid=reward.reward.projectid)


@onerror
@auth.requires_login
def delete():
    rewardid = request.args(0)

    if rewardid is None:
        raise HTTP(404, "No project specified")

    reward = db((db.reward.idreward == rewardid) & myprojects & (db.project.idproject == db.reward.projectid)).select(
        db.project.ALL, db.reward.ALL).first()

    if reward is None:
        raise HTTP(404, "Reward does not exist")

    if not reward.project.canedit():
        raise HTTP(403, "Cannot edit this project")

    form = FORM.confirm('Delete', {'Back': URL(request.env.http_referrer)})
    projectid = reward.reward.projectid

    if form.accepted:
        db(db.reward.idreward == rewardid).delete()
        redirect(URL('reward', 'view', args=[projectid]))

    return dict(form=form, projectid=projectid)
