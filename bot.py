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
import wolframalpha

def generateConfig():
	config = configparser.ConfigParser()
	config.read('config.cfg')
	config['main'] = {'AppID': 'YOUR_ID_HERE'}
	config['main'] = {'OAuth': True}
	config['main'] = {'Username': 'YOUR_USERNAME'}
	config['main'] = {'Password': 'YOUR_PASSWORD'}
	
	with open('config.cfg', 'w') as f:
		config.write(f)

	print('Configuration not found, a default config.cfg was generated (you must edit it)')
	sys.exit()

def check_comment(comment, already_done):
	url_regex = re.compile(r'http[s]?:\/\/(?:www\.)?wolframalpha\.com\/input\/(\?i=.*)', re.I)
	
	# Get the joined parameters in a list
	urls = []
	urls.extend(url_regex.findall(comment.body))

	if urls != [] and comment.id not in already_done:
		print('Found comment with Wolfram URL')
		# Convert to a usable form
		query = []
		for urlend in urls:
			query.append(urllib.parse.parse_qs(urllib.parse.urlparse(urlend).query)['i'][0])
		
		try:
			generate_comment(comment, query)
		except HTTPError as e:
			print('HTTPError: Most likely banned')
		
		already_done.add(comment.id)

def check_inbox():
	print('Checking inbox')
	call_regex = re.compile(r'\[(.*)\]\(\/u\/WolframAlpha-Bot\)', re.I)
	messages = r.get_unread()
	for comment in messages:
		query = []
		query.append(call_regex.findall(comment.body))
		if query != []:
			print('Found message with query')
			try:
				generate_comment(comment, query)
			except HTTPError as e:
				print('HTTPError: Most likely banned')

def generate_comment(comment, query):
	# The porridge is feeling alright
	comment_reply = ''
	print('Processing comment')
	for formula in query:
		res = wolframclient.query(formula)  # Query the api
		for pod in res.pods:
			if pod.text: # If there is plaintext
				comment_reply = comment_reply + '**' + pod.title + '**\n\n\t' + pod.text.replace('\n', '\t\n') + '\n\n'
			elif pod.main.node.find('img').get('src'): # Try and print an image if it exists
				comment_reply = comment_reply + '**' + pod.title + '**\n\n[Image](' + pod.main.node.find('img').get('src') + ')\n\n'
			# Otherwise we pretend nothing was found (as there was no output we can use for this pod)
		comment_reply = comment_reply + '***\n'

	if not comment_reply:
		# Add some text if nothing was found
		comment_reply = '*The WolframAlpha API did not return anything for this query. Is it valid?*\n***\n'
	
	comment_reply = comment_reply + '\n[^About](https://github.com/JakeLane/WolframAlpha-Reddit-Bot) ^| [^(Report a Bug)](https://github.com/JakeLane/WolframAlpha-Reddit-Bot/issues) ^(| Created and maintained by /u/JakeLane)'
	comment.reply(comment_reply)
	comment.mark_as_read()
	print('Successfully posted comment.')

def main():
	# Read the config
	config = configparser.RawConfigParser()

	try:
		config.read('config.cfg')
		app_id = config.get('main', 'AppID')
		oauth = config.getboolean('main', 'oauth')
		username = config.get('main', 'Username')
		password = config.get('main', 'Password')
	except:
		generateConfig()

	if (app_id is None):
		generateConfig()
	
	# OAuth and reddit initialisation
	global r
	r = praw.Reddit('WolframAlpha script by /u/JakeLane')
	r.config.decode_html_entities = True
	if oauth:
		print("Using OAuth")
		o = OAuth2Util.OAuth2Util(r)
		o.refresh()
	else:
		print("Using Cookies")
		r.login(username, password)

	# Create wolframalpha
	global wolframclient
	wolframclient = wolframalpha.Client(app_id)

	already_done = set()
		
	print('WolframAlpha Bot is now running')
	# Start the main loop

	inbox_time = time.time() + 30
	
	while True:
		comments = praw.helpers.comment_stream(r, 'all', limit=None, verbosity=0)
		for comment in comments:
			check_comment(comment, already_done)
			if inbox_time <= time.time():
				check_inbox()
				inbox_time = time.time() + 30

if __name__ == '__main__':
	main()
