import unirest

# TODO finish documentation


class CamFindError(Exception):
    def __init__(self, args):
        self.args = args


class CamFind(object):
    """Manages CamFind API requests.

    Handles asynchronous requests to the CamFind API. Supports one request per object. It will store the resulting
    string from the request inside of the .result member and also set the .complete member flag when it completes.

    Example usage:
    def h(result):
        print result

    r = CamFind(key=key, callback=h)
    r.post_local(directory)
    """

    _request_url = 'https://camfind.p.mashape.com/image_requests'
    _response_url = 'https://camfind.p.mashape.com/image_responses/'

    def __init__(self, key, callback=None):
        self.key = key
        self.result = None
        self.complete = False

        # private vars
        self._locale = 'en_us'
        self._callback = callback
        self._image_file = None
        self._post_response = None
        self._get_response = None
        self._token = None
        self._busy = False

    #
    # ## PUBLIC METHODS ## #
    #

    def change_callback(self, callback):
        if self._busy:
            raise CamFindError('Cannot change callback mid-request')
        else:
            self._callback = callback

    def post_local(self, directory):
        """Sends a locally stored image to be analyzed using CamFind API.

        :param directory: relative file directory of the image to send
        :return: None
        """
        # only support one pending request per object
        if self._busy:
            raise CamFindError('A request is still being serviced')

        self.complete = False
        self._busy = True

        # attempt to close it if it is not None and it is open still
        if self._image_file and not self._image_file.closed:
            self._image_file.close()

        self._image_file = open(directory, mode='r')

        self._post_response = unirest.post(
            self._request_url,
            headers={
                'X-Mashape-Key': self.key
            },
            params={
                'image_request[image]': self._image_file,
                'image_request[locale]': self._locale
            },
            callback=self._post_callback
        )

    # TODO finish remote-hosted images method
    def post_remote(self, url):
        pass

    #
    # ## PRIVATE METHODS ## #
    #

    def _post_callback(self, response):
        # Callback function for the POST request methods
        self._image_file.close()
        self._post_response = response

        # find the token, else raise error
        if 'token' in response.body:
            self._token = self._post_response.body['token']
        else:
            raise CamFindError('POST failed with response: ' + response.body)

        # start making GET requests
        self._getResponse = unirest.get(
            self._response_url + self._token,
            headers={
                'X-Mashape-Key': self.key,
                'Accept': 'application/json'
            },
            callback=self._get_callback
        )

    def _get_callback(self, response):
        # Callback function for the GET requests made in POST callback
        self._get_response = response

        if response.body['status'] == 'completed':
            # finished, set result
            self.result = response.body['name']

            # reset flags
            self.complete = True
            self._busy = False

            # if a handler is provided, call it
            if self._callback:
                self._callback(self.result)
        elif response.body['status'] == 'not completed':
            # make a new request and repeat until it completes or errors out
            self._getResponse = unirest.get(
                self._response_url + self._token,
                headers={
                    'X-Mashape-Key': self.key,
                    'Accept': 'application/json'
                },
                callback=self._get_callback
            )
        else:
            # finished, clear flags and raise an error
            self._busy = False
            raise CamFindError('GET failed with response: ' + response.body)

if __name__ == '__main__':
    import sys

    def handler(result):
        print result
        sys.exit(0)

    k = 'rsKvDw2rwSmshDWwMsQhFxVhoaGVp1GkBwcjsnmRaVtLOjt9h4'

    try:
        request = CamFind(key=k, callback=handler)
        request.post_local('./ImageRequests/banana.jpg')
    except CamFindError as e:
        print e
        sys.exit(0)

    print 'Request sent'

    while True:
        # pretend to work on other things
        pass