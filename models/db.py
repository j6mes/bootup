from itertools import groupby

db = DAL('sqlite://bootup.db',pool_size=1,check_reserved=['sqlite'],migrate=False)
auth = BootUpAuth(db)

db.define_table('category',
                Field('idcategory',type='id'),
                Field('name'),
                Field('url'))


db.define_table('user',
                Field('iduser', type='id', readable=False, writable=False, default=None),
                Field('realname',label='Name', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter your name'),
                    IS_LENGTH(maxsize=200, error_message='Please enter a shorter name'),

                ]),
                Field('username',label='Username',requires=[
                    IS_LENGTH(minsize=1, error_message='Please choose a username'),
                    IS_LENGTH(maxsize=60, error_message='Please chose a shorter username'),
                    IS_NOT_IN_DB(db,'user.username',error_message="Username is already taken")
                ]),
                Field('dateofbirth',type='date', label='Date of Birth', requires=[
                    IS_DATE(error_message='Please enter a date'),
                    #IS_DATE_IN_RANGE(error_message='Please enter a date in the recent past')
                ]),
                Field.Method('age', lambda row: request.now.year-row.dateofbirth.year
                    if (request.now.month, request.now.day) >= (row.dateofbirth.month, row.dateofbirth.day) else
                    request.now.year-row.dateofbirth.year-1),
                Field.Method('expectedrewards', lambda row: groupby(
                    db(
                        (db.expectedrewards.userid==row.user.iduser) &
                        (db.expectedrewards.projectid==db.project.idproject) &
                        (db.pledge.idpledge==db.expectedrewards.pledgeid) &
                        projectstats)
                    .select(db.expectedrewards.ALL,
                            db.project.ALL,
                            db.projectstat.ALL,
                            db.pledge.ALL

                            ),
                    key=lambda item:item.project.idproject))
)


#As primary key is a reference to user, the type='id' parameter cannot be set, use the primarykey= kwarg instead
db.define_table('credential',
                Field('userid',type='reference user', readable=False,writable=False),
                Field('passwordhash', writable=False, readable=False),
                Field('passwordsalt', writable=False, readable=False),
                primarykey=['userid']
    )


#There is a limitation with web2py that type='id' only supports integer types,
#as country code is a string, the primary key must be defined using the primarykey kwarg
db.define_table('country',
                Field('code'),
                Field('name'),
                primarykey=['code'])


#had to remove explicit reference to country code as for some reason web2py restricts all references to be numeric
#to maintain constraint, the IS_IN_DB validator is used
db.define_table('address',
                Field('idaddress',type='id', readable=False, writable=False),
                Field('street', label='Street', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter your street address'),
                    IS_LENGTH(maxsize=100, error_message='Please enter a shorter street address')
                ]),
                Field('city', label='City', requires=[
                    IS_LENGTH(minsize=1, error_message='Please enter your city'),
                    IS_LENGTH(maxsize=100, error_message='Please enter a shorter city name')
                ]),
                Field('postcode', label='Post Code', requires=[
                    IS_MATCH('[a-zA-Z0-9]{4} [a-zA-Z0-9]{3}',error_message='Postcode must be in the format XXXX XXX')
                ]),
                Field('countrycode',type='string', requires=IS_IN_DB(db, db.country.code,'%(name)s',
                                   zero='Select A Country',
                                   error_message='Please choose your country'
                                   )),
                Field('userid',type='reference user',
                      requires=IS_IN_DB(db,db.user.iduser),
                      readable=False, writable=False)
    )







db.define_table('project',
                Field('idproject',type='id',readable=False,writable=False),
                Field('title',
                      type='string',
                      label='Project Name',
                      requires= [
                        IS_LENGTH(60,error_message='Project title must be shorter than 60 characters'),
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
                          IS_DECIMAL_IN_RANGE(minimum=100,error_message="Please enter a project goal greater than &pound;100"),
                          IS_DECIMAL_IN_RANGE(maximum=10**8,error_message="Your project goal is too optimistic. Please chose a lower goal"),
                                ]),

                Field('categoryid',
                      type='reference category',
                      label='Category',
                      requires=IS_IN_DB(db, db.category.idcategory,'%(name)s',
                                   zero='Select A Category',
                                   error_message='Please choose a category'
                                   )
                ),

                Field('managerid',
                      type='reference user',
                      requires=IS_IN_DB(db,db.user.iduser),
                      default=auth.user_id,
                      readable=False,
                      writable=False
                      ),

                Field('imageurl',type='upload',label="Project Image",autodelete=True,required=[
                    IS_IMAGE(error_message="File must be image"),
                    IS_NOT_EMPTY(error_message="Please choose an image")]),

                Field.Method('canopen', lambda row:  auth.user_id==row.project.managerid and db(db.openproject.projectid==row.project.idproject).count()==0),
                Field.Method('canclose', lambda row: auth.user_id==row.project.managerid and db(db.openproject.projectid==row.project.idproject).count()==1 and db(db.closedproject.openprojectid==row.project.idproject).count()==0),
                Field.Method('candelete', lambda row: auth.user_id==row.project.managerid and (db(db.openproject.projectid==row.project.idproject).count()==0 or db(db.closedproject.openprojectid==row.project.idproject).count()==1)),
                Field.Method('canedit', lambda row: auth.user_id==row.project.managerid and db(db.openproject.projectid==row.project.idproject).count()==0),

                Field.Method('hascontributed', lambda row: db((db.booting.openprojectid==row.project.idproject) & (db.booting.userid == auth.user_id)).count() > 0),
                Field.Method('pledges', lambda row: db((db.pledge.projectid==row.project.idproject) & pledgestats).select(db.pledge.ALL,db.pledgestat.ALL, orderby=db.pledge.value)),
                Field.Method('expectedrewards', lambda row:  groupby(db((db.expectedrewards.projectid==row.project.idproject) & (db.user.id==db.expectedrewards.userid)).select(db.expectedrewards.ALL,db.user.ALL),key=lambda item:item.user.username)),
                Field.Method('rewards',lambda row: db(db.reward.projectid==row.project.idproject).select())
)

