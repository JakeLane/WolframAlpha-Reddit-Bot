'''
WolframAlpha-Bot
A bot that parses Wolfram|Alpha comments

Syntax:
[125 + 375](/u/WolframAlpha-Bot)

@author: Jake Lane
'''
import os
import configparser
from os.path import sys
import re
from threading import Thread
from time import sleep

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

def generate_comment(comment, query):
	# The porridge is feeling alright
	comment_reply = ''
	print('Processing comment')
	for formula in query:
		res = wolframclient.query(formula)  # Query the api
		for pod in res.pods:
			if pod.text: # If there is plaintext
				comment_reply = comment_reply + '**' + pod.title + '**\n\n\t' + pod.text + '\n\n'
			elif pod.main.node.find('img').get('src'): # Try and print an image if it exists
				comment_reply = comment_reply + '**' + pod.title + '**\n\n[Image](' + pod.main.node.find('img').get('src') + ')\n\n'
			# Otherwise we pretend nothing was found (as there was no output we can use for this pod)
	
	comment_reply = comment_reply + '***\n[^About](https://github.com/JakeLane/WolframAlpha-Reddit-Bot) ^| [^(Report a Bug)](https://github.com/JakeLane/WolframAlpha-Reddit-Bot/issues) ^(| Created and maintained by /u/JakeLane)'
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
	
	# Define the regex
	regex = re.compile(r'\[(.*)\]\(\/u\/WolframAlpha-Bot\)', re.I)
	
	print('WolframAlpha-Bot is now running')
	# Start the main loop
	while True:
		print("Checking inbox")
		messages = r.get_unread()
		for comment in messages:
			query = []
			query.extend(regex.findall(comment.body))
			if query != [] and comment.id:
				try:
					print('Found comment with query')
					generate_comment(comment, query)
				except HTTPError as e:
					print('HTTPError: Most likely banned')

		print("Sleeping for 30 seconds")
		sleep(30)

if __name__ == '__main__':
	main()