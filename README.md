Python Wrapper for Basecamp Next
================================

First, you need to ask user's permission to access her data:

    from basceampx.auth import Auth
    auth = Auth('clientid', 'clientsecret', 'http://my_app/handle_redirect')
    authorize_url = auth.authorize_url()

Redirect the user to the `authorize_url`. After user grants you access, get the
access token:

    token = auth.access_token(code)['access_token']

Find the accounts that this user has:

    from basecampx import Client
    client = Client(token, 'YourAppName')
    accounts = client.basecamp_accounts()

Use a user's Basecamp Next account to access data in projects:

    client = Client(token, 'YourAppName', bcx_accounts[0])

    from basecampx import Projects
    project_list = Projects(client).list()
    project_names = [project['name'] for project in project_list]

Get all discussions in a project:

    messages = Projects(client, 12345).topics.list()
