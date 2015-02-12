from itertools import groupby
from gluon import current, DAL, Field, DIV,SELECT
from gluon.validators import *
from gluon.custom_import import track_changes

from bootupauth import BootUpAuth

import math
from datetime import datetime
track_changes(True)


db = DAL('sqlite://bootup.db', pool_size=1, check_reserved=['sqlite'], migrate=False)
current.db = db

auth = BootUpAuth()


def date_mmyy_widget(field, value):
    monthvals = map(lambda val: str(val).zfill(2), range(1, 12 + 1))
    yearvals = map(lambda val: str(val)[2:], range(current.request.now.year, current.request.now.year + 7))

    if value is not None:
        value = datetime.strptime(value, '%Y-%m-%d').date()
        monthvals.insert(0, str(value.month).zfill(2))
        yearvals.insert(0, str(value.year)[2:])

    return DIV(SELECT(monthvals, _name=field.name + "_month"), SELECT(yearvals, _name=field.name + "_year"))


def date_yyyymmdd_widget (field, value):
    dayvals = map(lambda val: str(val).zfill(2), range(1, 31+1))
    monthvals = map(lambda val: str(val).zfill(2), range(1, 12 + 1))
    yearvals = map(lambda val: str(val), reversed(range( current.request.now.year -100,current.request.now.year-16)))

    if value is not None:
        value = datetime.strptime(value, '%Y-%m-%d').date()
        dayvals.insert(0, str(value.day).zfill(2))
        monthvals.insert(0, str(value.month).zfill(2))
        yearvals.insert(0, str(value.year-16))
    else:
        dayvals.insert(0, "Day")
        monthvals.insert(0, "Month")
        yearvals.insert(0, "Year")


    return DIV(SELECT(dayvals, _name=field.name + "_day"), SELECT(monthvals, _name=field.name + "_month"), SELECT(yearvals, _name=field.name + "_year"))






"""
Notes:

    "Database first" strategy was used when writing the BootUp web app. This means that a number of the constraints that
    appear in the specification may not be listed here due to limitations with web2py's support for schemas that are
    generated outside web2py.

    DDL will be included in the comments for each "define_table" statement to allow a better understanding of all the
    constraints that lie in the database. This can also be found in  /databases/bootup.sql

"""


"""
Category
Fields: IdCategory (integer) PRIMARY KEY AUTO INCREMENT, Name (string), URL (string) UNIQUE INDEX

Category is not written to using the DAL and therefore does not require validators/writable/default values.
The URL column is used for pretty style URLs (/category/art) etc. It is indexed and unique.




CREATE TABLE Category (
    IdCategory INTEGER        PRIMARY KEY AUTOINCREMENT
                              NOT NULL,
    Name       VARCHAR( 60 )  NOT NULL,
    Url        VARCHAR( 60 )  NOT NULL
                              UNIQUE
);

CREATE INDEX idx_CategoryUrl ON Category (
    Url COLLATE NOCASE ASC
);

"""
db.define_table('category',
                Field('idcategory', type='id'),
                Field('name'),
                Field('url'))



"""
User
Fields: IdUser (integer) PRIMARY KEY AUTO INCREMENT, RealName (string), DateOfBirth (date), UserName (string(120)) UNIQUE INDEX
Computed: Age (integer)

IdUser is set to be hidden from the forms (writable=False, readable=False). Setting default=None allows the database to
generate a unique primary key rather than relying on web2py to generate this.

Age is as the number of years from request.now and the birthdate stored in the record.



CREATE TABLE User (
    IdUser      INTEGER         PRIMARY KEY AUTOINCREMENT
                                NOT NULL,
    Username    VARCHAR( 60 )   NOT NULL
                                UNIQUE,
    RealName    VARCHAR( 200 )  NOT NULL,
    DateOfBirth DATE            NOT NULL
);
"""
db.define_table('user',
                Field('iduser', type='id', readable=False, writable=False, default=None),
                Field('realname', label='Name', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter your name'),
                    IS_LENGTH(maxsize=200, error_message='Please enter a shorter name'),

                ]),
                Field('dateofbirth', type='date', label='Date of Birth', widget=date_yyyymmdd_widget, requires=[
                    IS_DATE(error_message='Please enter a date'),

                    # IS_DATE_IN_RANGE(error_message='Please enter a date in the recent past')
                ]),
                Field('username', label='Username', requires=[
                    IS_LENGTH(minsize=1, error_message='Please choose a username'),
                    IS_LENGTH(maxsize=60, error_message='Please chose a shorter username'),
                    IS_NOT_IN_DB(db, 'user.username', error_message="Username is already taken")
                ]),
                Field.Method('expectedrewards', lambda row: groupby(
                    db(
                        (db.expectedrewards.userid == row.user.iduser) &
                        (db.expectedrewards.projectid == db.project.idproject) &
                        (db.pledge.idpledge == db.expectedrewards.pledgeid) &
                        joinprojectstats)
                    .select(db.expectedrewards.ALL,
                            db.project.ALL,
                            db.projectstat.ALL,
                            db.pledge.ALL

                    ),
                    key=lambda item: item.project.idproject)),
                Field.Method('age', lambda row: current.request.now.year - row.dateofbirth.year
                    if (current.request.now.month, current.request.now.day) >= (row.dateofbirth.month, row.dateofbirth.day) else
                    current.request.now.year - row.dateofbirth.year - 1),
)





