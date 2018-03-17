#
#	UserOrgRelation associates students with their organization
#

import ckan.plugins.toolkit as tk
import ckan.model as model
import sqlalchemy as sql
import logging
import re

log = logging.getLogger(__name__)

class UserOrgRelationError(BaseException): pass

UserOrgRelation = None

def auto_populate():
	maybe_log = log.info if tk.config.get('ckan.saabreg.log_population', False) else lambda x: x
	maybe_log('Populating UserOrgRelation')
	
	#	Add all existing users to table
	user_id_list = model.Session.query(model.User.id, model.User.name).all()
	datasets = model.Session.query(model.Package.name, model.Package.owner_org).all()
	
	name_matcher = re.compile('[A-Za-z]+[0-9][0-9]+')
	for user_id, user_name in user_id_list:
		if not name_matcher.match(user_name):
			continue
		org_id = None
		for dataset_name, _org_id in datasets:
			if user_name == dataset_name:
				org_id = _org_id
				break
		if org_id is None:
			maybe_log('Exclude (%s); No dataset'%user_name)
			continue
		org_name = model.Group.get(org_id).name
		if UserOrgRelation.get(user_id) is None:
			maybe_log('Include (%s, %s)'%(user_name, org_name))
			UserOrgRelation(user_id, org_id).save()
		else:
			maybe_log('Exclude (%s, %s); User already related'%(user_name, org_name))

def setup(populate=False):
	global UserOrgRelation
	
	if UserOrgRelation is None:
		#	Need to define
		class _UserOrgRelation(model.DomainObject):
			
			def __init__(self, *args):
				if len(args) > 0:
					self.user_id, self.org_id = args
				
			@classmethod
			def get(self, user_id):
				return model.Session.query(UserOrgRelation).filter(UserOrgRelation.user_id == user_id).first()
		
		UserOrgRelation = _UserOrgRelation
		
		#	Define and maybe create
		user_org_table = sql.Table('saabreg_user_org_rel', model.meta.metadata,
			sql.Column('user_id', sql.ForeignKey('user.id'), primary_key=True),
			sql.Column('org_id', sql.ForeignKey('group.id'))
		)
		user_org_table.create(checkfirst=True)
		#	Map
		model.meta.mapper(UserOrgRelation, user_org_table)
		
		if populate:
			auto_populate()
