from applications.bootup.forms.bootupform import BOOTUPFORM
from applications.bootup.modules.error import onerror


@onerror
@auth.requires_login
def make():
    pledgeid = request.args(0)
    if pledgeid is None:
        raise HTTP(404, 'No pledge specified')

    pledge = db((db.pledge.idpledge == pledgeid) & (db.project.idproject == db.pledge.projectid)).select(db.project.ALL,
                                                                                                         db.pledge.ALL).first()

    if pledge is None:
        raise HTTP(404, 'Pledge level does not exist')

    if not pledge.project.canpledge():
        raise HTTP(403, 'Project is not open for pledges')

    if pledge.project.hascontributed():
        raise HTTP(403, 'Already contributed')

    form = BOOTUPFORM.factory(db.booting)
    if form.process().accepted:
        db.booting.insert(openprojectid=pledge.project.idproject, pledgeid=pledgeid, addressid=form.vars.addressid,
                          cardid=form.vars.cardid, bootingdate=request.now, userid=auth.user_id)
        redirect(URL('bootup', 'project', 'view', args=[pledge.project.idproject]))

    return dict(pledge=pledge, form=form)


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

    form = BOOTUPFORM.factory(db.pledge, Field('rewards', requires=IS_IN_DB(db(db.reward.projectid == projectid),
                                                                            db.reward.idreward, '%(description)s',
                                                                            multiple=[1, 9999],
                                                                            error_message="Please select at least one reward")))

    if ( form.process().accepted):

        pledgeid = db.pledge.insert(idpledge=None, description=form.vars.description, value=form.vars.value,
                                    projectid=projectid)

        for reward in form.vars.rewards:
            reward = int(reward)
            dbreward = db(db.reward.idreward == reward).select(db.reward.ALL).first()
            if int(dbreward.projectid) is int(projectid):
                db.rewardpledge.insert(rewardid=reward, pledgeid=pledgeid)

        redirect(URL('bootup', 'pledge', 'view', args=[projectid]))
    return dict(project=project, form=form, projectid=projectid)


@onerror
@auth.requires_login
def edit():
    pledgeid = request.args(0)

    if pledgeid is None:
        raise HTTP(404, "No project specified")

    pledge = db((db.pledge.idpledge == pledgeid) & myprojects & (db.project.idproject == db.pledge.projectid)).select(
        db.project.ALL, db.pledge.ALL).first()

    if pledge is None:
        raise HTTP(404, "Reward does not exist")

    if not pledge.project.canedit():
        raise HTTP(403, "Cannot edit this project")

    record = dict(description=pledge.pledge.description, value=pledge.pledge.value, rewards=pledge.pledge.rewardids(),
                  projectid=pledge.pledge.projectid, id=13)
    form = BOOTUPFORM.factory(db.pledge,
                              Field('rewards', requires=IS_IN_DB(db(db.reward.projectid == pledge.pledge.projectid),
                                                                 db.reward.idreward, '%(description)s',
                                                                 multiple=[1, 9999],
                                                                 error_message="Please select at least one reward")),
                              record=record)
    if ( form.process().accepted):
        for reward in pledge.pledge.rewardids():
            db((db.rewardpledge.pledgeid == int(pledge.pledge.idpledge)) & (
            db.rewardpledge.rewardid == int(reward))).select(db.rewardpledge.ALL).first().rawdelete()

        for reward in form.vars.rewards:
            reward = int(reward)
            dbreward = db(db.reward.idreward == reward).select(db.reward.ALL).first()
            if int(dbreward.projectid) is int(pledge.pledge.projectid):
                db.rewardpledge.insert(rewardid=reward, pledgeid=pledgeid)

        db(db.pledge.idpledge == pledgeid).update(description=form.vars.description, value=form.vars.value)

        redirect(URL('bootup', 'pledge', 'view', args=[pledge.pledge.projectid]))
    return dict(form=form, projectid=projectid)


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
        redirect(URL('bootup', 'reward', 'view', args=[projectid]))

    return dict(form=form, projectid=projectid)
