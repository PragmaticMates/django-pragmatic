project = 'django-pragmatic'
copyright = '2024, Pragmatic Mates'
author = 'Pragmatic Mates'
release = '6.0.3'
version = '6.0'

extensions = [
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 3,
    'titles_only': False,
}

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'django': ('https://docs.djangoproject.com/en/stable/', 'https://docs.djangoproject.com/en/stable/_objects/'),
}
