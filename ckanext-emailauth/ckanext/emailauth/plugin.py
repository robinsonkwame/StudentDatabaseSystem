#
#	Plugin and controller
#

import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.controllers.user as user_controller
import routes.mapper as mapper
import email.Utils as emailutils
import hashlib
import binascii
import urllib
import logging
import os
import db

from smtplib import SMTP
from email import MIMEMultipart, MIMEText
from ckan.common import session

log = logging.getLogger(__name__)
	
def send_login_email(email_addr, user_id):
	#	Generate key
	pure_login_key = binascii.hexlify(os.urandom(tk.asint(tk.config.get('ckan.emailauth.login_key_size', 20))))
	
	#	Record
	entry = db.AutoLoginKey()
	entry.key_digest = hashlib.sha256((pure_login_key + email_addr).encode('utf-8')).hexdigest()
	entry.user_id = user_id
	entry.src_email = email_addr
	entry.save()

	#	Generate content
	login_page = tk.config.get('ckan.site_url') + tk.url_for(controller='user', action='login')[0]
	login_link = '%s?login=%s&email=%s'%(login_page, pure_login_key, urllib.quote(email_addr))
	email_sender = tk.config.get('ckan.emailauth.email_sender', 'login')
	email_content = tk.config.get('ckan.emailauth.email_content', '''
		<html>
			<head></head>
			<body>
				Click <a href="%s">here</a> to log in to SAAB.
			</body>
		</html>
		''')%login_link
	#	Build
	email_msg = MIMEMultipart.MIMEMultipart()
	email_msg['From'] = email_sender
	email_msg['To'] = email_addr
	email_msg['Date'] = emailutils.formatdate(localtime = True)
	email_msg['Subject'] = tk.config.get('ckan.emailauth.email_subject', 'Your SAAB Login Link')
	#	Attach content
	email_msg.attach(MIMEText.MIMEText(email_content, 'html'))
	
	#	Send
	smtp = SMTP()
	smtp.connect()
	smtp.sendmail(email_sender, email_addr, email_msg.as_string())
	smtp.close()

class EmailAuthPlugin(p.SingletonPlugin):
	p.implements(p.IAuthenticator)
	p.implements(p.IConfigurer)
	p.implements(p.IRoutes)

	def __init__(self, name=None):		
		#	Maybe set up AutoLoginKey
		db.setup()
		
		#	Unimplemented
		identity = lambda x: x
		self.after_map = identity
		self.update_config_schema = identity
				
	def update_config(self, config):
		tk.add_template_directory(config, 'templates')
		return config
	
	def before_map(self, route_map):
		with mapper.SubMapper(route_map, controller='ckanext.emailauth.plugin:EmailAuthController') as m:
			m.connect('login', '/user/login', action='login')
		return route_map
		
	def identify(self):
		if 'emailauth_user' in session:
			tk.c.user = session['emailauth_user']
			return
		if 'login' not in tk.request.GET:
			#	Not a login request
			return
		
		#	Digest the login key
		src_email = urllib.unquote(tk.request.GET['email'])
		to_digest = (tk.request.GET['login'] + src_email).encode('utf-8')
		key = hashlib.sha256(to_digest).hexdigest()
		
		#	Clear expired and pop
		db.AutoLoginKey.remove_expired(expiry_hrs=tk.config.get('ckan.emailauth.login_key_expiry_hrs', 48))
		user_id = db.AutoLoginKey.pop_key(key=key, src_email=src_email)
		
		if user_id is None:
			#	Invalid
			log.warn('Auto login key miss with email %s'%src_email)
			session['emailauth_fail'] = True
			session.save()
			tk.redirect_to(tk.url_for(controller='user', action='login'))
		else:
			#	Valid
			user_name = model.Session.query(model.User).filter(model.User.id == user_id).first().name
			session['emailauth_user'] = user_name
			session.save()
			tk.c.user = user_name
			
	def login(self): pass
		
	def logout(self):
		if 'emailauth_user' in session:
			#	Remove session
			del session['emailauth_user']
			session.save()

	def abort(self, status_code, detail, headers, comment): pass

class EmailAuthController(tk.BaseController):
	
	def login(self):
		if tk.c.user:
			#	Please log out to log in
			return tk.render('user/logout_first.html')
		variant = None
		if 'revert' in tk.request.GET:
			#	Default behaviour
			if 'login' in tk.request.POST:
				user = model.Session.query(model.User).filter(model.User.name == tk.request.POST['login']).first()
				if user is None or not user.validate_password(tk.request.POST['password']):
					return tk.render('user/login.html', extra_vars={
						'revert': True,
						'error_summary': {'': 'Invalid username or password.'}
					})
				#	Successful login
				session['emailauth_user'] = user.name
				session.save()
				tk.h.redirect_to(controller='user', action='me')
			variant = 'revert'
		elif 'emailauth_fail' in session:
			del session['emailauth_fail']
			session.save()
			variant = 'invalid'
		elif 'email_addr' in tk.request.POST:
			email_addr = tk.request.POST['email_addr']
			#	Check if email registered
			user = model.Session.query(model.User).filter(model.User.email == email_addr).first()
			if user is not None:
				#	Send email
				send_login_email(email_addr, user.id)
				variant = 'sent'
			else:
				variant = 'reg_required'
		vars = {}
		if variant is not None:
			vars[variant] = True
		return tk.render('user/login.html', extra_vars=vars)
	