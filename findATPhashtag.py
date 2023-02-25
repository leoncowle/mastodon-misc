#!/usr/bin/env python3.9

import requests
import feedparser
import bs4
import time
import sys
import os

# NOTE: We'll be using https://instances.social API to get a list of all Mastodon instances (servers)
# Register for a free account and get an AUTH TOKEN
# Put it in an ENV variable called INSTANCESSOCIAL_TOKEN
INSTANCES_API_TOKEN=os.environ["INSTANCESSOCIAL_TOKEN"]

# Use an API call to https://instances.social/api/1.0/instances/list to get a list of all the Mastodon instances they're keeping track of
# count=0 gets ALL instances (takes a few seconds to run). Currently (Feb 2023) gets around 16k up & not dead instances.
r = requests.get("https://instances.social/api/1.0/instances/list?count=0", headers={'Authorization':f'Bearer {INSTANCES_API_TOKEN}'}).json()
to_crawl = []
for i in r['instances']:
  #if i['version'] and int(i['version'][0]) >= 4 and i['up'] and not i['dead']:
  if i['up'] and not i['dead']:
    # This instance is apparently up and not dead, so add it
    to_crawl.append(i['name'])

askATPentries = {}

count = 0
total = len(to_crawl)
for instance in to_crawl:
  count += 1
  print(f"Crawling {instance} ({count} of {total})...")
  try:
    f = feedparser.parse(f"https://{instance}/tags/askatp.rss")
  except:
    # feedparser had some sort of fatal error, so just ignore this instance
    continue
  if f.bozo:
    # bozo is feedparser's way of saying 'broken feed'
    continue
  for rssentry in f.entries:
    try:
      theLink = rssentry.link
      theDate = time.strftime("%Y-%m-%d %H:%M:%S", rssentry.published_parsed)
      theSumm = bs4.BeautifulSoup(rssentry.summary, features="html.parser").text
    except KeyError as e:
      # the rssentry didn't have a "link" or "published_parsed" or "summary" key(s), so ignore this entry
      continue

    if time.time() - time.mktime(rssentry.published_parsed) < 28*24*60*60:
      # Post date is within last 4 weeks (within 2419200 seconds)
      askATPentries[theLink] = { "timestamp": theDate, "summary": theSumm }
  
# Sort the entries by reverse chronological order. It does a string sort on the html line, but the 1st non-similar item on each line is the date, so it works :-)
sortedentries = []
for entry in askATPentries:
  sortedentries.append(f"<span style=\"white-space: nowrap\">{askATPentries[entry]['timestamp']} : <a href=\"{entry}\">LINK</a> : {askATPentries[entry]['summary']}</span><br>\n")
sortedentries.sort(reverse=True)

# Write it out to a html file to be able to load in a browser using file:///tmp/askatp.html, but change this to a DB or whatever you want :-)
with open("/tmp/askatp.html", "w") as f:
  f.write("<html>\n<head>\n<title>AskATP Mastodon posts</title>\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />\n</head>\n<body>\n")
  for entry in sortedentries:
    f.write(entry)
  f.write("</body>\n</html>")
