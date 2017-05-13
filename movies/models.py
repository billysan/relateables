# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class Movie(models.Model):

    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200, unique = True)
    is_explored = models.BooleanField(default = False)
    rating = models.FloatField(default = 0)
    genre = models.CharField(max_length=20)
    info = models.CharField(max_length=1024, blank = True, null = True)
    
    poster = models.CharField(max_length=1024, blank = True, null = True)

    def __unicode__(self):
    	return self.title 

    def __str__(self):
    	return self.title


class MovieRelation(models.Model):

    movie_1 = models.ForeignKey(Movie, related_name = 'movie_1s')
    movie_2 = models.ForeignKey(Movie, related_name = 'movie_2s')

    class Meta:
    	unique_together = ('movie_1', 'movie_2')

    def __unicode__(self):
    	return "%s : %s" % (self.movie_1, self.movie_2)

    def __str__(self):
    	return "%s : %s" % (self.movie_1, self.movie_2)

