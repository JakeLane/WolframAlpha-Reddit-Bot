'''
WolframAlpha-Bot
A bot that parses Wolfram|Alpha comments

Syntax:
[125 + 375](/u/WolframAlpha-Bot)

@author: Jake Lane
'''
import configparser
from os.path import sys
import re
import time
import urllib.parse

import praw
import OAuth2Util
import pyimgur
import wolframalpha

class Query(object):
	def __init__(self, query, assumptions=None):
		self.query = query
		self.assumptions = assumptions

def generateConfig():
	config = configparser.ConfigParser()
	config.read('config.cfg')
	config['main'] = {'AppID': 'YOUR_ID_HERE'}
	config['main'] = {'OAuth': True}
	config['main'] = {'location': None}
	config['main'] = {'Username': 'YOUR_USERNAME'}
	config['main'] = {'Password': 'YOUR_PASSWORD'}
	config['main'] = {'imgurID': 'IMGUR_ID'}
	config['main'] = {'imgurSECRET': 'IMGUR_SECRET'}
	
	with open('config.cfg', 'w') as f:
		config.write(f)

	print('Configuration not found, a default config.cfg was generated (you must edit it)')
	sys.exit()

def check_comment(comment, already_done):
	url_regex = re.compile(r'[(]?http[s]?:\/\/(?:www\.|m.)?wolframalpha\.com\/input\/(\?i=[^)]*)[)]?', re.I)
	
	# Get the joined parameters in a list
	urls = []
	urls.extend(url_regex.findall(comment.body))

	if urls != [] and comment.id not in already_done and comment.subreddit.display_name not in sub_blacklist:
		print('Found comment with Wolfram URL')
		# Convert to a usable form
		queries = []
		for urlend in urls:
			args = urllib.parse.parse_qs(urllib.parse.urlparse(urlend).query)
			if 'a' in args:
				queries.append(Query(args['i'][0], args['a'][0]))
			else:
				queries.append(Query(args['i'][0]))
		try:
			generate_comment(comment, queries, True)
		except HTTPError as e:
			print('HTTPError: Most likely banned')
		
		already_done.add(comment.id)

def check_inbox():
	print('Checking inbox')
	call_regex = re.compile(r'\[(.*)\][ ]?\(\/u\/WolframAlpha-Bot[ ]?\)', re.I)
	messages = r.get_unread()
	for comment in messages:
		matches = call_regex.findall(comment.body)

		queries = []
		for match in matches:
			queries.append(Query(match))

		if queries != []:
			print('Found message with query')
			try:
				generate_comment(comment, queries, False)
			except HTTPError as e:
				print('HTTPError: Most likely banned')
		elif comment.body.startswith('delete http'):
			print('Delete command found')
			try:
				parent = r.get_submission(comment.body.split()[1]).comments[0]
				if parent.author == comment.author:
					for bot_comment in parent.replies:
						if bot_comment.author.name == 'WolframAlpha-Bot':
							bot_comment.delete()
					comment.reply('Comment deleted')
					print('Comment deleted')
			except Exception as e: 
				print('Could not delete', e)
			comment.mark_as_read()
		else:
			# Not a valid comment
			print('Invalid message')
			comment.mark_as_read()
	print('Done checking inbox')

def upload_image(url):
	im = pyimgur.Imgur(imgur_id, imgur_secret)
	return im.upload_image(url=url).link

def generate_comment(comment, queries, automatic):
	do_not_post = False
	# Check the blacklist
	if comment.author.name not in user_blacklist:
		comment_reply = ''
		print('Processing comment')
		for formula in queries:
			res = wolframclient.query(formula.query, formula.assumptions) # Query the api
			for pod in res.pods:
				comment_reply += '**' + pod.title + '**\n\n'
				if pod.text and pod.text <= 1000: # If there is plaintext
					comment_reply += '\t' + pod.text.replace('\n', '\n\t') + '\n\n'
				if pod.main.node.find('img').get('src'): # Try and print an image if it exists
					comment_reply += '[Image](' + upload_image(pod.main.node.find('img').get('src'))[:-4] + ')\n\n'
				# Otherwise we pretend nothing was found (as there was no output we can use for this pod)
				if pod.title == 'Input interpretation' and 'current geoIP location' in pod.text:
					# Don't post if the geoIP is taken
					do_not_post = True
			comment_reply += '***\n'

		if comment_reply == '***\n':
			if not automatic:
				comment_reply = '*The WolframAlpha API did not return anything for this query. Is it valid?*\n***\n'
			else:
				do_not_post = True

		try:
			comment_reply += '\n[^(Delete (comment author only)^)](https://www.reddit.com/message/compose?to=WolframAlpha-Bot&subject=WolframAlpha-Bot%20Deletion&message=delete+' + comment.permalink + ') ^| '
		except AttributeError:
			comment_reply += '\n'

		comment_reply += '[^About](https://github.com/JakeLane/WolframAlpha-Reddit-Bot) ^| [^(Report a Bug)](https://github.com/JakeLane/WolframAlpha-Reddit-Bot/issues) ^(| Created and maintained by /u/JakeLane)'
		if not do_not_post:
			comment.reply(comment_reply)
			print('Successfully posted comment.')
		else:
			print('Did not post comment.')
		comment.mark_as_read()

def main():
	# Read the config
	config = configparser.RawConfigParser()

	try:
		config.read('config.cfg')
	except:
		generateConfig()

	app_id = config.get('main', 'AppID')
	oauth = config.getboolean('main', 'oauth')
	username = config.get('main', 'Username')
	password = config.get('main', 'Password')
	location = config.get('main', 'Location')
	global imgur_id
	imgur_id = config.get('main', 'imgurID')
	global imgur_secret
	imgur_secret = config.get('main', 'imgurSECRET')

	# Get the user blacklist
	global user_blacklist
	with open('user_blacklist.txt') as f:
		user_blacklist = f.read().splitlines()

	# Get the sub blacklist
	global sub_blacklist
	with open('sub_blacklist.txt') as f:
		sub_blacklist = f.read().splitlines()
	
	# OAuth and reddit initialisation
	global r
	r = praw.Reddit('WolframAlpha script by /u/JakeLane')
	r.config.decode_html_entities = True
	if oauth:
		print('Using OAuth')
		o = OAuth2Util.OAuth2Util(r)
		o.refresh()
	else:
		print('Using Cookies')
		r.login(username, password)

	# Create wolframalpha
	global wolframclient
	wolframclient = wolframalpha.Client(app_id, location)

	already_done = set()
		
	print('WolframAlpha Bot is now running')
	# Start the main loop

	oauth_time = time.time() + 3000 # 50 minutes
	inbox_time = time.time() + 30 # 30 seconds
	
	while True:
		comments = praw.helpers.comment_stream(r, 'all', limit=None, verbosity=0)
		try:
			for comment in comments:
				if oauth and oauth_time <= time.time():
					o.refresh() # Refresh the oauth token every 50 mins
				check_comment(comment, already_done)
				if inbox_time <= time.time():
					check_inbox()
					inbox_time = time.time() + 30

		except Exception as e:
			print('Bot Crashed:', e)

if __name__ == '__main__':
	main()
