"""
WSGI config for slide_management project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

import site

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'slide_management.settings')

# activate_this = '/home/wpuralensis/virtualenv/public_html/slide-management/3.6/bin/activate_this.py'
# with open(activate_this) as file_:
#          exec(file_.read(), dict(__file__=activate_this))

application = get_wsgi_application()
