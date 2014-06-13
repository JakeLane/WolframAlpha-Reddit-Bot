'''
WolframAlpha-Bot
A bot that parses wolframalpha comments

Syntax:
[125 + 375](/u/WolframAlpha-Bot)

@author: Jake Lane
'''
import logging
import os
from os.path import sys
import re
from threading import Thread
from time import sleep

import praw
import wolframalpha


def main():
    # Start the logger
    initialize_logger('log')

    # Parse the configuration
    enviroment_fail = False
    
    username = os.environ.get('wolframalpha_bot_reddit_username')
    if username == None:
        logging.error('Could not load username')
        enviroment_fail = True
        
    password = os.environ.get('wolframalpha_bot_reddit_password')
    if password == None:
        logging.error('Could not load password')
        enviroment_fail = True
        
    global wolfram_app_id
    wolfram_app_id = os.environ.get('wolframalpha_bot_wolfram_app_id')
    if wolfram_app_id == None:
        logging.error('Could not load wolfram_app_id')
        enviroment_fail = True
        
    subreddits = os.environ.get('wolframalpha_bot_reddit_subreddits')
    if subreddits == None:
        logging.error('Could not load subreddits')
        enviroment_fail = True
    else:
        subreddits = subreddits.split(',')
    
    if not enviroment_fail:
        logging.info('WolframAlpha-Bot v1 by /u/LeManyman has started')
    else:
        logging.error('Could not start bot.')
        sys.exit(0)
    
    # Initiate things
    global banned_subs
    banned_subs = []
    
    # Login to Reddit
    r = praw.Reddit('WolframAlpha-Bot by u/LeManyman'
                    'Url: https://bitbucket.org/JakeLane/wolframalpha-redditbot')
    r.config.decode_html_entities = True
    r.login(username, password)
    logging.info('Bot has successfully logged in')
    
    # Create wolframalpha
    global client
    client = wolframalpha.Client(wolfram_app_id)
    
    # Define the regex
    regex = re.compile('\[(.*\n*)\]\(\/u\/WolframAlpha-Bot\)')
    
    already_done = set()
    
    while True:
        try:
            # Generate the multireddit
            if str(subreddits[0]) != 'all':
                multireddit = ('%s') % '+'.join(subreddits)
                logging.info('Bot will be scanning the multireddit "' + multireddit + '".')
            else:
                all_comments = praw.helpers.comment_stream(r, 'all', limit=None)
                logging.info('Bot will be scanning all of reddit.')
            
            # Start the main loop
            while True:
                if str(subreddits[0]) != 'all':
                    subs = r.get_subreddit(multireddit)
                    all_comments = subs.get_comments()
                
                for comment in all_comments:
                    query = []
                    query.extend(regex.findall(comment.body))
                    if query != [] and comment.id not in already_done:
                        try:
                            logging.info('Found comment with query')
                            thread = Thread(target=generate_comment, args=(r, comment, username, already_done, query))
                            thread.start()
                        except HTTPError as e:
                            logging.info('HTTPError: Most likely banned')
    
        except Exception as e:
            logging.error(e)
            continue

def generate_comment(r, comment, username, already_done, query):
    comment_with_replies = r.get_submission(comment.permalink).comments[0]
    for reply in comment_with_replies.replies:
        if reply.author.name == username:
            already_done.add(comment.id)
            logging.info('Comment was already done.')
    if comment.id not in already_done:
        # The porridge is feeling alright
        comment_reply = ''
        for formula in query:
            res = client.query(formula)  # Query the api
            if len(res.pods) > 0:
                pod = res.pods[1]
                if pod.text:
                    comment_reply = comment_reply + '>' + formula + '\n\n' + pod.text + '\n\n'
                else:
                    comment_reply = comment_reply + '>' + formula + '\n\n' + "This bot does not support this type of input. Nag /u/LeManyman about it.\n\n"
            else:
                comment_reply = comment_reply + "Wolfram|Alpha does not support this input.\n\n"
        
        comment_reply = comment_reply + '***\n[^About](https://bitbucket.org/JakeLane/wolframalpha-redditbot) ^| [^(Report a Bug)](https://bitbucket.org/JakeLane/wolframalpha-redditbot/issues) ^(| Created and maintained by /u/LeManyman)'
        try:
            comment.reply(comment_reply)
            already_done.add(comment.id)
            logging.info('Successfully posted comment.')
        except Exception as e:
            logging.error(e)

def initialize_logger(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if not os.path.exists(output_dir + '/all.log'):
        open(output_dir + '/all.log', 'w+').close()
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
     
    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
 
    # create error file handler and set level to error
    handler = logging.FileHandler(os.path.join(output_dir, "error.log"), "w", encoding=None, delay="true")
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
 
    # create debug file handler and set level to debug
    handler = logging.FileHandler(os.path.join(output_dir, "all.log"), "w")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

if __name__ == '__main__':
    main()
