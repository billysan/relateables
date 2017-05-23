
import urllib2
import traceback

from HTMLParser import HTMLParser
from itertools import chain

from django.db.models import Q

from models import Movie, MovieRelation

from relateables.settings import IMDB_URL, BROKEN_IMAGE_URL, WORDS_PER_LINE_IN_MOVIE_INFO, INFO_CHARS_NEWLINES_THRESHOLD


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def format_title(movie):

	info_perfix = "<i><b>%s</b></i>" % (movie.title)

	info = ''

	if len(movie.info) < INFO_CHARS_NEWLINES_THRESHOLD:
		
		info = movie.info

	else:

		info_arr = movie.info.split(' ')
		current_line = info_perfix

		for word in info_arr:

			info += word + ' '
			current_line += word + ' '
			
			if len(current_line) > INFO_CHARS_NEWLINES_THRESHOLD:
				info += '<br>'
				current_line = ''

	return "%s: %s" % (info_perfix, info)


def get_movie_node(base_url, movie):
	return {
		"id" : movie.url.split('/')[-1], # ttXXXXXX
		"label" : str(movie.rating),
		"title" : format_title(movie),
		"shape" : "circularImage",
		"image" : movie.poster,
		"size" : 55 if movie.url == base_url else 40
	}


def relations_to_json(base_url, relations):

	known_movies = []

	nodes = []
	edges = []

	for r in relations:

		movie_1_id = r.movie_1.url.split('/')[-1]
		movie_2_id = r.movie_2.url.split('/')[-1]

		if not r.movie_1.pk in known_movies:
			nodes.append(get_movie_node(base_url, r.movie_1))
			known_movies.append(r.movie_1.pk)

		if not r.movie_2.pk in known_movies:
			nodes.append(get_movie_node(base_url, r.movie_2))
			known_movies.append(r.movie_2.pk)
	
		edges.append({ "from" : movie_1_id, "to" : movie_2_id })

	return (nodes, edges)


def explore_url(movie_url, ring, ring_stop):

	url_data = urllib2.urlopen(movie_url).read()

	relation_objects = []

	try:
		base_title = url_data.split('Share this Rating')[1].split('<strong>')[1].split('</strong>')[0]
		base_rating = url_data.split('<span itemprop="ratingValue">')[1].split('</span>')[0]
	except IndexError:
		print traceback.format_exc()
		return relation_objects

	try:
		base_poster = url_data.split('<div class=\"poster\">')[1].split('src=\"')[1].split('\"')[0]
	except IndexError:
		print traceback.format_exc()
		base_poster = BROKEN_IMAGE_URL

	try:
		base_summary_text = url_data.split('<div class=\"summary_text\" itemprop=\"description\">')[1].split('</div>')[0]
	except IndexError:
		print traceback.format_exc()
		base_summary_text = 'Missing summary'

	base_movie, created = Movie.objects.get_or_create(url = movie_url)
	base_movie.title = base_title
	base_movie.url = movie_url
	base_movie.rating = float(base_rating)
	base_movie.info = strip_tags(base_summary_text.replace('\n', '').replace('See full summary', '').strip())
	base_movie.poster = base_poster
	base_movie.save()

	if 'rec_item' in url_data:

		for rec_section in url_data.split('rec_item')[1:-1]:

			try:

				related_relative_url = rec_section.split('href=\"')[1].split('\"')[0].split('?')[0]
				
				related_id = related_relative_url.split('/')[2]
				
				related_r = url_data.split('id=\"%s' % related_id)[1]

				related_rating = related_r.split('|')[2]
				related_summary_text = related_r.split('<p>')[1].split('</p>')[0]
				related_poster = rec_section.split('loadlate=\"')[1].split('\"')[0]
				related_title = rec_section.split('alt=\"')[1].split('\"')[0]

				related_url = "%s%s" % (IMDB_URL, related_relative_url)

				if related_url[-1] == '/':
					related_url = related_url[:-1]

				related_movie, created = Movie.objects.get_or_create(url = related_url)
				related_movie.title = related_title
				related_movie.url = related_url
				related_movie.rating = float(related_rating)
				related_movie.info = strip_tags(related_summary_text.replace('\n', '').replace('See full summary', '').strip())
				related_movie.poster = related_poster
				related_movie.save()

				try:
					c1 = Q(movie_1 = base_movie) & Q(movie_2 = related_movie)
					c2 = Q(movie_1 = related_movie) & Q(movie_2 = base_movie)

					if 0 == MovieRelation.objects.filter(Q(c1) | Q(c2)).count():
						relation, created = MovieRelation.objects.get_or_create(movie_1 = base_movie, movie_2 = related_movie)
						relation_objects.append(relation)
				except Exception as e:
					print traceback.format_exc()
					print "Could not create relation: %s" % e

				if ring < ring_stop:
					try:
						other_relations = liked_by_others(related_url, ring + 1, ring_stop)
						if other_relations:
							relation_objects = relation_objects + other_relations
					except:
						print traceback.format_exc()
						print "Could not fetch URL: %s" % related_url
			except:
				print traceback.format_exc()
				print "Could not parse movie: %s" % movie_url
				return relation_objects

	base_movie.is_explored = True
	base_movie.save()

	return relation_objects


def liked_by_others(movie_url, ring, ring_stop):

	movie_url = movie_url.split('?')[0]

	if movie_url[-1] == '/':
		movie_url = movie_url[:-1]

	try:

		movie = Movie.objects.get(url = movie_url, is_explored = True)

		relations = MovieRelation.objects.filter(Q(movie_1 = movie) | Q(movie_2 = movie))

		if ring < ring_stop:

			relation_objects = []

			for r in relations:
				relation_objects = list(chain(relation_objects, liked_by_others(r.movie_1.url, ring + 1, ring_stop)))
				relation_objects = list(chain(relation_objects, liked_by_others(r.movie_2.url, ring + 1, ring_stop)))

			return list(set(relation_objects))

		else:
			return list(set(relations))

	except Movie.DoesNotExist:
		return explore_url(movie_url, ring, ring_stop)

	except:
		print traceback.format_exc()
		return [ ]