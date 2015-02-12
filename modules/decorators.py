from gluon import HTTP, LOAD, current


def loadaddress(function):
    def _a(*args, **kwargs):
        addressid = current.request.args(0)

        if addressid is None:
            raise HTTP(404, "No address specified")

        address = current.db(current.myaddresses & current.joincountry & (current.db.address.idaddress == addressid)).select(current.db.address.ALL).first()

        if address is None:
            raise HTTP(404, "Address does not exist")


        current.request.vars['address'] = address

        return function(*args, **kwargs)

    return _a


def loadcard(function):
    def _a(*args, **kwargs):
        cardid = current.request.args(0)

        if cardid is None:
            raise HTTP(404, "No card specified")

        card = current.db(current.mycards & (current.db.card.idcard == cardid)).select(current.db.card.ALL).first()

        if card is None:
            raise HTTP(404, "Card does not exist")


        current.request.vars['card'] = card

        return function(*args, **kwargs)

    return _a


def loadcategory(function):
    def _a(*args, **kwargs):
        categoryurl = current.request.args(0)

        if categoryurl is None:
            raise HTTP(404, "Category not found")

        category = current.db(current.db.category.url == categoryurl).select().first()
        if category is None:
            raise HTTP(404, "Category not found")


        current.request.vars['category'] = category

        return function(*args, **kwargs)

    return _a


class LoadPledge:

    def __init__(self, requires_edit = False, requires_pledge = False):
        self.requires_edit = requires_edit
        self.requires_pledge = requires_pledge

    def __call__(self,function):
        def _a(*args, **kwargs):
            pledgeid = current.request.args(0)

            if pledgeid is None:
                raise HTTP(404, "No pledge specified")

            pledge = current.db(current.myprojects & current.joinprojectpledges & (current.db.pledge.idpledge == pledgeid)).select(
                current.db.project.ALL, current.db.pledge.ALL).first()

            if pledge is None:
                raise HTTP(404, "Pledge does not exist")


            if self.requires_edit and not pledge.project.canedit():
                raise HTTP(403, "Cannot edit this project")


            if self.requires_pledge and pledge.project.hascontributed():
                raise HTTP(403, 'Already contributed')


            current.request.vars['pledge'] = pledge

            return function(*args, **kwargs)

        return _a




class LoadProject:

    def __init__(self, requires_edit = False, requires_delete = False, requires_pledge = False, allow_preview = False, requires_open=False, requires_close=False):
        self.allow_preview = allow_preview
        self.requires_edit = requires_edit
        self.requires_delete = requires_delete
        self.requires_pledge = requires_pledge
        self.requires_edit = requires_edit
        self.requires_open = requires_open
        self.requires_close = requires_close

    def __call__(self,function):
        def _a(*args, **kwargs):
            projectid = current.request.args(0)

            if projectid is None:
                raise HTTP(404, "Project not found")

            preview = False
            project = current.db(current.searchableprojects & current.joinprojectstats & current.joinopenproject & current.joinmanager & (
                current.db.project.idproject == projectid)).select(current.db.project.ALL, current.db.projectstat.ALL, current.db.openproject.ALL,
                                                           current.db.user.ALL).first()

            if project is None:
                if self.allow_preview:
                    project = current.db(current.myprojects & current.joinprojectstats & current.joinmanager & (
                    current.db.project.idproject == projectid)).select(current.db.project.ALL, current.db.projectstat.ALL, current.db.user.ALL).first()

                    preview = True



            if project is None:
                raise HTTP(404, "This project either doesn't exist or hasn't been made public yet.")




            if self.requires_edit and not project.project.canedit():
                raise HTTP(400,"You cannot edit this project")


            if self.requires_delete and not project.project.candelete():
                raise HTTP(400,"You cannot delete this project")

            if self.requires_open and not project.project.canopen():
                raise HTTP(400,"You cannot open this project")

            if self.requires_open and len(project.project.pledges()) == 0:
                raise HTTP(400, "Project needs pledge levels before it can be opened")

            if self.requires_close and not project.project.canclose():
                raise HTTP(400,"You cannot close this project")

            current.request.vars['project'] = project
            current.request.vars['preview'] = preview
            return function(*args, **kwargs)

        return _a



def loadreward(function):
    def _a(*args, **kwargs):
        rewardid = current.request.args(0)

        if rewardid is None:
            raise HTTP(404, "No reward specified")

        reward = current.db((current.db.reward.idreward == rewardid) & current.myprojects & (current.db.project.idproject == current.db.reward.projectid)).select(
            current.db.project.ALL, current.db.reward.ALL).first()

        if reward is None:
            raise HTTP(404, "Reward does not exist")

        if not reward.project.canedit():
            raise HTTP(403, "Cannot edit this project")

        current.request.vars['reward'] = reward

        return function(*args, **kwargs)

    return _a

