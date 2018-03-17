#
#	Schema-related constants
#

__all__ = [
	'REPORT_TYPES',
	'EXCLUDES',
	'ACTIVITY_REPORT_FIELDS',
	'MEMBERSHIP_MISSING_FIELDS',
	'SEMESTER_MISSING_FIELDS'
]

#	Form id, type description mapping
REPORT_TYPES = {
	'student': 'student/semester summary',
	'chapter_activity': 'chapter activity',
	'chapter_member': 'chapter membership',
	'custom': 'custom'
}

#	Stuff we dont care about
EXCLUDES = [
	'cache_last_updated',
	'cache_url',
	'format',
	'hash',
	'mimetype',
	'mimetype_inner',
	'resource_type',
	'last_modified',
	'size',
	'url',
	'created',
	'url_type',
	'author',
	'author_email',
	'license_id',
	'license_title',
	'maintainer',
	'maintainer_email',
	'num_tags',
	'num_resources',
	'notes',
	'groups',
	'relationships_as_object',
	'relationships_as_subject',
	'revision_id',
	'resources',
	'tags',
	'url',
	'version',
	'package_id',
	'position',
	'private',
	'revision',
	'description',
	'owner_org',
	'metadata_modified',
	'metadata_created',
	'isopen',
	'id',
	'creator_user_id',
	'type',
	'state',
	'datastore_active',
	'created'
]

#	The semester fields that constitute
#	an activity report
ACTIVITY_REPORT_FIELDS = [
	'student',
	'after_school_events',
	'after_club_events',
	'after_school_dates',
	'after_club_dates',
	'leadership_SAAB',
	'leadership_SAAB_notes',
	'community_service_events',
	'community_service_dates',
	'adviser_meeting_notes',
	'adviser_meeting_dates'
]

#	Missing/empty fields to filter on
#	for membership
MEMBERSHIP_MISSING_FIELDS = [
	'act',
	'college_applications',
	'city_of_residence',
	'contact_email',
	'contact_phone_number',
	'fafsa',
	'parent_consent',
	'parent_first_name',
	'parent_last_name',
	'parent_middle_name',
	'pdp_exists',
	'pdp_notes',
	'psat',
	'sat',
	'state_of_residence',
	'student_consent'
]

#	Missing/empty fields to filter on
#	for semesters
SEMESTER_MISSING_FIELDS = [
	'academic_advisor_notes',
	'advisor_meeting_dates',
	'after_club_dates',
	'after_club_events',
	'after_school_dates',
	'after_school_events',
	'community_service_dates',
	'community_service_events',
	'credits_attempted',
	'credits_earned',
	'days_absent',
	'degree_obtained1',
	'degree_obtained2',
	'leadership_saab',
	'leadership_saab_notes',
	'passed_all_classes'
]