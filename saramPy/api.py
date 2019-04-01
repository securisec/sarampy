from saramPy import Saram
import json
import requests
from uuid import uuid1

class StatusNotOk(Exception):
    """Exception with status code is not 200"""
    pass

class NotValidCategory(Exception):
    """Exception when category is not valid"""
    pass

class SaramAPI(Saram):
    """
    Class that exposes the full API for Saram. Interits from 
    saramPy.Saram.

    :param base_url: Set if the base url is neither of the pre-defined ones
    :type token: str
    :param local: Set to True to use http://localhost:5001/ as base url
    :type token: bool

    >>> from saramPy.api import SaramAPI
    >>> saram = SaramAPI(local=True)
    """

    def __init__(self, base_url: str=None, local: bool=False):
        super().__init__(token=None, base_url=base_url, local=local)
        with open(self._conf_file, 'r') as f:
            conf = json.loads(f.read())
            self.username = conf['username'] 
            self.apiKey = conf['apiKey']
            self.avatar = conf.get('avatar', '/static/saramapi.png')
        self.api_url = f'{self.base_url}api/'
        self._valid_types = ['file', 'stdout', 'script', 'dump', 'tool', 'image']
        self._valid_categories = [
            'android',
            'cryptography',
            'firmware',
            'forensics',
            'hardware',
            'ios',
            'misc',
            'network',
            'pcap',
            'pwn',
            'reversing',
            'stego',
            'web',
            'none',
            'other',
            'scripting',
        ]
        self._headers = {
            'x-saram-apikey': self.apiKey,
            'x-saram-username': self.username
        }

    def get_all_entries(self) -> list:
        """
        Gets an array of all the valid entries
        
        :raises StatusNotOk: Exception on fail
        :return: Array containing objects of all the entries
        :rtype: list
        
        >>> entries = saram.get_all_entries()
        >>> print(entries)
        """

        r = requests.get(f'{self.api_url}all/entries', headers=self._headers)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not create section')

    def get_entry(self, token: str) -> dict:
        """
        Gets all the data associated with a single entry
        
        :param token: Valid token for entry
        :type token: str
        :raises StatusNotOk: Exception if not found
        :return: object with all entry data
        :rtype: dict

        >>> entry = saram.get_entry(token='sometoken')
        """

        r = requests.get(f'{self.api_url}{token}', headers=self._headers)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not create section')

    def delete_entry(self, token: str) -> dict:
        """
        Delete an entry entirely
        
        :param token: Valid token for entry
        :type token: str
        :raises StatusNotOk: Exception on fail
        :return: OK object
        :rtype: dict

        >>> entry = saram.delete_entry(token='sometoken')
        """

        r = requests.delete(f'{self.api_url}{token}', headers=self._headers)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk(f'Could not delete Status code: {r.status}')

    def create_new_section(self, token: str, type: str,
        output: str, command: str, comment: str='saramPy'
    ) -> dict:
        """
        Create a new section. This will add to the existing entry.
        
        :param token: Valid token for the entry
        :type token: str
        :param type: Valid type. Ex. `stdout`
        :type type: str
        :param output: Output of a command/variable etc
        :type output: str
        :param command: Command executed to get the output
        :type command: str
        :param comment: Comment to add, defaults to ['saramPy']
        :param comment: list, optional
        :raises TypeError: Exception if type is not valid
        :raises StatusNotOk: Exception on fail
        :return: OK object
        :rtype: dict
        """

        payload = {
            'id': str(uuid1()),
            'type': type,
            'output': output,
            'command': command,
            'user': self.username,
            'comment': {
                'text': comment,
                'username': self.username,
                'avatar': self.avatar
            },
            'options': {
                'marked': 2
            },
            'time': self._time
        }
        if type not in self._valid_types:
            raise TypeError(f'Valid types are {self._valid_types}')
        r = requests.patch(f'{self.api_url}{token}', headers=self._headers,
        json=payload)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not create section')
    
    def add_comment(self, token: str, dataid: str, comment: str) -> dict:
        """
        Add a comment to a section.
        
        :param token: Valid token for the entry
        :type token: str
        :param dataid: Valid section to add the comment to
        :type dataid: str
        :param comment: Comment to add
        :type comment: str
        :raises StatusNotOk: Exception on fail
        :return: OK object
        :rtype: dict

        >>> entry = saram.add_comment(token='sometoken', dataid='long_data_id', comment='helpful comment')
        """

        payload = {
            'data': {
                'text': comment,
                'username': self.username,
                'avatar': self.avatar
            }
        }
        r = requests.patch(f'{self.api_url}{token}/{dataid}/comment',
        json=payload, headers=self._headers)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not add comment')

    def delete_section(self, token: str, dataid: str) -> dict:
        """
        Delete a section. This will delete a single section in an entry
        
        :param token: Valid token for the entry
        :type token: str
        :param dataid: Valid dataid for the section to delete
        :type dataid: str
        :raises StatusNotOk: Exception on fail
        :return: OK object
        :rtype: dict
        """

        r = requests.delete(f'{self.api_url}{token}/{dataid}', headers=self._headers)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not delete section')

    def create_new_entry(self, title: str, category: str, slack_link: str='') -> dict:
        """
        Create a new entry. This is a whole new entry to work with
        
        :param title: Title of section/challenge
        :type title: str
        :param category: Category of section/challenge
        :type category: str
        :param slack_link: Slack link, or any other valid reference link, defaults to ''
        :param slack_link: str, optional
        :raises NotValidCategory: Exception if a vategory is not valid
        :raises StatusNotOk: Exception on fail
        :return: OK response object
        :rtype: dict
        """

        if category not in self._valid_categories:
            raise NotValidCategory(f'Valid categories are {self._valid_categories}')
        token = self._token_generator(title)
        payload = {
            'title': title,
            'category': category,
            'slackLink': slack_link,
            'timeCreate': self._time,
            'data': []
        }
        r = requests.post(f'{self.api_url}create/{token}', headers=self._headers,
        json=payload)
        if r.status_code == 200:
            print('Created new entry')
        else:
            raise StatusNotOk('Could not create entry')

    def reset_api_key(self, old_apikey: str, username: str) -> dict:
        """
        Reset the API key
        
        :param old_apikey: Valid API key
        :type old_apikey: str
        :param username: Username associated with valid API key
        :type username: str
        :raises StatusNotOk: Exception on fail
        :return: object containing new API key
        :rtype: dict
        """

        payload = {
            'apiKey': old_apikey,
            'username': username
        }
        r = requests.post(f'{self.api_url}reset/key', headers=self._headers, json=payload)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not create section')
    
    def change_username(self, api_key: str, old_username: str, new_username: str) -> dict:
        """
        Change the username to a new username
        
        :param api_key: Valid API key
        :type api_key: str
        :param old_username: Old username
        :type old_username: str
        :param new_username: New username
        :type new_username: str
        :raises StatusNotOk: Exception on fail
        :return: object with both old and new usernames
        :rtype: dict
        """

        payload = {
            'apiKey': api_key,
            'username': old_username,
            'newUsername': new_username
        }
        r = requests.post(f'{self.api_url}reset/username', headers=self._headers, json=payload)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not create section')

    def validate_api_key(self, api_key: str) -> dict:
        """
        Validate and API key and if valid, return the API and assciated username
        
        :param api_key: Valid API key
        :type api_key: str
        :raises StatusNotOk: Exception
        :return: dict containing the valid API key and associated username
        :rtype: dict

        >>> entry = saram.validate_api_key(api_key='secretapikey')
        """

        payload = {
            'key': api_key
        }
        r = requests.post(f'{self.base_url}misc/valid/key', json=payload)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not validate API key')

    def get_valid_token(self, title: str) -> dict:
        """
        Supply a title, and get a valid token back. This is useful when 
        testing token creation, or when working with other API endpoints.
        
        :param title: Title to generate the token with
        :type title: str
        :raises StatusNotOk: Exception
        :return: reponse dictionary object
        :rtype: dict

        >>> entry = saram.get_valid_token(title='Title of some challenge')
        """

        payload = {
            'title': title
        }
        r = requests.post(f'{self.base_url}misc/valid/token', json=payload)
        if r.status_code == 200:
            return r.json()
        else:
            raise StatusNotOk('Could not create a valid token')
