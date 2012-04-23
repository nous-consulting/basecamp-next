Python Wrapper for Basecamp Next
================================

First, you need to get an access token, if you don't have one:

> from basceampx import Auth
> auth = Auth('clientid', 'clientsecret', 'http://redirecturl')
> auth.authorize _ url()

After user grants you access, get the token itself:

> auth.access _ token(code)