"""
Credential
Fields: UserId (PRIMARY KEY REFERENCES User), Salt (string), Hash (string)

The users' credentials are stored in a separate table from the account. This seperation of concerns allows a default
SQLForm to be used when creating/editing users and a special type of form (like CHANGEPASSWORD in /forms/userform.py) to
be used to set only the passwords.

As primary key is a reference to user, the type='id' parameter cannot be set as this causes web2py to break.
The primarykey= kwarg is being used instead

The code used to generate the salt/hash is contained within the authentication module in /modules/auth.py
The authentication module is a greatly simplified version of the built in auth. As full role-based authentication is not
needed, the simplified version will do just fine.




CREATE TABLE Credential (
    UserId       INTEGER        PRIMARY KEY
                                NOT NULL
                                REFERENCES User ( IdUser ) ON DELETE CASCADE
                                                           ON UPDATE CASCADE,
    PasswordSalt VARCHAR( 22 )  NOT NULL,
    PasswordHash VARCHAR( 64 )  NOT NULL
);
"""
db.define_table('credential',
                Field('userid', type='reference user', readable=False, writable=False),
                Field('passwordhash', writable=False, readable=False),
                Field('passwordsalt', writable=False, readable=False),
                primarykey=['userid']
)

"""
Country
Fields: CODE (CHAR(3)) PRIMARY KEY, Name (String)

This lookup table contains a list of countries that are used to populate country drop-down boxes for addresses.
The country table is not written to using the DAL and therefore does not require validators/writable/default values.

There is a limitation with web2py that type='id' only supports integer types,
as country code is a string, the primary key must be defined using the primarykey kwarg

As described in the report, the country code is an ISO-3 letter country code and therefore a fixed 3 letter char can be
used to store this field.



CREATE TABLE Country (
    Code CHAR( 3 )      PRIMARY KEY
                        NOT NULL,
    Name VARCHAR( 60 )  NOT NULL
);
"""
db.define_table('country',
                Field('code'),
                Field('name'),
                primarykey=['code'])


