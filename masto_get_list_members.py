#!/usr/bin/env python3.9

""" 
##############################################################################
##############################################################################
##############################################################################

Author: Leon Cowle
Copyright (c) 2023 Leon Cowle
Version 0.1 -- 2023/02/09

Background:  You use Lists in Mastodon.
             Someone you follow, who you also have in 1 or more lists, moves
             their Mastodon account to a new instance/server.
             Mastodon will (should) automatically follow the moved-to-account
             for you.
             HOWEVER, the person's new account will NOT be added to any lists
             automatically, and their old account will SILENTLY be dropped
             from any of your lists that it was a member of.
             This is not ideal. :-)

Description: short script that saves your current Mastodon Lists' members
             into a file (when using the '--savecurrent' flag) and then at any later
             time, compares that saved file's content to the current Lists'
             members, to see if any accounts have dropped out of any lists.

License:

   MIT License

   Copyright (c) 2023 Leon Cowle

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.

Acknowledgments:
  https://github.com/halcy/Mastodon.py by https://icosahedron.website/@halcy

Instructions:
1. Create a Mastodon Application, with read:lists permissions, and copy the Access Token.
2. Either hardcode the access token below in GLOBAL VARIABLES or, better yet, 
   add it into an environment variable called MASTOLISTTOKEN
3. On your Mac or Linux box: pip install Mastodon.py (or pip3)
4. Run this script once (with or without the --savecurrent arg), to create the initial required saved 
   file containing your lists and their members
5. Run this script at any time again without the --savecurrent argument, to compare the 
   currect lists & members to what you had saved, to see if any accounts had dropped out of any lists.
6. Once you've fixed any issues in your Mastodon Lists (added missing people back, etc), 
   and you're happy with the output from this script, then re-run it with the --savecurrent argument
   to save the current list+members state (overwriting the previously saved state)

Optional instructions:
1. If you have a 2nd Mastodon account that you post status updates into for yourself (that you follow
   on your main account), then add the access token of that account into 'postTOKEN' in the OPTIONAL 
   section or, better yet, into an environment variable called MASTOPOSTTOKEN
2. Set postToMasto to True in GLOBAL VARIABLES

##############################################################################
##############################################################################
##############################################################################
"""

import os
import json
import sys
from mastodon import Mastodon

#################### GLOBAL VARIABLES ##################
### Change as needed
TOKEN = os.environ["MASTOLISTTOKEN"]          # Mastodon access_token, needs read:lists permission
INSTANCE = "hachyderm.io"                     # NB: only the domain -- don't add http:// or https://, or the api path
SAVEFILE = "masto_get_list_members.json"      # File you want to save the current state of your lists into
debug = True                                 # Change this to True to also show accounts that exist in your current lists AND in the saved file
postToMasto = False                            # Change this to True if you want to post the missing accounts to Mastodon
########################################################

########################################################
### START OPTIONAL
### These are only needed if you have a 2nd Mastodon account + token
### used to write posts into (that you follow on your main account)
### AND you want to post dropped-out-account status updates to that Mastodon account
if postToMasto:
  postTOKEN = os.environ["MASTOPOSTTOKEN"]   # Mastodon access_token, needs write:statuses permission
  postInstance = Mastodon(access_token = postTOKEN, api_base_url = f"https://{INSTANCE}")
def _postToMasto(listId, listName, acctName):
  global postInstance
  status  =  "An account dropped out of one of your lists:\n\n"
  status += f'List: "{listName}" (id:{listId})\n'
  if "@" in acctName:
    status += f"Acct: {acctName}"
  else:
    status += f"Acct: {acctName}@{INSTANCE}"
  postInstance.status_post(status, visibility="private")
### END OPTIONAL
########################################################

# Let's get our main Mastodon instance
mastodon = Mastodon(access_token = TOKEN, api_base_url = f"https://{INSTANCE}")

# Let's get all our current Lists and their members (accounts)
currentlists = {}
for entry in mastodon.lists():
  entryId = str(entry['id'])
  entryTitle = entry['title']
  currentlists[entryId] = {}
  currentlists[entryId]['title'] = entryTitle
  currentlists[entryId]['accounts'] = []
  m = mastodon.list_accounts(entryId, limit=40)
  while len(m) > 0:
    # Getting 40 list members at a time, so page through results
    currentlists[entryId]['accounts'] += [ i['acct'] for i in m ]
    max_id = m[-1]['id']
    m = mastodon.list_accounts(entryId, limit=40, max_id=max_id)

# If run with --savecurrent, let's save the retrieved Lists+Members into SAVEFILE
if not os.path.exists(SAVEFILE) or (len(sys.argv) > 1 and sys.argv[1] == "--savecurrent"):
  with open(SAVEFILE, 'w') as f:
    json.dump(currentlists, f)
  print(f"Saved current state of lists out to '{SAVEFILE}'...")
  for i in currentlists:
    print(f"ID:{i} NAME:{currentlists[i]['title']} MEMBERCOUNT:{len(currentlists[i]['accounts'])}")
  sys.exit(0)

# Wasn't run with --savecurrent, so let's read old Lists+Members state from SAVEFILE (and then compare to live/current state)
oldlists = {}
with open(SAVEFILE, 'r') as f:
  oldlists = json.load(f)

print()

foundNew = False

setOldLists = set(oldlists.keys())
setCurLists = set(currentlists.keys())
for newlistId in setCurLists.difference(setOldLists):
  if debug:
    print(f"INFO: New list found that isn't in your saved file (so not checking its members): {currentlists[newlistId]['title']} (id:{newlistId})")
  foundNew = True

# Compare old (saved) state to current/live state, and report.
for oldId in oldlists:
  if oldId in currentlists:
    # oldId is still there in currentlists (i.e. the list hasn't been deleted)
    setOld = set(oldlists[oldId]['accounts'])
    setCur = set(currentlists[oldId]['accounts'])
    if debug:
      for inBoth in setOld & setCur:
        print(f"INFO: List member that appears in your saved file AND in the same current list: {oldlists[oldId]['title']} (id:{oldId}) : {inBoth}")
    for newacct in setCur.difference(setOld):
      if debug:
        print(f"INFO: New list member found that isn't in your saved file: {oldlists[oldId]['title']} (id:{oldId}) : {newacct}")
      foundNew = True
    for missing in setOld.difference(setCur):
      print(f"WARNING: A list member has been removed from a list: {oldlists[oldId]['title']} (id:{oldId}) : {missing}")
      if postToMasto:
        # Also OPTIONALLY post this to a Mastodon account
        _postToMasto(oldId, oldlists[oldId]['title'], missing)

if foundNew:
  print("\nFYI: There are new members in your list(s) and/or you have new list(s), so once you've fixed any missing members (if any),")
  print(f"I recommend you save the current state of your lists back into '{SAVEFILE}' by running (WARNING: it will OVERWRITE what's there):")
  print(sys.argv[0], "--savecurrent")
  print()

sys.exit(0)
