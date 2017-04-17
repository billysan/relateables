
import urllib2

from itertools import chain

from django.db.models import Q

from models import Movie, MovieRelation


IMDB_URL = "http://www.imdb.com"


def get_movie_relations(movie, ring, ring_stop):

	relations = MovieRelation.objects.filter(Q(movie_1 = movie) | Q(movie_2 = movie))
	
	additional_relations = MovieRelation.objects.none()

	if ring < ring_stop:
	
		for r in relations:
			additional_relations = list(chain(additional_relations, get_movie_relations(r.movie_1, ring + 1, ring_stop)))
			additional_relations = list(chain(additional_relations, get_movie_relations(r.movie_2, ring + 1, ring_stop)))

	return list(set(chain(relations, additional_relations)))


def relations_to_json(relations):

	known_movies = []
	nodes = []
	edges = []

	for r in relations:
		if not r.movie_1.pk in known_movies:
			nodes.append(
				{
					"id" : r.movie_1.pk,
					"label" : "%s (%s)" % (r.movie_1.title, str(r.movie_1.rating)),
					"title" : r.movie_1.info
					#"font" : "%dpx verdana blue" % int(r.movie_1.rating * 2)
				})
			known_movies.append(r.movie_1.pk)

		if not r.movie_2.pk in known_movies:
			nodes.append(
				{ 
					"id" : r.movie_2.pk,
					"label" : "%s (%s)" % (r.movie_2.title, str(r.movie_2.rating)),
					"title" : r.movie_2.info
					#"font" : "%dpx verdana blue" % int(r.movie_2.rating * 2) 
				})
			known_movies.append(r.movie_2.pk)
	
		edges.append({ "from" : r.movie_1.pk, "to" : r.movie_2.pk })

	return (nodes, edges)


def liked_by_others(movie_url, ring, ring_stop):
	
	relation_objects = []

	movie_url = movie_url.split('?')[0]

	url_data = urllib2.urlopen(movie_url).read()
	
	my_title = url_data.split('Share this Rating')[1].split('<strong>')[1].split('</strong>')[0]
	
	my_rating = url_data.split('<span itemprop="ratingValue">')[1].split('</span>')[0]
	
	summary_text = url_data.split('<div class=\"summary_text\" itemprop=\"description\">')[1].split('</div>')[0]

	base_movie, created = Movie.objects.get_or_create(url = movie_url)

	if created:
		base_movie.title = my_title
		base_movie.url = movie_url
		base_movie.rating = float(my_rating)
		base_movie.info = summary_text.replace('\n', '')
		base_movie.save()

	for rec_section in url_data.split('rec_item')[1:-1]:
		
		local_url = rec_section.split('href=\"')[1].split('\"')[0].split('?')[0]
		movie_id = local_url.split('/')[2]
		
		related_r = url_data.split('id=\"%s' % movie_id)[1]
		rating = related_r.split('|')[2]
		summary_text = related_r.split('<p>')[1].split('</p>')[0]
		
		url = "%s%s" % (IMDB_URL, local_url)
		
		title = rec_section.split('alt=\"')[1].split('\"')[0]

		#print "%s\t%s" % (title, url)

		related_movie, created = Movie.objects.get_or_create(url = url)

		if created:
			related_movie.title = title
			related_movie.url = url
			related_movie.rating = float(rating)
			related_movie.info = summary_text.replace('\n', '')
			related_movie.save()

		try:
			c1 = Q(movie_1 = base_movie) & Q(movie_2 = related_movie)
			c2 = Q(movie_1 = related_movie) & Q(movie_2 = base_movie)

			if 0 == MovieRelation.objects.filter(Q(c1) | Q(c2)).count():
				relation, created = MovieRelation.objects.get_or_create(movie_1 = base_movie, movie_2 = related_movie)
				relation_objects.append(relation)
		except Exception as e:
			print "Could not create relation: %s" % e

		if ring < ring_stop:
			other_relations = liked_by_others(url, ring + 1, ring_stop)
			if other_relations:
				relation_objects = relation_objects + other_relations		

	base_movie.is_explored = True
	base_movie.save()

	return relation_objects