db.define_table('reward',
                Field('idreward',type='id', readable=False, writable=False, default=None),
                Field('description',type='text',requires=[
                    IS_LENGTH(minsize=1,error_message='Please enter a description'),
                    IS_LENGTH(maxsize=120, error_message='Maximum length of pledge description is 120 characters')
                ]),
                Field('projectid', type='reference project', requires=IS_IN_DB(db,db.project.idproject),readable=False,writable=False))



db.define_table('pledge',
                Field('idpledge', type='id', readable=False, writable=False, default=None),
                Field('description',type='text',requires=[
                    IS_LENGTH(minsize=1,error_message='Please enter a description'),
                    IS_LENGTH(maxsize=60, error_message='Maximum length of pledge description is 60 characters')
                ]),
                Field('value',type='decimal(10,2)',requires=[
                    IS_DECIMAL_IN_RANGE(minimum=1, error_message='Please enter a suitable value for this pledge level'),
                    IS_DECIMAL_IN_RANGE(maximum=10000, error_message='The chosen pledge value is too high. Crowd funding relies on lots of people pledging small amounts. Why not choose something a bit lower?')
                ]),
                Field('projectid', type='reference project', label='Project',writable=False, readable=False, requires=IS_IN_DB(db,db.project.idproject)),
                Field.Method('rewards',lambda row:
                    db((db.rewardpledge.pledgeid==row.pledge.idpledge)&(db.reward.idreward==db.rewardpledge.rewardid)).select(db.reward.ALL)),
                Field.Method('rewardids',lambda row: map(lambda r: r.rewardid, db((db.rewardpledge.pledgeid==row.pledge.idpledge)).select(db.rewardpledge.rewardid))))



#CAVEAT
#the rewardid and pledgeid fields originally were set to reference the reward and pledge tables. however, web2py is unable
#to handle a deletion from these tables as it attempts to do the job of the database and cascade the deletion, however as
#rewardpledge is a weak entity and doesn't have a single value as the primary key, web2py borks and is unable to delete
#a pledge or reward
#
#the referential integrity is maintained by the database in this instance. as web2py is not generating the DDL
#(migrations=False is set), this isn't an issue
#i hate web2py

db.define_table('rewardpledge',
                Field('rewardid',type='integer', requires=IS_IN_DB(db,db.reward.idreward,'%(description)s')),
                Field('pledgeid',type='integer', requires=IS_IN_DB(db,db.pledge.idpledge,'£%(value)s %(description)s')),
                Field.Method('rawdelete',lambda row: db.executesql('DELETE FROM rewardpledge WHERE rewardid={0} AND pledgeid={1}'.format(row.rewardpledge.rewardid,row.rewardpledge.pledgeid))),
                primarykey=['rewardid','pledgeid'])


db.define_table('pledgestat',
                Field('idpledge',type='id'),
                Field('projectid',type='integer'),
                Field('value',type='decimal(10,2)'),
                Field('pledgecount',type='integer'),
                Field('totalvalue',type='decimal(10,2)'))

db.define_table('expectedrewards',
                Field('userid',type='integer'),
                Field('projectid',type='integer'),
                Field('rewardid',type='integer'),
                Field('pledgeid',type='integer'),
                Field('rewarddescription'),
                Field('pledgedescription'),
                Field('value',type='decimal(10,2)'),
                primarykey=['userid','projectid'])

db.define_table('openproject',
                Field('projectid', type='reference project', requires=IS_IN_DB(db,db.project.idproject)),
                Field('opendate', type='datetime', default=request.now),
                primarykey=['projectid'])

db.define_table('closedproject',
                Field('openprojectid', type='reference openproject', requires=IS_IN_DB(db,db.openproject.projectid)),
                Field('closeddate',type='datetime', default=request.now),
                primarykey=['openprojectid'])






db.define_table('projectstat',
                Field('idproject', type='id'),
                Field('goal',type='decimal(10,2)'),
                Field('progress', type='integer'),
                Field('funded',type='integer'),
                Field('bootings'),
                Field('totalvalue',type='decimal(10,2)'),
                Field('remaining',type='decimal(10,2)')
                )

db.define_table('booting',
                Field('idbooting',type='id'),
                Field('userid', type='integer'),
                Field('openprojectid',type='integer'),
                Field('pledgeid',type='integer'))



myprojects = (db.project.managerid == auth.user_id)

closedprojects  = (db.project.idproject.belongs(db()._select(db.closedproject.openprojectid)))
openprojects    = (db.project.idproject.belongs(db()._select(db.openproject.projectid)))


includeopendate = (db.project.idproject==db.openproject.projectid)

notstartedprojects = (~openprojects & ~closedprojects)

projectstats = (db.project.idproject == db.projectstat.idproject)
pledgestats = (db.pledge.idpledge == db.pledgestat.idpledge)
fundedprojects = (db.projectstat.funded==1)
notfundedprojects = (db.projectstat.funded==0)

searchableprojects = (openprojects | closedprojects)
