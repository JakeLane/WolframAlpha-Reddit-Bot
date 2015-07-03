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
import wolframalpha

def generateConfig():
	config = configparser.ConfigParser()
	config.read('config.cfg')
	config['main'] = {'Username': 'YOURUSERNAME', 'Password': 'YOURPASSWORD', 'AppID': 'YOUR_ID_HERE'}
	
	with open('config.cfg', 'w') as f:
		config.write(f)

	print('Configuration not found, a default config.cfg was generated (you must edit it)')
	sys.exit()

def generate_comment(r, comment, username, already_done, query, wolframclient):
	comment_with_replies = r.get_submission(comment.permalink).comments[0]
	for reply in comment_with_replies.replies:
		if reply.author.name == username:
			already_done.add(comment.id)
			print('Comment was already done.')
	if comment.id not in already_done:
		# The porridge is feeling alright
		comment_reply = ''
		for formula in query:
			res = wolframclient.query(formula)  # Query the api
			for pod in res.pods:
				if pod.text: # If there is plaintext
					comment_reply = comment_reply + '**' + pod.title + '**\n\n\t' + pod.text + '\n\n'
				elif pod.main.node.find('img').get('src'): # Try and print an image if it exists
					comment_reply = comment_reply + '**' + pod.title + '**\n\n[Image](' + pod.main.node.find('img').get('src') + ')\n\n'
				# Otherwise we pretend nothing was found (as there was no output we can use for this pod)
		
		comment_reply = comment_reply + '***\n[^About](https://github.com/JakeLane/WolframAlpha-Reddit-Bot) ^| [^(Report a Bug)](https://github.com/JakeLane/WolframAlpha-Reddit-Bot/issues) ^(| Created and maintained by /u/JakeLane)'

		try:
			comment.reply(comment_reply)
			already_done.add(comment.id)
			print('Successfully posted comment.')
		except Exception as e:
			print(e)

def main():
	# Read the config
	config = configparser.RawConfigParser()

	try:
		config.read('config.cfg')
		username = config['main']['Username']
		password = config['main']['Password']
		app_id = config['main']['AppID']
	except:
		generateConfig()

	if (username is None) or (password is None) or (app_id is None):
		generateConfig()
	
	# Login to Reddit
	r = praw.Reddit('WolframAlpha-Bot by /u/JakeLane'
					'Url: https://github.com/JakeLane/WolframAlpha-Reddit-Bot')
	r.config.decode_html_entities = True
	r.login(username, password)
	print('Bot has successfully logged in')
	
	# Create wolframalpha
	wolframclient = wolframalpha.Client(app_id)
	
	# Define the regex
	regex = re.compile('\[(.*\n*)\]\(\/u\/WolframAlpha-Bot\)')
	
	already_done = set()
	
	while True:
		try:
			all_comments = praw.helpers.comment_stream(r, 'all', limit=None, verbosity=0)
			
			# Start the main loop
			while True:
				for comment in all_comments:
					query = []
					query.extend(regex.findall(comment.body))
					if query != [] and comment.id not in already_done:
						try:
							print('Found comment with query')
							thread = Thread(target=generate_comment, args=(r, comment, username, already_done, query, wolframclient))
							thread.start()
						except HTTPError as e:
							print('HTTPError: Most likely banned')
	
		except Exception as e:
			print(e)
			continue

main()