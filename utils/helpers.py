from .config import *
import spotipy.oauth2 as oauth2
import re
import logging
import datetime

async def fetch_playlist(spotify, username, playlist_id, previous_date):
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id: The playlist id
	:param previous_date: The last time fetched
	:return: A list of URLs of the new songs
	"""
	results = spotify.user_playlist(
		username, playlist_id, fields='tracks,next,name')
	tracks = results['tracks']
	new_songs = []
	while True:
		for item in tracks['items']:
			track = item['track'] if 'track' in item else item
			try:
				track_url = track['external_urls']['spotify']
				if convert_time(item['added_at']) > previous_date:
					new_songs.append(track_url)
			except (KeyError, UnicodeEncodeError) as e:
				logging.warn(u'Skipping track {0} by {1} (local only?)'.format(
					track['name'], track['artists'][0]['name']))
		# 1 page = 50 results
		# check if there are more pages
		if tracks['next']:
			tracks = spotify.next(tracks)
		else:
			break
	return new_songs

async def fetch_playlist_art(spotify, username, playlist_id):
	results = spotify.user_playlist(username, playlist_id, fields='images')
	if results:
		return results['images'][0]['url']
	return None


async def fetch_playlist_name(spotify, username, playlist_id):
	"""
	Find the name of a spotify playlist by its id
	:return: The name of the playlist
	"""
	result = spotify.user_playlist(username, playlist_id)
	return result['name']


async def fetch_playlist_link(spotify, username, playlist_id):
	"""
	Fetches a playlist for new songs
	:param username: Spotify username / id
	:param playlist_id: The playlist id
	:return: The URL of the playlist
	"""
	result = spotify.user_playlist(username, playlist_id)
	return result['external_urls']['spotify']


def generate_credentials():
	""" Generate the token for Spotify. """
	credentials = oauth2.SpotifyClientCredentials(
		client_id=client_id,
		client_secret=client_secret)
	return credentials

async def extract_playlist_id(string):
	"""
	Takes in a string and extracts the playlist id
	:param string: The spotify playlist URL or id
	:return: The id
	"""
	p = re.compile(r"(?<!=)[0-9a-zA-Z]{22}")
	result = p.findall(string)
	if len(result) > 0:
		return result[0]
	logging.error('Invalid playlist id or url')
	return None

def convert_time(time_string):
	"""
	Takes time as a string and converts it to an aware datetime
	:param time_string: Time in the form %Y-%m-%dT%H:%M:%SZ
	:return: An aware datetime
	"""
	added_at = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
	return pytz.UTC.localize(added_at)


def get_current_time(as_string=False):
	"""
	Get the current time
	:param as_string: Whether to return a datetime or as a string (for the db)
	:return: The current time
	"""
	ret = new_time.localize(datetime.datetime.now()).astimezone(old_time)
	return ret.strftime('%Y-%m-%dT%H:%M:%SZ') if as_string else ret