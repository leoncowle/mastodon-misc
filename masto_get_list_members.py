#!/usr/bin/env python3.9

##############################################################################
##############################################################################
##############################################################################

# Background:  You use Lists in Mastodon.
#              Someone you follow, who you also have in 1 or more lists, moves
#              their Mastodon account to a new instance/server.
#              Mastodon will (should) automatically follow the moved-to-account
#              for you.
#              HOWEVER, the person's new account will NOT be added to any lists
#              automatically, and their old account will SILENTLY be dropped
#              from any of your lists that it was a member of.
#              This is not ideal. :-)

# Description: short script that saves your current Mastodon Lists' members
#              into a file (when using the '--reset' flag) and then at any later
#              time, compares that saved file's content to the current Lists'
#              members, to see if any accounts have dropped out of any lists.

# Author: Leon Cowle
# Copyright (c) 2023 Leon Cowle
# Version 0.1
# License:
"""

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

"""
# Acknowledgments:
#   https://github.com/halcy/Mastodon.py by https://icosahedron.website/@halcy

# Instructions:
# 1. Create a Mastodon Application, with read:lists permissions, and copy the Access Token.
# 2. Either hardcode the access token below in GLOBAL VARIABLES or add it into an environment variable called MASTOTOKEN
# 3. On your Mac or Linux box: pip install Mastodon.py (or pip3)
# 4. Run this script once with the --reset argument, to create the required saved file containing your lists and their members
# 5. Run this script at any time again without the --reset argument, to compare the currect lists & members to what you had saved,
#    to see if any accounts had dropped out of any lists.
# 6. Once you've fixed any issues in your Mastodon Lists (added missing people back, etc), and you're happy with the output from this script, 
#    then re-run it with the --reset argument to save the current list+members state (overwriting the previously saved state)

##############################################################################
##############################################################################
##############################################################################

import os
import pickle
import sys
from mastodon import Mastodon

#################### GLOBAL VARIABLES ##################
### Change as needed
TOKEN = os.environ["MASTOTOKEN"]         # Mastodon access_token, needs read:lists permission
INSTANCE = "https://hachyderm.io"
SAVEFILE = "masto_get_list_members.pkl"
debug = True
########################################################

mastodon = Mastodon(access_token = TOKEN, api_base_url = INSTANCE)

# Let's get all our current Lists and their members (accounts)
currentlists = {}
for entry in mastodon.lists():
  entryId = entry['id']
  entryTitle = entry['title']
  currentlists[entryId] = {}
  currentlists[entryId]['title'] = entryTitle
  currentlists[entryId]['accounts'] = []
  m = mastodon.list_accounts(entryId, limit=10)
  while len(m) > 0:
    currentlists[entryId]['accounts'] += [ i['acct'] for i in m ]
    max_id = m[-1]['id']
    m = mastodon.list_accounts(entryId, limit=40, max_id=max_id)

# If run with --reset, let's save the retrieved Lists+Members into SAVEFILE
if len(sys.argv) > 1 and sys.argv[1] == "--reset":
  with open(SAVEFILE, 'wb') as f:
    pickle.dump(currentlists, f)
  print("Saved current state of lists out to 'masto_get_list_members.pkl'...")
  for i in currentlists:
    print(f"ID:{i} NAME:{currentlists[i]['title']} MEMBERCOUNT:{len(currentlists[i]['accounts'])}")
  sys.exit(0)

# Wasn't run with --reset, so let's read old Lists+Members state from SAVEFILE (and then compare to live/current state)
oldlists = {}
with open(SAVEFILE, 'rb') as f:
  oldlists = pickle.load(f)

# Compare old (saved) state to current/live state, and report.
for oldId in oldlists:
  if oldId in currentlists:
    # oldId is still there in currentlists (i.e. the list hasn't been deleted)
    for oldAcct in oldlists[oldId]['accounts']:
      if oldAcct in currentlists[oldId]['accounts']:
        if debug:
          print("Good   : ", oldId, oldlists[oldId]['title'], oldAcct)
      else:
        print("MISSING:", oldId, oldlists[oldId]['title'], oldAcct)
