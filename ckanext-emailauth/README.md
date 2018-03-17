#	What?

A CKAN plugin that allows users to authenticate via email. Username and password login is still supported.

Tested on CKAN 2.7.

#	Why?

So your CKAN users don't need to remember their passwords.

#	How?

Install like any other CKAN plugin. Check out the CKAN docs for a tutorial on how to do that.

Unsurprisingly, requires an SMTP client (eg. postfix).

Configuration, with defaults shown, is:
```ini
#	The number of hours a login email's link will stay valid
ckan.emailauth.login_key_expiry_hrs = 48
#	The number of bytes to use for the automatic login key
ckan.emailauth.login_key_size = 20
#	A format string for the email. The formatted value is link HREF
ckan.emailauth.email_content = *authored for SAAB*
#	The name of the email sender
ckan.emailauth.email_sender = login
#	The subject of the login email
ckan.emailauth.email_subject = *authored for SAAB*
```
#	Who?

Authored by Robin Saxifrage of [OpenGovGear](http://opengovgear.com) for [SAAB](http://saabnational.org).