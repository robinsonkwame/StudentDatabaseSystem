#
#	Plugin and registration controller
#

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from routes import mapper
import urllib
import random
import logging
import db

from ckan import model, logic
from ckan.lib import helpers
from ckan.common import session
from ckan.lib.dictization import model_dictize

log = logging.getLogger(__name__)

#	Gets the username of the dataset owner when creating
#	or viewing a student dataset
def _get_dataset_owner():
	if 'student/new' in tk.request.path:
		#	Dataset being created
		return tk.c.user
	else:
		#	Dataset being viewed
		return tk.request.path.split('/')[-1]

#	Passed to templates to populate selector options
def get_organization_options(sort_on_user=False):
	orgs = model.Session.query(model.Group).filter(model.Group.is_organization).filter(model.Group.state == 'active').all()
	orgs = [{
		'text': ' '.join(org.name.split('-')).title(),
		'value': org.name
	} for org in orgs]
	if sort_on_user:
		#	Move the correct organization to front
		owner_org_id = db.UserOrgRelation.get(model.User.get(_get_dataset_owner()).id).org_id
		owner_org = model.Group.get(owner_org_id).name
		j = 0
		for i, org in enumerate(orgs):
			if org['value'] == owner_org:
				j = i
				break
		orgs.insert(0, orgs.pop(j))
	return orgs

class SaabRegPlugin(p.SingletonPlugin):
	p.implements(p.IAuthFunctions)
	p.implements(p.IActions)
	p.implements(p.ITemplateHelpers)
	p.implements(p.IAuthenticator)
	p.implements(p.IConfigurer)
	p.implements(p.IRoutes)
	
	def __init__(self, name=None):
		#	Maybe set up UserOrgRelation
		db.setup(populate=tk.config.get('ckan.saabreg.auto_populate', True))
		
		#	Not implemented
		self.after_map = lambda x: x
	
	def update_config(self, config):
		tk.add_template_directory(config, 'templates')
		tk.add_public_directory(config, 'public')
		return config
	
	def before_map(self, route_map):
		with mapper.SubMapper(route_map, controller='ckanext.saabreg.plugin:SaabRegController') as m:
			m.connect('register', '/user/register', action='register')
		return route_map
	
	def get_helpers(self):
		#	Returns basic information on a dataset owner for
		#	field autofill
		def get_user_info():
			user = model.User.get(_get_dataset_owner())
			first, last = user.fullname.split(' ')
			return {
				'username': user.name,
				'first_name': first,
				'last_name': last
			}
	
		return {
			'saabreg_get_user_info': get_user_info,
			'saabreg_get_organization_options': get_organization_options
		}
	
	def get_actions(self):
		#	Show students only their parent organization
		def organization_list_for_user(ctx, data_dict=None):
			user = model.User.get(ctx['user'])
			if user is None:
				return []
			
			#	We have too
			logic.check_access('organization_list_for_user', ctx, data_dict)
			
			rel = db.UserOrgRelation.get(user.id)
			if rel is None:
				#	Not a student, revert
				return logic.action.get.organization_list_for_user(ctx, data_dict)
			
			org_list = [model.Group.get(rel.org_id)]
			pkg_count_flag = tk.asbool(data_dict.get('include_dataset_count', 'false'))
			return model_dictize.group_list_dictize(org_list, ctx, with_package_counts=pkg_count_flag)
		
		return {
			'organization_list_for_user': organization_list_for_user
		}
		
	def get_auth_functions(self):
		#	Allow students to create a single package. Since students can only
		#	add to their organization, no need to check
		def package_create(ctx, data_dict=None):
			user = model.User.get(ctx['user'])
			if user is None or db.UserOrgRelation.get(user.id) is None:
				#	Not a student, revert
				return logic.auth.create.package_create(ctx, data_dict)
			dataset_exists = model.Package.get(user.name) is not None
			if data_dict is None:
				#	Pass pre-check
				return {
					'success': not dataset_exists
				}
			if 'name' not in data_dict:
				#	We need the name to authorize
				return {
					'success': False
				}
			if data_dict['name'] != user.name:
				#	Must share a name
				return {
					'success': False
				}
			return {
				'success': not dataset_exists
			}
		
		#	Only allow students to see their own dataset
		def package_show(ctx, data_dict=None):
			user = model.User.get(ctx['user'])
			if user is None or db.UserOrgRelation.get(user.id) is None:
				#	Not a student, revert
				return logic.auth.create.package_show(ctx, data_dict)
			#	Damn you Python 2...
			if 'id' in data_dict:
				dataset_ref = data_dict['id']
			else:
				dataset_ref = data_dict['name_or_id']
			return {
				'success': user.name == model.Package.get(dataset_ref).name
			}
		
		#	Only allow students to add a dataset to their organization once
		def organization_update(ctx, data_dict=None):
			user = model.User.get(ctx['user'])
			if user is None or db.UserOrgRelation.get(user.id) is None:
				#	Not a student, revert
				return logic.auth.update.organization_update(ctx, data_dict)
			return {
				'success': model.Package.get(user.name) is None
			}
		
		#	This is fine since visibility is restricted
		def package_update(context, data_dict=None):
			return {
				'success': True
			}
		
		return {
			'package_create': package_create,
			'package_show': package_show,
			'package_update': package_update,
			'organization_update': organization_update
		}
	
	def identify(self):
		#	Handle auth. for the first session
		if 'saabreg_new_user' in session:
			tk.c.user = session['saabreg_new_user']
			session['saabreg_user'] = session['saabreg_new_user']
			del session['saabreg_new_user']
			session.save()
		elif 'saabreg_user' in session:
			tk.c.user = session['saabreg_user']
			
	def login(self):
		if 'saabreg_user' in session:
			if 'saabreg_not_student' in session:
				#	Revert
				del session['saabreg_not_student']
				session.save()
				tk.h.redirect_to(controller='user', action='me')
			else:
				#	Redirect to dataset creation
				tk.h.redirect_to('/student/new')
		
	def logout(self):
		if 'saabreg_user' in session:
			#	Remove session
			del session['saabreg_user']
			session.save()

	def abort(self, status_code, detail, headers, comment): pass

