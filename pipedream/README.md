# PIPEDREAM -- masto_warn_list_members.py

This is the python code that is used in a PipeDream [https://www.pipedream.com] workflow.

### Purpose

If you make use of Lists in Mastodon, you may not realize an important caveat: if someone you follow moves their
Mastodon account from one instance/server to another, Mastodon will (very likely) automatically follow their new account
for you. 

**HOWEVER, if you had them in a Mastodon List, their old account will SILENTLY drop out of the List, and their
new account will NOT be added back into the List.**

This PipeDream workflow warns you when this happens.

It does so by saving the state of your Lists into a PipeDream ```data_store```, and then, on subsequent runs, compares the
current state of your Lists with what it has saved. If it finds any accounts that are suddendy missing, it posts a
message back into Mastodon, which you'll see in your Home Timeline (as a DM post from-you-to-you).

### Installation

This isn't meant to be a detailed instructional tutorial on how to get started with PipeDream.

But because this project was inspired by Stefan Bohacek
(https://stefanbohacek.com/blog/automating-your-mastodon-profile-with-pipedream-com/ and you can find Stefan on Mastodon
at https://stefanbohacek.online/@stefan), you can you read _that_ blog post for a great writeup of how to set up 
PipeDream! Thanks Stefan.

**Few points of note for my project:**
1. You will need a Mastodon token with ```read:lists``` and ```write:statuses``` permissions.
2. Like Stefan's instructions, you'll need to add this auth token (from step 1) into PipeDream's Settings into
an Environment Variable. I've called it ```MASTO_TOKEN```, but you can call it anything, as long as you update the 
reference to it in the Python code as well.
3. Something that Stefan didn't use that is needed for this project: set up a ```data_store```. Once you've created a 
Python step, go into the ```Configure``` section of the new Python step (above the ```Code``` section) and create a 
```data_store```. You can call it anything you want, as the name doesn't appear to matter. The handler in the Python 
code simply refers to it as ```pd.inputs["data_store"]```, not by its name.

### Triggers

You will need 2 triggers for this PipeDream workflow to work correctly.
1. The 1st trigger mirrored Stefan's approach of using a ```Schedule``` trigger to run this code at a specific 
date & time -- I do it once daily in the middle-ish of the day.
2. The 2nd trigger is a ```HTTP/WebHook``` trigger. This will give you a unique URL that you can call to run this code.
This is needed to force a re-save of the current state of your Lists. E.g. you deliberately removed a List member, or you
have new List members. Once you're happy with the state of your Lists, you call this unique URL, adding a path of 
```https://<uniqueURL>/savecurrent```, which will force a fresh save of your current Lists status.

# HAVE FUN! :-) 