"""
Address
Fields: IdAddress(String), Street(String), City (String), PostCode (String), Country (Country), UserId (User)

The IdAddress PK field is incremented by the DB engine. Setting default None and readable/writable = False to hide it
from auto-generated SQLFORMS in web2py.

Street and city are stored as plain text fields. The length of these fields is restricted to 100 characters as a sensible
limit.

Postcode is stored in a CHAR(8) as it is always expected to be in the fixed format of XXXX XXX. The postcode has a regex
validator on it requiring it to match the pattern XXXX XXX. This assumes that all post codes in the world fit this the
value. However this is what is specified in the requirements document.

The address table references the country table. I had to remove explicit reference to country code as for some reason
web2py restricts all references to be numeric to maintain this constraint which doesn't work as country code is a CHAR(3)
The IS_IN_DB validator is used to generate a dropdown list for the create/edit address forms.

Likewise, a IS_IN_DB validator is used to enforce the relation to an active users. This field is set to be the current
user's id by default and can be overriden if neccesary. As this field has a default value, readable and writable are set
to false to prevent this field from appearing on the web2py auto generated forms.

The FK constraints to User/Country are set to ON DELETE restrict as there is no behaviour specified for removing users
and countries.



CREATE TABLE Address (
    IdAddress   INTEGER         PRIMARY KEY AUTOINCREMENT
                                NOT NULL,
    Street      VARCHAR( 100 )  NOT NULL,
    City        VARCHAR( 100 )  NOT NULL,
    PostCode    CHAR( 8 )       NOT NULL,
    CountryCode CHAR( 3 )       NOT NULL
                                REFERENCES Country ( Code ) ON DELETE RESTRICT
                                                            ON UPDATE CASCADE,
    UserId      INTEGER         NOT NULL
                                REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                           ON UPDATE CASCADE
);

"""
db.define_table('address',
                Field('idaddress', type='id', readable=False, writable=False, default=None),
                Field('street', label='Street', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter your street address'),
                    IS_LENGTH(maxsize=100, error_message='Please enter a shorter street address')
                ]),
                Field('city', label='City', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter your city'),
                    IS_LENGTH(maxsize=100, error_message='Please enter a shorter city name')
                ]),
                Field('postcode', label='Post Code', requires=[
                    IS_LENGTH(maxsize=8),
                    IS_MATCH('^[a-zA-Z0-9]{4} [a-zA-Z0-9]{3}$', error_message='Postcode must be in the format XXXX XXX')
                ]),
                Field('countrycode', type='string', label='Country', requires=IS_IN_DB(db, db.country.code, '%(name)s',
                                                                      zero='Select A Country',
                                                                      error_message='Please choose your country'
                )),
                Field('userid', type='reference user',
                      requires=IS_IN_DB(db, db.user.iduser),
                      default=auth.user_id,
                      readable=False, writable=False)
)



"""
Card


"""


db.define_table('card',
                Field('idcard', type='id', readable=False, writable=False, default=None),
                Field('userid', default=auth.user_id, readable=False, writable=False),
                Field('number', type='string', label='Card Number', requires=[
                    IS_LENGTH(maxsize=12, minsize=12, error_message='Credit Card number must be 12 digits long')]),
                Field('expdate', type='date', label='Expiry Date', widget=date_mmyy_widget),
                Field('pin', requires=[IS_LENGTH(minsize=3, maxsize=3, error_message="Pin must be 3 digits long"),
                                       IS_MATCH('^[0-9]{3}$', error_message='Pin must be 3 numeric digits')]),
                Field('addressid', type='reference address', label='Billing Address',
                      requires=IS_IN_DB(db(db.address.userid == auth.user_id),
                                        db.address.idaddress, '%(street)s, %(city)s, %(postcode)s',
                                        zero='Select an address',
                                        error_message='Please choose your billing address'
                      )),
                Field.Method('display_expdate',lambda row: str(row.card.expdate.month).zfill(2) + "/" + str(row.card.expdate.year)[2:]),
                migrate=False)







