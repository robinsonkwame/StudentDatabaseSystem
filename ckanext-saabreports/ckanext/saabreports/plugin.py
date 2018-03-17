#
#	Plugin and controllers
#

import ckan.plugins as p
import ckan.plugins.toolkit as tk
import sqlalchemy as sql
import logging
import uuid
import re
import db

from ckan import model, common, logic
from ckan.lib.helpers import full_current_url
from ckan.lib.dictization import model_dictize
from routes import mapper

from schema_constants import *

log = logging.getLogger(__name__)

#	Return all chapters the user in ctx
#	is an admin of
def get_authorized_chapters(ctx):
	user = model.User.get(ctx['user'])
	if user.sysadmin:
		#	Return all chapters
		chapter_objs = model.Session.query(model.Group).filter(sql.and_(model.Group.is_organization, 
				model.Group.state == 'active')).all()
		return [tk.get_action('organization_show')(ctx, {
				'id': chapter_obj.id
			}) for chapter_obj in chapter_objs]
	else:
		#	Return whatever chapters they are admin of
		return tk.get_action('organization_list_for_user')(ctx, {})

#	Return all students in any of the
#	given chapters
def get_students_in(ctx, chapters):
	#	Collect all
	student_objs = model.Session.query(model.Package).filter(model.Package.type == 'student',
			model.Package.state == 'active').all()
	students = [tk.get_action('package_show')(ctx, {
		'id': student_obj.id
	}) for student_obj in student_objs]
	#	Get chapter ids
	chapter_ids = [chapter['id'] for chapter in chapters]
	#	Return all students in one of the chapters
	in_a_chapter = lambda student: 'owner_org' in student and student['owner_org'] in chapter_ids
	return [student for student in students if in_a_chapter(student) ]

#	Return all semesters for the given
#	students
def get_semesters_for(students):
	data = []
	for student in students:
		resources = student['resources']
		if resources is not None and len(resources) > 0:
			for resource in resources:
				resource['student'] = student['title']
				data.append(resource)
	return data

#	Turn a list of dicts into a CSV
def csv(items, keys=None):
	#	Helper
	safe_str = lambda obj: str(obj).encode('utf-8').replace(',', '&#44;')
	
	#	Maybe filter keys
	if keys is None:
		keys = sorted([key for key in items[0].keys() if key not in EXCLUDES])
	#	Title row
	csv_data = [[key.encode('utf-8') for key in keys]]
	
	#	Make content rows
	for item in items:
		row = []
		for key in keys:
			if key in item:
				if key == 'organization':
					try:
						row.append(safe_str(item['organization']['title']))
					except:
						row.append('Not found')
				else:
					row.append(safe_str(item[key]))
			else:
				row.append('Not found')
		csv_data.append(row)

	#	Make string
	return '\n'.join([','.join(row) for row in csv_data])

#	Actually create a report and 
#	send the user to it
def create_report(ctx, report_name, report_type, csv_str):
	#	Save report to table
	report = db.Report(report_name, csv_str)
	report.save()

	#	Create dataset
	ctx['return_id_only'] = True
	dataset_id = tk.get_action('package_create')(ctx, {
		'name': uuid.uuid4(),
		'title': report_name,
		'type': 'saabreport',
		'schema': 'saabreport',
		'author': ctx['user']
	})

	#	Create resource
	new_path = '/get_report?report_id=%s'%report.id
	tk.get_action('resource_create')(ctx, {
		'url': full_current_url().replace('/create_report', new_path).replace('/create_chapter_report', new_path),
		'package_id': dataset_id,
		'description': 'Generated %s report'%report_type,
		'type': 'text/csv',
		'format': 'csv'
	})
	tk.redirect_to(controller='package', action='read', id=dataset_id)

class SaabReportsPlugin(p.SingletonPlugin):
	p.implements(p.IConfigurer)
	p.implements(p.IRoutes)
	
	def __init__(self, **kwargs):
		db.setup()

	def update_config(self, config):
		tk.add_template_directory(config, 'templates')
		tk.add_public_directory(config, 'public')
		return config
		
	def before_map(self, route_map):
		with mapper.SubMapper(route_map, controller='ckanext.saabreports.plugin:SaabReportsController') as m:
			m.connect('create_report', '/create_report', action='create_report')
			m.connect('get_report', '/get_report', action='get_report')
		return route_map
		
	def after_map(self, route_map):
		return route_map

