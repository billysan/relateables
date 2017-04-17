
from __future__ import unicode_literals

from django.contrib import admin

from .models import Movie, MovieRelation

admin.site.register(Movie)
admin.site.register(MovieRelation)