"""
Project
Fields: IdProject (integer) PRIMARY KEY AUTO INCREMENT, Title (string (60)), ShortDescription (string (120)),
        LongDescrpition (text), Story (text), Goal (currency), CategoryId (category), ManagerId (user), ImageUrl (url)

Computed:   canopen, canclose, canedit, candelete, canpledge, isopen, isfunded, isclosed, hascontributed, state,
            pledges, rewards, expectedrewards


ProjectId is set readable/writable=False and default to None to allow the DB to generate a primary key without causing
web2py to show it in the forms.

Title is set to be limited to 60 characters as a sensible constraint.

Short description is set to be limited to 120 characters as specified in the requirements. The field type has been set
to Text rather than String as this allows web2py to show a multi-line textbox for this which prompts the user into entering
a longer description rather than displaying a single line text box.

Long description and story are unlimited length text fields - stored as TEXT in the database

Project Goal is stored as a numeric field type (decimal) with 2 digits of precision as this is the most appropriate
analogue for storing monetary values regardless of whether the full amount or a rounded value is displayed on the web
page. Web2Py validators are used to constrain the value between 10^2 and 10^8 as these seem like sensible limits on a
funding goal for a crowd funding project.

ImageUrl is stored as a TEXT field. Web2Py generates a random URL for each image. There is no guarantee on the length of
this value. This also provides a better future proofing for moving content to a CDN in the future as Amazon S3/Rackspace
urls to assets can be hundreds of characters long - exceeding the max length for VARCHAR. AutoDelete is set to true to
remove images from the uploads directory if a project is deleted. The IS_IMAGE validator is used to restrict file upload
type to JPG/PNG/GIF as required in specification

ManagerId and CategoryId are set to reference category/user tables as appropriate. Category uses a IS_IN_DB validator
to generate the dropdown list, whereas manager ID is set to default to the value of the current user id.

canopen, canclose, candelete and canedit computed fields are computed on-demand rather than when the record is fetched,
in each of these methods, a check is made to verify that the current user is the manager and that the project is in the
correct state to allow the action

Correct behavior:

                Not Available           Open        Closed(Funded)      Closed(Not Funded)
canedit         yes                     no          no                  no
candelete       yes                     no          yes                 yes
canopen         yes                     no          no                  yes
canclose        no                      yes         no                  no



Implementation:

canedit =   ismanager AND not opened
candelete = ismanager AND (not opened OR closed)
canopen =   ismanager AND (not opened OR (closed AND not funded))
canclose =  ismanager AND opened AND not closed


isfunded = total pledge value >= goal
isopen = exists db.openproject where projectid = idproject
isclosed = exists db.closedproject where openprojectid = idproject


Project state:
                        IsOpen  IsClosed    IsFunded
    Not Available       no      x           x
    Open                yes     no          x
    Closed (funded)     yes     yes         yes
    Closed (not funded) yes     yes         no


Pledges:
    pledges where projectid = project.idproject

Rewards:
    rewards where projectid = project.idproject

HasPledged:
    where booting (user.id = current user) is greater than 0



CREATE TABLE Project (
    IdProject        INTEGER           PRIMARY KEY AUTOINCREMENT
                                       NOT NULL,
    Title            VARCHAR( 60 )     NOT NULL,
    ShortDescription VARCHAR( 120 )    NOT NULL,
    LongDescription  TEXT              NOT NULL,
    Story            TEXT              NOT NULL,
    Goal             NUMERIC( 10, 2 )  NOT NULL,
    ImageUrl         TEXT              NOT NULL,
    CategoryId       INTEGER           NOT NULL
                                       REFERENCES Category ( IdCategory ) ON DELETE RESTRICT
                                                                          ON UPDATE CASCADE,
    ManagerId        INTEGER           NOT NULL
                                       REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                                  ON UPDATE CASCADE
);


"""
db.define_table('project',
                Field('idproject', type='id', readable=False, writable=False, default=None),
                Field('title',
                      type='string',
                      label='Project Name',
                      requires=[
                          IS_LENGTH(60, error_message='Project title must be shorter than 60 characters'),
                          IS_NOT_EMPTY(error_message='Project must have a title')
                      ]),

                Field('shortdescription',
                      label='Quick Summary',
                      type='text',
                      requires=[
                          IS_LENGTH(120, error_message='Project summary must be shorter than 120 characters'),
                          IS_NOT_EMPTY(error_message='Project summary must be filled in')
                      ]),

                Field('longdescription',
                      label='Description',
                      type='text',
                      requires=[
                          IS_NOT_EMPTY(error_message='Project description must be filled in')
                      ]),

                Field('story',
                      label='Project Story',
                      type='text',
                      requires=[
                          IS_NOT_EMPTY(error_message='Project story must be filled in')
                      ]),

                Field('goal',
                      label='Funding Goal',
                      type='decimal(10,2)',
                      requires=[
                          IS_DECIMAL_IN_RANGE(minimum=100,
                                              error_message="Please enter a project goal greater than &pound;100"),
                          IS_DECIMAL_IN_RANGE(maximum=10 ** 8,
                                              error_message="Your project goal is too optimistic. Please chose a lower goal"),
                      ]),

                Field('categoryid',
                      type='reference category',
                      label='Category',
                      requires=IS_IN_DB(db, db.category.idcategory, '%(name)s',
                                        zero='Select A Category',
                                        error_message='Please choose a category'
                      )
                ),

                Field('managerid',
                      type='reference user',
                      requires=IS_IN_DB(db, db.user.iduser),
                      default=auth.user_id,
                      readable=False,
                      writable=False
                ),

                Field('imageurl', type='upload', label="Project Image", autodelete=True, required=[
                    IS_IMAGE(error_message="File must be image"),
                    IS_NOT_EMPTY(error_message="Please choose an image")]),


                Field.Method('isopen', lambda row: db(db.openproject.projectid == row.project.idproject).count() > 0),
                Field.Method('isclosed',
                             lambda row: db(db.closedproject.openprojectid == row.project.idproject).count() > 0),
                Field.Method('isfunded', lambda row: db(
                    db.projectstat.idproject == row.project.idproject).select().first().funded > 0),


                Field.Method('canopen',     lambda row: auth.user_id == row.project.managerid and (not row.project.isopen() or (row.project.isclosed() and not row.project.isfunded()))),
                Field.Method('canclose',    lambda row: auth.user_id == row.project.managerid and row.project.isopen() and not row.project.isclosed()),
                Field.Method('candelete',   lambda row: auth.user_id == row.project.managerid and (not row.project.isopen() or row.project.isclosed())),
                Field.Method('canedit',     lambda row: auth.user_id == row.project.managerid and not row.project.isopen()),
                Field.Method('canpledge',   lambda row: row.project.isopen() and not row.project.isclosed()),

                Field.Method('state', lambda row: ("Not Available" if not row.project.isopen()
                                                   else ("Open" if not row.project.isclosed()
                                                         else("Funded" if row.project.isfunded()
                                                              else "Not funded")))),

                Field.Method('hascontributed', lambda row: db((db.booting.openprojectid == row.project.idproject) & (
                db.booting.userid == auth.user_id)).count() > 0),
                Field.Method('pledges',
                             lambda row: db((db.pledge.projectid == row.project.idproject) & joinpledgestats).select(
                                 db.pledge.ALL, db.pledgestat.ALL, orderby=db.pledge.value)),
                Field.Method('expectedrewards', lambda row: groupby(db(
                    (db.expectedrewards.projectid == row.project.idproject) & (
                    db.user.id == db.expectedrewards.userid)).select(db.expectedrewards.ALL, db.user.ALL),
                                                                    key=lambda item: item.user.username)),
                Field.Method('rewards', lambda row: db(db.reward.projectid == row.project.idproject).select()),
                Field.Method('rawdelete', lambda row:
                    db.executesql('DELETE FROM project WHERE idproject={0}'.format(row.project.idproject,
                                                                                        )))
)