class SaabReportsController(tk.BaseController):

	def create_report(self):
		req = tk.request.POST
		ctx = {
			'model': model,
			'session': model.Session,
			'user': tk.c.user,
			'auth_user_obj': tk.c.userobj
		}

		#	Make life easier
		page_vars = {}
		def render_page():
			return tk.render('create_report.html', extra_vars=page_vars)

		#	Figure out what chapters the user can see
		chapters = get_authorized_chapters(ctx)
		page_vars['saabreports_all_chapters'] = chapters	#	This is the display chapters

		#	Base auth check
		if len(chapters) == 0:
			#	Not authorized to see anything
			page_vars['saabreports_authorized'] = False
			return render_page()
		page_vars.update({
			'saabreports_authorized': True,
			'saabreports_missing_semester': SEMESTER_MISSING_FIELDS,
			'saabreports_missing_student': MEMBERSHIP_MISSING_FIELDS
		})

		#	Maybe filter chapters if buddy
		#	has hella privs
		if 'form_id' in req and req['form_id'] == 'chapter_selection':
			choice = req['chapter']
			page_vars['chapter_choice'] = choice
			page_vars['chapter_choice_display'] = 'All' if choice == '__all__' else choice
			if choice != '__all__':
				for chapter in chapters:
					if chapter['id'] == choice:
						page_vars['chapter_choice_display'] = chapter['title']
						chapters = [chapter]
						break
			page_vars['saabreports_chapters'] = chapters

		#	Collect student list 
		students = get_students_in(ctx, chapters)
		#	Collect semester list
		semesters = get_semesters_for(students)
		#	Make students look nicer
		for student in students:
			if 'first_name' in student and 'student_middle_name' in student and 'last_name' in student:
				full_name = '%s %s %s'%(student['first_name'], student['student_middle_name'], student['last_name'])
				student['title'] = re.sub(r'\s+', ' ', full_name)
		page_vars['saabreports_students'] = students
		
		#	This one is for the semester filter in custom
		semester_names = []
		for semester in semesters:
			if 'name' in semester and semester['name'] not in semester_names:
				semester_names.append(semester['name'])
		page_vars['saabreports_semester_names'] = semester_names

		if 'form_id' not in req:
			return render_page()
		#	---- Report request below here
		form_id = req['form_id']

		#	Setup for errors
		#	TODO: Save values
		def render_error(desc):
			page_vars['%s_error'%form_id] = desc
			return render_page()

		#	Assert name exists
		if 'report_name' not in req or len(req['report_name']) == 0:
			return render_error('Please supply a report name')
		report_name = req['report_name']

		#	Assert dataset selected if required
		if form_id in ['student', 'custom'] and 'dataset_type' not in req:
			return render_error('Please select a dataset type')

		#	Do form specific ag.
		if form_id == 'student':
			if 'student' not in req:
				return render_error('Please select a student')
			#	Find the student and semester
			student_id = req['student']
			if student_id != '__all__':
				for check in students:
					if check['id'] == student_id:
						students = [check]
						semesters = get_semesters_for(students)
						break
			#	Make dat CSV
			csv_str = csv(semesters if req['dataset_type'] == 'semester' else students)
		else:
			#	Get chapter choice, if there wasn't
			#	one either we didn't ask (only one
			#	option), or the selector is still on
			#	default (all)
			if 'chapter_choice' in req:
				chapter_id = req['chapter_choice']
				if chapter_id != '__all__':
					#	Filter students and semesters
					chapter_students = []
					for student in students:
						log.warning(student['owner_org'] + ' VS ' + chapter_id)
						if student['owner_org'] == chapter_id:
							chapter_students.append(student)
					students = chapter_students
					semesters = get_semesters_for(students)
			if form_id == 'chapter_activity':
				#	Make dat CSV
				csv_str = csv(semesters, keys=ACTIVITY_REPORT_FIELDS)
			elif form_id == 'chapter_member':
				#	Make dat CSV
				csv_str = csv(students)
			elif form_id == 'custom':
				is_student = req['dataset_type'] == 'membership'
				name, set = ('students', students) if is_student else ('semesters', semesters)
				
				#	Filter helper
				def _filter(set, cond):
					return [item for item in set if cond(item)]
				
				#	Filter missing
				to_check = []
				for key in req:
					if key.startswith('saabreports_missing_'):
						to_check.append(key[20:])
				for key in to_check:
					set = _filter(set, lambda item: key not in item or len(item[key].strip()) == 0)
				
				if not is_student:
					#	Filter GPA
					min_gpa = float(req['filter_gpa_min'])
					max_gpa = float(req['filter_gpa_max'])
					def in_range(sem):
						if 'overall_gpa' not in sem:
							return False
						gpa = float(sem['overall_gpa'])
						return min_gpa <= gpa and max_gpa >= gpa
					set = _filter(set, in_range)

					#	Filter name
					semester_name = req['semester']
					if semester_name != '__all__':
						set = _filter(set, lambda sem: 'name' in sem and sem['name'] == semester_name)

				if len(set) == 0:
					return render_error('No %s match your query'%name)
				
				csv_str = csv(set)

			else: pass # There is no else
		
		#	Store report and redirect to
		create_report(ctx, report_name, REPORT_TYPES[form_id], csv_str)
		#	This is unreachable unless uuid
		#	fails which it never will

	def get_report(self):
		#	Return a CSV
		#	TODO: auth check even though good luck guessing
		tk.response.headers['Content-Type'] = bytes('text/csv; charset=utf-8')
		report = db.Report.get(tk.request.GET['report_id'])
		tk.response.headers['Content-Disposition'] = bytes('attachment; filename=%s.csv'%report.name)
		return bytes(report.csv.encode('utf-8'))
