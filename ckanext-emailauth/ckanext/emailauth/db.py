#
#	Handles the auto login key table
#

import ckan.model as model
import sqlalchemy as sql
import datetime as dt
import logging

log = logging.getLogger(__name__)

AutoLoginKey = None

def setup():
	global AutoLoginKey
	
	if AutoLoginKey is None:
		#	Need to define
		class _AutoLoginKey(model.DomainObject):
			
			def save(self):
				model.Session.add(self)
				model.Session.commit()
			
			@classmethod
			def pop_key(cls, key, src_email):
				rows = model.Session.query(cls).filter(AutoLoginKey.key_digest == key).filter(AutoLoginKey.src_email == src_email)				
				row = rows.first()
				if row is None:
					return None	
				user_id = row.user_id
				rows.delete()
				model.Session.commit()
				
				return user_id
				
			@classmethod
			def remove_expired(cls, expiry_hrs):
				remove_before = dt.datetime.utcnow() - dt.timedelta(hours=expiry_hrs)
				model.Session.query(cls).filter(AutoLoginKey.timestamp < remove_before).delete()
				
		AutoLoginKey = _AutoLoginKey
		
		#	Define and maybe create
		auto_login_key_table = sql.Table('auto_login_key', model.meta.metadata,
			sql.Column('key_digest', sql.types.UnicodeText, primary_key=True),
			sql.Column('user_id', sql.ForeignKey('user.id')),
			sql.Column('timestamp', sql.types.DateTime, default=dt.datetime.utcnow),
			sql.Column('src_email', sql.types.UnicodeText)
		)
		auto_login_key_table.create(checkfirst=True)
		#	Map
		model.meta.mapper(AutoLoginKey, auto_login_key_table)
		