"""
Reward
Fields: IdReward (integer) PRIMARY KEY AUTO INCREMENT, Description (text), ProjectId (project)

Nothing interesting here, project ID is set to reference the project. added a validator to ensure that the project
exists, but this is already handled through the FK constraint in the DB.

FK constraint is to cascade on delete as projects can be deleted, all rewards/pledges should be deleted too



CREATE TABLE Reward (
    IdReward    INTEGER         PRIMARY KEY AUTOINCREMENT
                                NOT NULL,
    Description VARCHAR( 120 )  NOT NULL,
    ProjectId   INTEGER         NOT NULL
                                REFERENCES Project ( IdProject ) ON DELETE CASCADE
                                                                 ON UPDATE CASCADE
);


"""
db.define_table('reward',
                Field('idreward', type='id', readable=False, writable=False, default=None),
                Field('description', type='text', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter a description'),
                    IS_LENGTH(maxsize=120, error_message='Maximum length of pledge description is 120 characters')
                ]),
                Field('projectid', type='reference project', requires=IS_IN_DB(db, db.project.idproject),
                      readable=False, writable=False),
                Field.Method('rawdelete', lambda row:
                    db.executesql('DELETE FROM reward WHERE idreward={0}'.format(row.reward.idreward,
                                                                                        ))))



