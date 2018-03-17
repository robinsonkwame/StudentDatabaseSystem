#
#	Table to hold generated reports
#

import sqlalchemy as sql
import uuid

from ckan import model

Report = None

def setup():
	global Report

	if Report is None:
		#	Need to define
		class _Report(model.DomainObject):

			def __init__(self, name, csv_str):
				self.id = uuid.uuid4().hex
				self.name = name
				self.csv = csv_str

			@classmethod
			def get(self, id):
				return model.Session.query(Report).filter(Report.id == id).first()

			def save(self):
				model.Session.add(self)
				model.Session.commit()

		Report = _Report

		#	Define table and maybe create
		report_table = sql.Table('saabreports_reports', model.meta.metadata,
			sql.Column('id', sql.Unicode, primary_key=True),
			sql.Column('name', sql.Unicode),
			sql.Column('csv', sql.Unicode)
		)
		report_table.create(checkfirst=True)
		#	Map
		model.meta.mapper(Report, report_table)