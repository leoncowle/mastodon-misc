import os
import requests
import re
import copy

#################### GLOBAL VARIABLES ##################
### Change as needed
TOKEN = os.environ["MASTO_TOKEN"]              # Mastodon access_token, needs read:lists permission
INSTANCE = "hachyderm.io"                      # NB: only the domain -- don't add http:// or https://, or the api path
HEADERS = {"Authorization": f"Bearer {TOKEN}"} # Auth header
########################################################

def getListAccts(listId):
  ''' 
    Function to get all the members in a List
    Takes the list id as argument
    Returns a python list [] of accounts in the Mastodon List
  '''
  accts = []
  r = requests.get(f"https://{INSTANCE}/api/v1/lists/{listId}/accounts?limit=80", headers=HEADERS)
  if r.status_code != 200:
    print(f"Error getting list details for listId '{listId}'. API responded with: {r.text}")
  while r.status_code == 200:
    # This 'while' loop pages through Mastodon results, 
    # as long as there is a response header containing a rel="next" entry
    accts += [ i['acct'] for i in r.json()]
    if "link" in r.headers and 'rel="next"' in r.headers["link"]:
      urlnext = re.sub(".*<([^>]+)>; rel=.next.*", r"\1", r.headers["link"])
      r = requests.get(urlnext, headers=HEADERS)
    else:
      # We've reached the end; no more 'rel="next"' entry in 'link' header
      break
  return accts

def postToMasto(listName, listId, acctName):
  '''
    Function to post a message back to Mastodon
    Takes the list name, list id, and account name as arguments
    Returns nothing
  '''
  status  =  "PIPEDREAM:\n\nAn account dropped out of one of your lists:\n\n"
  status += f'List: "{listName}" (id:{listId})\n'
  if "@" in acctName:
    status += f"Acct: {acctName}"
  else:
    status += f"Acct: {acctName}@{INSTANCE}"
  # Post it!
  payload = {}
  payload["status"] = status
  payload["visibility"] = "direct"
  r = requests.post(f"https://{INSTANCE}/api/v1/statuses", data=payload, headers=HEADERS)
  if r.status_code != 200:
    print(f"Error posting back to Mastodon. API responded with: {r.text}")

def handler(pd: "pipedream"):
  '''
    Main PipeDream handler (entrypoint from trigger)
    1. Gets the data_store data into the 'ds' variable
    2. Gets a list of your Mastodon Lists
    3. If called using the webhook trigger and "/savecurrent" path, save your Mastodon Lists, 
       as they currently look, back into the data_store (overwriting previous saved data)
    4. If called using the timer trigger, compare your current (live) List data with
       the data saved in the PipeDream data_store. 
    5. Post any newly-missing accounts back as a 'direct' status update into Mastodon, so
       it'll only be visible to yourself, but you'll still see it in your Home TL.

    NOTES:
      You may wonder why I'm using "requests" instead of "Mastodon.py" to make the API calls.
      Well, Mastodon.py (at time of writing) has/had a bug in its function call to get 
      List members -- it would only get the first 40 and no more (because it was ignoring
      filter arguments). I've submitted a pullrequest to its github repo which fixes this.
  '''

  # Get our DataStore
  ds = pd.inputs["data_store"]

  # Let's get all our current Lists and their members (accounts) from Mastodon
  r = requests.get(f"https://{INSTANCE}/api/v1/lists", headers=HEADERS)
  if r.status_code != 200:
    print(f"Error getting list of Lists. API responded with: {r.text}")
    return {"status":"mastodon API error"}     # return out of handler
  currentlists = {}
  for aList in r.json():
    listId = str(aList['id'])
    listTitle = aList['title']
    currentlists[listId] = {}
    currentlists[listId]['title'] = listTitle
    currentlists[listId]['accounts'] = getListAccts(listId)
    if listId not in ds:
      # If a new list is found that isn't in the saved lists in the data_store
      # then just go ahead and add it -- because why not?
      ds[listId] = currentlists[listId]

  try:
    # Let's check if we we called with the http GET trigger with /savecurrent PATH
    eventMethod = pd.steps["trigger"]["event"]["method"]
    eventPath = pd.steps["trigger"]["event"]["path"]
    if eventMethod == "GET" and eventPath == "/savecurrent":
      # Let's clear the data_store (to ensure we save only the current state)
      ds.clear()
      # And then repopulate it with the current state of lists
      for listId in currentlists:
        ds[listId] = currentlists[listId]
      return {"status":"saved current status"}
  except KeyError as e:
    # Wasn't called with GET and /savecurrent
    # So don't attempt to save to data_store
    pass

  # Load saved lists from data_store...
  oldlists = {}
  for listId in ds.keys():
    oldlists[listId] = ds[listId]

  # Compare old (saved) state to current/live state, and report.
  for oldId in oldlists:
    if oldId in currentlists:
      # oldId is still there in currentlists (i.e. the list hasn't been deleted)
      # Let's use sets, for easy comparison
      setOld = set(oldlists[oldId]['accounts'])
      setCur = set(currentlists[oldId]['accounts'])
      for inBoth in setOld & setCur:
        print(f"INFO: List member that appears in your saved list AND in the same current list: {oldlists[oldId]['title']} (id:{oldId}) : {inBoth}")
      for newacct in setCur.difference(setOld):
        print(f"INFO: New list member found that isn't in your saved list: {oldlists[oldId]['title']} (id:{oldId}) : {newacct}")
      for missing in setOld.difference(setCur):
        print(f"WARNING: A list member has been removed from a list: {oldlists[oldId]['title']} (id:{oldId}) : {missing}")
        postToMasto(oldlists[oldId]['title'], oldId, missing)

