# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json
import simplejson
import requests

from itertools import chain

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q

from models import Movie, MovieRelation

from imdb import liked_by_others, relations_to_json, get_movie_relations


MAX_RING_STOP = 2

def index(request):
    return render(request, "index.html")


def movie_search(request):

	if request.method == "POST" and request.POST.get("movie_url") and request.POST.get('ring'):

		movie_url = "http://www.imdb.com/title/%s" % request.POST['movie_url']
		ring_stop = int(request.POST['ring'])

		if ring_stop > MAX_RING_STOP:
			ring_stop = MAX_RING_STOP

		print movie_url
		print Movie.objects.filter(url = movie_url, is_explored = True)

		try:
			movie = Movie.objects.get(url = movie_url, is_explored = True)
			
			relations = get_movie_relations(movie, 0, ring_stop)

			nodes, edges = relations_to_json(relations)
		
		except Movie.DoesNotExist:
			nodes, edges = relations_to_json(set(liked_by_others(movie_url, 0, ring_stop)))

		return render(request, "movie_graph.html", context = { 'nodes' : json.dumps(nodes), 'edges' : json.dumps(edges) })

def json_response(func):
    """
    A decorator thats takes a view response and turns it
    into json. If a callback is added through GET or POST
    the response is JSONP.
    """
    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)
        if isinstance(objects, HttpResponse):
            return objects
        try:
            data = simplejson.dumps(objects)
            if 'callback' in request.REQUEST:
                # a jsonp response!
                data = '%s(%s);' % (request.REQUEST['callback'], data)
                return HttpResponse(data, "text/javascript")
        except:
            data = simplejson.dumps(str(objects))

        return HttpResponse(data, "application/json")
    
    return decorator

@json_response
def get_imdb_suggestions(request):

	query = request.GET.get('term')

	if query:

		query = query.replace(' ', '_').lower()
		query_url = "https://v2.sg.media-imdb.com/suggests/%s/%s.json" % (query[0], query)
		req = requests.get(query_url)

		results_str = unicode(req.content, 'latin-1').split("%s(" % query)[1][:-1]
		results_q = simplejson.loads(results_str)['d']

		end_results = { }

		results = 'results'.encode('utf-8').strip()

		end_results[results] = { }

		for e in results_q:
			entry = re.sub(r'[^\x00-\x7f]',r'.', e['l'].encode('utf-8').strip()).replace('\'','').encode('utf-8').strip()
			mdbid = re.sub(r'[^\x00-\x7f]',r'.', e['id'].encode('utf-8').strip()).encode('utf-8').strip()
			
			if 'tt' in mdbid:
				end_results[results][mdbid] = entry

		print end_results
		return end_results

	return {}