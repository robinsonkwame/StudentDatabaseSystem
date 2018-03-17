import ckan.plugins as p
import ckan.plugins.toolkit as tk


class StudentfieldsPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
  p.implements(p.IDatasetForm)
  p.implements(p.IConfigurer)

  # IConfigurer

  def update_config(self, config_):
    tk.add_template_directory(config_, 'templates')
    tk.add_public_directory(config_, 'public')
    tk.add_resource('fanstatic', 'studentfields')

  def create_package_schema(self):
    # let's grab the default schema in our plugin
    schema = super(StudentfieldsPlugin, self).create_package_schema()
    # our custom field
    schema.update({
      'student_first_name': [tk.get_validator('ignore_missing'),
                             tk.get_converter('convert_to_extras')],
      'student_last_name': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
      'student_middle_name': [tk.get_validator('ignore_missing'),
                              tk.get_converter('convert_to_extras')],
      'parent_first_name': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
      'parent_last_name': [tk.get_validator('ignore_missing'),
                           tk.get_converter('convert_to_extras')],
      'parent_middle_name': [tk.get_validator('ignore_missing'),
                             tk.get_converter('convert_to_extras')],
      'contact_email': [tk.get_validator('ignore_missing'),
                        tk.get_converter('convert_to_extras')],
      'contact_phone_number': [tk.get_validator('ignore_missing'),
                               tk.get_converter('convert_to_extras')],
      'enrollment_date': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')],
      'graduation_date': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')],
      'age': [tk.get_validator('ignore_missing'),
              tk.get_converter('convert_to_extras')],
      'race': [tk.get_validator('ignore_missing'),
               tk.get_converter('convert_to_extras')],
      'departure_date': [tk.get_validator('ignore_missing'),
                         tk.get_converter('convert_to_extras')],
      'city_of_residence': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
      'state_of_residence': [tk.get_validator('ignore_missing'),
                             tk.get_converter('convert_to_extras')],
      'prior_school': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')],
      'student_id_number': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')],
      'student_consent': [tk.get_validator('ignore_missing'),
                          tk.get_converter('convert_to_extras')],
      'parent_consent': [tk.get_validator('ignore_missing'),
                         tk.get_converter('convert_to_extras')]

    })
    return schema

  def update_package_schema(self):
    schema = super(StudentfieldsPlugin, self).update_package_schema()
    # our custom field
    schema.update({
      'custom_text': [tk.get_validator('ignore_missing'),
                      tk.get_converter('convert_to_extras')],
      'custom_text2': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')]

    })
    return schema

  def show_package_schema(self):
    schema = super(StudentfieldsPlugin, self).show_package_schema()
    schema.update({
      'custom_text': [tk.get_validator('ignore_missing'),
                      tk.get_converter('convert_to_extras')],
      'custom_text2': [tk.get_validator('ignore_missing'),
                       tk.get_converter('convert_to_extras')]

    })
    return schema

  def is_fallback(self):
    # Return True to register this plugin as the default handler for
    # package types not handled by any other IDatasetForm plugin.
    return True

  def package_types(self):
    # This plugin doesn't handle any special package types, it just
    # registers itself as the default (above).
    return []
