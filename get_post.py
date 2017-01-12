#!/usr/bin/env python

import facebook
import requests
import re
import httplib2
import os


def process_post_from_group (post):
  id_list = []
  class_date = ''
  try:
    topic = re.search('(\[ct([0-9/ ]*)\])', post['message']).group(0)
    class_date = topic.replace('[ct', '').replace(']', '')
  except AttributeError:
    return
  post_comments = graph.get_object(post['id'] + '/comments')
  numbers = re.compile('[0-9]{9}')
  while True:
    try:
      for comment in post_comments['data']:
        [id_list.append(sid) for sid in numbers.findall(comment['message'])]
      post_comments = requests.get(post_comments['paging']['next']).json()
    except KeyError as error:
      break
  print(class_date)
  print(id_list)

access_token = 'EAACEdEose0cBAP6sittRB4bb2x51wRuZC8eUAdizJZAR9UBCZBpkex4RCwJNxoBu6Wk4lCSZAlKchxePXdLczwk0rZAcjdWfCjCYEtQjd8klE4S6Q8T8Uz8WcajjFM3PGZBCvkSOLOyhpviyrA9iolWh5YJB1HdcK3FLDhYSfI4XRngqZCImYbU0XFwyUZAC4X4ZD'
#443
group_id = '424361884574443/feed'

graph = facebook.GraphAPI(access_token)
group = graph.get_object(group_id)

while True:
  try:
    [process_post_from_group(post=post) for post in group['data'] if post['message'].startswith('[ct')]
    posts = requests.get(posts['paging']['next']).json()
  except KeyError:
    break
