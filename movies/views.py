# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json
import simplejson
import requests
import traceback
import random
from itertools import chain

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q

from relateables.settings import SEARCH_PLACEHOLDERS, IMDB_URL_PREFIX, IMDB_SUGGEST_PREFIX

from models import Movie, MovieRelation

from imdb import liked_by_others, relations_to_json


def index(request):

	context = {
		'random_search_placeholder' : random.choice(SEARCH_PLACEHOLDERS)
	}

	return render(request, 'index.html', context = context)


def movie_search(request):

	try:

		if request.method == "POST" and request.POST.get('movie_url'):

			movie_url = "%s%s" % (IMDB_URL_PREFIX, request.POST['movie_url'])

			nodes, edges = relations_to_json(movie_url, set(liked_by_others(movie_url, 0, 1)))

			movie_obj = Movie.objects.get(url = movie_url)

			context = {
				'random_search_placeholder' : random.choice(SEARCH_PLACEHOLDERS),
				'movie' : movie_obj,
				'nodes' : json.dumps(nodes),
				'edges' : json.dumps(edges)
			}

			return render(request, "movie_graph.html", context = context)

		else:
			raise ValueError

	except ValueError as e:
		context = {
			'random_search_placeholder' : random.choice(SEARCH_PLACEHOLDERS),
			'message' : 'Your input was not valid'
		}
		
		return render(request, "index.html", context = context)

	except Exception as e:
		context = {
			'random_search_placeholder' : random.choice(SEARCH_PLACEHOLDERS),
			'message' : 'An error occured while getting results from IMDB.'
		}

		return render(request, "index.html", context = context)


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

		try:
		
			query = query.replace(' ', '_').lower()
			query_url = "%s/%s/%s.json" % (IMDB_SUGGEST_PREFIX, query[0], query)
		
			req = requests.get(query_url)

			results_str = unicode(req.content, 'latin-1').split("%s(" % query)[1][:-1]
			results_q = simplejson.loads(results_str)['d']

			search_results = { }

			results = 'results'.encode('utf-8').strip()

			search_results[results] = { }

			for e in results_q:
				
				entry = ''
				
				if e.has_key('l'):
					entry = e['l'].encode('utf-8').strip()

				if e.has_key('q'):
					entry += " - %s" % e['q']

				if e.has_key('y'):
					entry += " (%d)" % e['y']

				entry = re.sub(r'[^\x00-\x7f]',r'.', entry.encode('utf-8').strip()).replace('\'','').encode('utf-8').strip()
				mdbid = re.sub(r'[^\x00-\x7f]',r'.', e['id'].encode('utf-8').strip()).encode('utf-8').strip()

				if 'tt' in mdbid:
					search_results[results][mdbid] = entry

			return search_results

		except:
			return { }
	
	return { }