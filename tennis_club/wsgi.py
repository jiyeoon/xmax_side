"""
WSGI config for tennis_club project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tennis_club.settings')

application = get_wsgi_application()

