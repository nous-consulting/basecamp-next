Python Wrapper for Basecamp Next
================================

First, you need to get an access token, if you don't have one yet:

    from basceampx import Auth
    auth = Auth('clientid', 'clientsecret', 'http://redirecturl')
    auth.authorize_url()

After user grants you access, get the token itself:

    auth.access_token(code)
