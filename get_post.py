#!/usr/bin/env python
from __future__ import print_function
import ConfigParser

import facebook
import requests
import re
import httplib2
import os
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


import argparse
parser = argparse.ArgumentParser(parents=[tools.argparser])
parser.add_argument('-c', '--course', dest='course', help='Course config file in .ini format')
args = parser.parse_args()

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Facebook/Google Sheets Checkin'


def process_post_from_group (post, graph):
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
  return (class_date.strip(), sorted(id_list))

def get_credentials():
  home_dir = os.path.expanduser('~')
  credential_dir = os.path.join(home_dir, '.credentials')
  if not os.path.exists(credential_dir):
    os.makedirs(credential_dir)
  credential_path = os.path.join(credential_dir,  'sheets.googleapis.com-python-quickstart.json')
  store = Storage(credential_path)
  credentials = store.get()
  if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    flow.user_agent = APPLICATION_NAME
    credentials = tools.run_flow(flow, store, args)
    print('Storing credentials to ' + credential_path)
  return credentials

def push_to_sheet(data_list, service, spreadsheet_id, sheet_name, student_num, week_count):
  range_name = sheet_name + '!A2:' + str(int(student_num) + 1) 
  c_result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,range=range_name).execute()
  c_values = c_result.get('values', [])
  i = int(week_count) - 1

  range_name = sheet_name + '!' + chr(ord('B') + i) + '1:N1'
  result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,range=range_name).execute()
  values = result.get('values', [])
  if not values:
    print('No data found')
  else:
    w_body = {'values' : [['x']]}
    for row in values:
      for col in row:
        if col in data_list:
          my_col = chr(ord('B') + i)
          print(my_col)
          j = 2
          for c_row in c_values:
            if c_row[0] in data_list[col]:
              range_name = sheet_name + '!' + my_col + '' + str(j)
              service.spreadsheets().values().update(spreadsheetId=spreadsheet_id,range=range_name,valueInputOption='RAW',body=w_body).execute()
            j = j + 1

        i = i + 1 #FIXME this might not always be true!!!
def main():
  # load config
  config = ConfigParser.ConfigParser()
  config.read(args.course)
  access_token = config.get('facebook', 'access_token')
  group_id = config.get('facebook', 'group_id') + '/feed'
  spreadsheet_id = config.get('google', 'sheet_id')
  sheet_name = config.get('google', 'sheet_name')
  student_num = config.get('class', 'student_num')
  week_count = config.get('class', 'week_count')

  # get credential
  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                  'version=v4')
  service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

  # get data from facebook
  graph = facebook.GraphAPI(access_token)
  group = graph.get_object(group_id)

  data_list = []

  while True:
    try:
      [data_list.append(process_post_from_group(post=post, graph=graph)) for post in group['data'] if post['message'].startswith('[ct')]
      posts = requests.get(posts['paging']['next']).json()
    except KeyError:
      break
  date_id_map = {}
  for entry in data_list:
    date_id_map[entry[0]] = entry[1]
  
  #push data to google sheet
  push_to_sheet(data_list = date_id_map, service = service, spreadsheet_id = spreadsheet_id, sheet_name=sheet_name, student_num=student_num, week_count=week_count)
if __name__ == '__main__':
  main()