"""
Pledge
Fields: IdPledge (integer) PRIMARY KEY AUTO INCREMENT, Description (text), ProjectId (project)
Computed: Rewards (returns list of rewards that are linked to this pledge) - not sure if this actually used any more as
            this effectively will query the DB for every pledge. Instead the app now selects pledges inner joined with
            rewards and performs the grouping in software using python's built in group by.


Value is set to numeric for reasons already stated.
FK constraint is to cascade on delete as projects can be deleted, all rewards/pledges should be deleted too


CREATE TABLE Pledge (
    IdPledge    INTEGER           PRIMARY KEY AUTOINCREMENT
                                  NOT NULL,
    Description VARCHAR( 60 )     NOT NULL,
    Value       NUMERIC( 10, 2 )  NOT NULL,
    ProjectId   INTEGER           NOT NULL
                                  REFERENCES Project ( IdProject ) ON DELETE CASCADE
                                                                   ON UPDATE CASCADE
);


"""
db.define_table('pledge',
                Field('idpledge', type='id', readable=False, writable=False, default=None),
                Field('description', type='text', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter a description'),
                    IS_LENGTH(maxsize=60, error_message='Maximum length of pledge description is 60 characters')
                ]),
                Field('value', type='decimal(10,2)', requires=[
                    IS_DECIMAL_IN_RANGE(minimum=1, error_message='Please enter a suitable value for this pledge level'),
                    IS_DECIMAL_IN_RANGE(maximum=10000,
                                        error_message='The chosen pledge value is too high. Crowd funding relies on lots of people pledging small amounts. Why not choose something a bit lower?')
                ], filter_out=lambda value: int(math.ceil(value))),
                Field('projectid', type='reference project', label='Project', writable=False, readable=False,
                      requires=IS_IN_DB(db, db.project.idproject)),
                Field.Method('rewards', lambda row:
                db((db.rewardpledge.pledgeid == row.pledge.idpledge) & (
                db.reward.idreward == db.rewardpledge.rewardid)).select(db.reward.ALL)),
                Field.Method('rewardids', lambda row: map(lambda r: r.rewardid,
                                                          db((db.rewardpledge.pledgeid == row.pledge.idpledge)).select(
                                                              db.rewardpledge.rewardid))))


"""
RewardPledge
Fields: RewardId (Reward) PK, PledgeId (Pledge) PK.

The rewardid and pledgeid fields originally were set to reference the reward and pledge tables. however, web2py is unable
to handle a deletion from these tables as it attempts to do the job of the database and cascade the deletion, however as
rewardpledge is a weak entity and doesn't have a single value as the primary key, web2py borks and is unable to delete
a pledge or reward

the referential integrity is maintained by the database in this instance. as web2py is not generating the DDL
(migrations=False is set), this isn't an issue


CREATE TABLE RewardPledge (
    RewardId INTEGER NOT NULL,
    PledgeId INTEGER NOT NULL,
    PRIMARY KEY ( RewardId, PledgeId ),
    UNIQUE ( RewardId, PledgeId ),
    FOREIGN KEY ( RewardId ) REFERENCES Reward ( IdReward ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE,
    FOREIGN KEY ( PledgeId ) REFERENCES Pledge ( IdPledge ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE
);

"""
db.define_table('rewardpledge',
                Field('rewardid', type='integer', requires=IS_IN_DB(db, db.reward.idreward, '%(description)s')),
                Field('pledgeid', type='integer',
                      requires=IS_IN_DB(db, db.pledge.idpledge, '?%(value)s %(description)s')),
                Field.Method('rawdelete', lambda row:
                    db.executesql('DELETE FROM rewardpledge WHERE rewardid={0} AND pledgeid={1}'.format(row.rewardpledge.rewardid,
                                                                                          row.rewardpledge.pledgeid))),
                primarykey=['rewardid', 'pledgeid'])



"""
OpenProject

OpenProject is used to record when a project is opened. The project's IsOpen method is computed by checking whether
a record exists in openproject for the projectid.

As the web2py DAL doesnt support a foreign key that is also a primary key, primary key is specified as a kwarg.


CREATE TABLE OpenProject (
    ProjectId INTEGER  PRIMARY KEY
                       NOT NULL
                       REFERENCES Project ( IdProject ) ON DELETE CASCADE
                                                        ON UPDATE CASCADE,
    OpenDate  DATETIME NOT NULL
);
"""
db.define_table('openproject',
                Field('projectid', type='reference project', requires=IS_IN_DB(db, db.project.idproject)),
                Field('opendate', type='datetime', default=current.request.now),
                primarykey=['projectid'])

"""
ClosedProject

Closedproject records the closure of a project in the same regard as OpenProject. Projects can be reopened by deleting
the closedroject.



CREATE TABLE ClosedProject (
    OpenProjectId INTEGER  PRIMARY KEY
                           NOT NULL
                           REFERENCES OpenProject ( ProjectId ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE,
    ClosedDate    DATETIME NOT NULL
);

"""
db.define_table('closedproject',
                Field('openprojectid', type='reference openproject', requires=IS_IN_DB(db, db.openproject.projectid)),
                Field('closeddate', type='datetime', default=current.request.now),
                primarykey=['openprojectid'])