class SaabRegController(tk.BaseController):
	
	def register(self):
		vars = {
			'form_data': {
				'org_list': get_organization_options()
			}
		}
		def render_page():
			tk.c.form = tk.render('user/new_user_form.html', extra_vars=vars)
			return tk.render('user/new.html')
		
		if 'is_student' not in tk.request.POST:
			#	Not a form request
			return render_page()
		
		#	So template can refill form on error
		vars['form_data'].update(tk.request.POST)
		#	Parse request
		is_student = tk.request.POST['is_student'] == '1'
		first_name = tk.request.POST['first_name']
		last_name = tk.request.POST['last_name']
		email_addr = tk.request.POST['email']
		password = tk.request.POST['password']
		confirm_password = tk.request.POST['confirm_password']
		chapter = tk.request.POST['chapter']
		
		#	Validate
		#	TODO: Use CKAN validation method
		class ValidationError(BaseException): pass
		def validate(flag, error):
			if flag:
				vars['error_summary'] = {'': error}
				raise ValidationError
		
		try:
			validate(len(first_name) == 0 or len(last_name) == 0, 'Please provide your first and last name.')
			validate(len(email_addr) == 0, 'Please provide your email address.')
			validate(len(model.User.by_email(email_addr)) > 0, 'The email you provided is already associated with an account.')
			validate(len(password) == 0 or len(confirm_password) == 0, 'Please complete both password fields.')
			validate(password != confirm_password, 'The passwords you supplied do not match.')
			validate(model.Group.get(chapter) is None, 'The chapter you supplied does not exist (how did you do that?).')
		except ValidationError:
			return render_page()
		
		#	Create user
		if is_student:
			#	Generate unique name
			name_base = ('%s%s'%(first_name, last_name)).lower()
			
			def get_unique(tries_per=100):
				digits = 2
				while True:
					for n in range(tries_per):
						user_name = '%s%s'%(name_base, ''.join([str(random.randint(0, 9)) for k in range(digits)]))
						if model.User.get(user_name) is None:
							return user_name
					digits += 1
			
			user_name = get_unique()
		else:
			user_name = '%s%s'%(first_name, last_name)
		
		try:
			user = tk.get_action('user_create')({
				'model': model,
				'session': model.Session,
				'user': tk.c.user,
				'auth_user_obj': tk.c.userobj
			}, {
				'name': user_name,
				'email': email_addr,
				'fullname': '%s %s'%(first_name, last_name),
				'password': password
			})
		except Exception as e:
			vars['error_summary'] = str(e)
			return render_page()
		
		if is_student:
			#	Add organization relation
			db.UserOrgRelation(user['id'], model.Group.get(chapter).id).save()
		
		#	For the imminent authentication
		session['saabreg_new_user'] = user_name
		if not is_student:
			session['saabreg_not_student'] = True
		session.save()
		#	Redirect to login
		tk.h.redirect_to('../student/new')
