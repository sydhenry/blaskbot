from functions import chat as _chat
from functions import loadViewersDatabase as _getViewersDB

def command_response(function):

    """
    Limits how fast the function is
    called.
    """

    def wrapper(*args, **kwargs):
        sock = args[0]
        kwargs.update({'sock': sock})
        try:
            userName = args[1]
        except IndexError:
            # No username included in command
            pass
        else:
            viewerDatabase = _getViewersDB()
            kwargs.update({'viwersDatabase': viwersDatabase})

        response = function(*args, **kwargs)
        # We accept a single message, str, as well as a iterable for muti response commands
        responses = [response] if type(response) == str else response
        for response in responses:
            _chat(sock, response)
        return response

    return wrapper