"""
Booting
Fields: BootingDate (datetime), UserId (User), OpenProjectId (OpenProject), PledgeId (Pledge), AddressId(Addres) CardId(card)

AddressId and CardId fields use the IS_IN_DB validator to generate the address/card dropdowns that are shown on the
make pledge page. However, these are not explicitly set to reference address/card tables.

UserID is always computed to be the current users ID.

BootingDate is auto-generated to be the date that this record was entered. This might come in handy if producing an account
ledger.



CREATE TABLE Booting (
    UserId        INTEGER  NOT NULL
                           REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                      ON UPDATE CASCADE,
    OpenProjectId INTEGER  NOT NULL
                           REFERENCES OpenProject ( ProjectId ) ON DELETE CASCADE
                                                                ON UPDATE CASCADE,
    CardId        INTEGER  REFERENCES Card ( IdCard ) ON DELETE SET NULL
                                                      ON UPDATE CASCADE,
    AddressId     INTEGER  REFERENCES Address ( IdAddress ) ON DELETE SET NULL
                                                            ON UPDATE CASCADE,
    BootingDate   DATETIME NOT NULL,
    PledgeId      INTEGER  NOT NULL
                           REFERENCES Pledge ( IdPledge ) ON DELETE CASCADE
                                                          ON UPDATE CASCADE,
    PRIMARY KEY ( UserId, OpenProjectId ),
    FOREIGN KEY ( UserId ) REFERENCES User ( IdUser ) ON DELETE RESTRICT
                                                          ON UPDATE CASCADE,
    FOREIGN KEY ( OpenProjectId ) REFERENCES OpenProject ( ProjectId ) ON DELETE CASCADE
                                                                           ON UPDATE CASCADE
);

"""
db.define_table('booting',
                Field('userid', type='reference user', default=auth.user_id, readable=False, writable=False),
                Field('openprojectid', type='reference openproject', readable=False, writable=False),
                Field('pledgeid', type='reference pledge', readable=False, writable=False),
                Field('addressid', type='reference address', label="Delivery Address", ondelete='SET NULL',
                      requires=IS_IN_DB(db(db.address.userid == auth.user_id), db.address.idaddress, '%(street)s, %(city)s, %(postcode)s',
                                        zero='Select Delivery Address')),
                Field('cardid', type='reference card', label="Payment Card",ondelete='SET NULL',
                      requires=IS_IN_DB(db(db.card.userid == auth.user_id), db.card.idcard, '%(number)s',
                                        zero='Select Payment Card')),
                Field('bootingdate', type='datetime', readable=False, writable=False, default=current.request.now),
                primarykey=['userid','openprojectid'],
            )








"""
CREATE VIEW PledgeStat AS
       SELECT IdPledge,
              ProjectId,
              Description,
              Value,
              COUNT( UserId ) AS PledgeCount,
              COUNT( UserId ) * Value AS TotalValue
         FROM Pledge
              LEFT JOIN Booting
                     ON Pledge.IdPledge = Booting.PledgeId
        GROUP BY Pledge.IdPledge;
;
"""
db.define_table('pledgestat',
                Field('idpledge', type='id'),
                Field('projectid', type='integer'),
                Field('value', type='decimal(10,2)'),
                Field('pledgecount', type='integer'),
                Field('totalvalue', type='decimal(10,2)'))



"""
ExpectedRewards

Returns a list of rewards that have been generated as a result of pledges made to a project.
This is used in 2 cases:
    firstly, the list of expected rewards on the user account page (select expected rewards where userid = auth.user)
    secondly, the list of pledges on the view proejct page (select expected rewards where projectid = project)



CREATE VIEW ExpectedRewards AS
       SELECT Pledge.ProjectId AS ProjectId,
              Booting.UserId AS UserId,
              Booting.PledgeId AS PledgeId,
              Pledge.Description AS PledgeDescription,
              Pledge.Value AS Value,
              Reward.IdReward AS RewardId,
              Reward.Description AS RewardDescription
         FROM Booting
              INNER JOIN Pledge
                      ON Pledge.IdPledge = Booting.PledgeId
              INNER JOIN RewardPledge
                      ON RewardPledge.PledgeId = Booting.PledgeId
              INNER JOIN Reward
                      ON RewardPledge.RewardId = Reward.IdReward;
;
"""
db.define_table('expectedrewards',
                Field('userid', type='reference user'),
                Field('projectid', type='reference project'),
                Field('rewardid', type='reference reward'),
                Field('pledgeid', type='reference pledge'),
                Field('rewarddescription'),
                Field('pledgedescription'),
                Field('value', type='decimal(10,2)', filter_out=lambda value: int(math.ceil(value))),
                primarykey=['userid', 'projectid'])



