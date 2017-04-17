# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from itertools import chain

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q

from models import Movie, MovieRelation

from imdb import liked_by_others, relations_to_json, get_movie_relations

def index(request):
    return render(request, "index.html")


def movie_search(request):

	if request.method == "POST" and request.POST.get("movie_url") and request.POST.get('ring'):

		movie_url = request.POST['movie_url'].split('?')[0]
		ring_stop = int(request.POST['ring'])

		print movie_url
		print Movie.objects.filter(url = movie_url, is_explored = True)

		try:
			movie = Movie.objects.get(url = movie_url, is_explored = True)
			
			relations = get_movie_relations(movie, 0, ring_stop)

			nodes, edges = relations_to_json(relations)
		
		except Movie.DoesNotExist:
			nodes, edges = relations_to_json(set(liked_by_others(movie_url, 0, ring_stop)))

		return render(request, "movie_graph.html", context = { 'nodes' : json.dumps(nodes), 'edges' : json.dumps(edges) })