"""
Project Stats

Generates stats for projects such as progress, total value, number of bootings, remaining value etc.
Left join is used so that this can return a value even if a project has not received any bootings yet.

This is normally joined to the project using inner join. This is used throughout the application (in fact, almost
anywhere a project is displayed. Using a view is much simpler than using web2py's DAL to compute the project statistics.


CREATE VIEW ProjectStat AS
       SELECT IdProject,
              Goal,
              CAST ( IFNULL( CAST ( SUM( TotalValue )  AS Float ) / goal * 100, 0 )  AS Integer ) AS Progress,
              MIN( 100, CAST ( IFNULL( CAST ( SUM( TotalValue )  AS Float ) / goal * 100, 0 )  AS Integer )  ) AS LimitedProgress,
              IFNULL( SUM( TotalValue ) >= Goal, 0 ) AS Funded,
              IFNULL( SUM( TotalValue ) , 0 ) AS TotalValue,
              IFNULL( SUM( PledgeCount ) , 0 ) AS Bootings,
              Goal - IFNULL( SUM( TotalValue ) , 0 )  Remaining
         FROM Project
              LEFT OUTER JOIN PledgeStat
                           ON Project.IdProject == PledgeStat.ProjectId
        GROUP BY IdProject;
;
"""
db.define_table('projectstat',
                Field('idproject', type='id'),
                Field('goal', type='decimal(10,2)'),
                Field('progress', type='integer'),
                Field('limitedprogress', type='integer'),
                Field('funded', type='integer'),
                Field('bootings'),
                Field('totalvalue', type='decimal(10,2)'),
                Field('remaining', type='decimal(10,2)')
)




"""
Query clauses, these are used throughout the project pages
"""
closedprojects = (db.project.idproject.belongs(db()._select(db.closedproject.openprojectid)))
current.closedprojects = closedprojects

openprojects = (db.project.idproject.belongs(db()._select(db.openproject.projectid)))
current.openprojects = openprojects

notstartedprojects = (~openprojects & ~closedprojects)
current.notstartedprojects = notstartedprojects





fundedprojects = (db.projectstat.funded == 1)
current.fundedprojects = fundedprojects

notfundedprojects = (db.projectstat.funded == 0)
current.notfundedprojects = notfundedprojects






searchableprojects = (openprojects | closedprojects)
current.searchableprojects = searchableprojects

myprojects = (db.project.managerid == auth.user_id)
current.myprojects = myprojects






joinopenproject = (db.project.idproject == db.openproject.projectid)
current.joinopenproject = joinopenproject

joinprojectstats = (db.project.idproject == db.projectstat.idproject)
current.joinprojectstats = joinprojectstats

joinpledgestats = (db.pledge.idpledge == db.pledgestat.idpledge)
current.joinpledgestats = joinpledgestats

joinmanager = (db.user.iduser == db.project.managerid)
current.joinmanager = joinmanager



db.category.projects = Field.Method(lambda row: db((db.project.categoryid == row.category.idcategory) & searchableprojects & joinprojectstats & joinopenproject & (
        db.project.managerid == db.user.iduser)).select(db.project.ALL, db.user.ALL, db.projectstat.ALL,
                                                        db.openproject.ALL, orderby=~db.openproject.opendate))


"""
Address Query bits.
"""
myaddresses = (db.address.userid == auth.user_id)
current.myaddresses = myaddresses

joincountry = (db.country.code == db.address.countrycode)
current.joincountry = joincountry


"""
Card Query bits.
"""
mycards = (db.card.userid == auth.user_id)
current.mycards = mycards


"""
Pledges
"""
joinprojectpledges = (db.project.idproject == db.pledge.projectid)
current.joinprojectpledges = joinprojectpledges




"""
Once DB is initialised check account integrity
"""

auth.force_integrity()