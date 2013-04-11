# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2013 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <http://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
'''
Base code for machine translation services.
'''

from django.core.cache import cache
from django.conf import settings
import json
import urllib
import urllib2
import weblate


class MachineTranslationError(Exception):
    '''
    Generic Machine translation error.
    '''


class MachineTranslation(object):
    '''
    Generic object for machine translation services.
    '''
    name = 'MT'
    default_languages = []

    def __init__(self):
        '''
        Creates new machine translation object.
        '''
        self.mtid = self.name.lower().replace(' ', '-')

    def authenticate(self, request):
        '''
        Hook for backends to allow add authentication headers to request.
        '''
        return

    def json_req(self, url, http_post=False, skip_auth=False, **kwargs):
        '''
        Performs JSON request.
        '''
        # Encode params
        if len(kwargs) > 0:
            params = urllib.urlencode(kwargs)
        else:
            params = ''

        # Append parameters
        if len(params) > 0 and not http_post:
            url = '%s?%s' % (url, params)

        # Create request object with custom headers
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Weblate/%s' % weblate.VERSION)
        # Optional authentication
        if not skip_auth:
            self.authenticate(request)

        # Fire request
        if http_post:
            handle = urllib2.urlopen(request, params)
        else:
            handle = urllib2.urlopen(request)

        # Read and possibly convert response
        text = handle.read()
        # Needed for Microsoft
        if text.startswith('\xef\xbb\xbf'):
            text = text.decode('UTF-8-sig')
        else:
            # Some services just cut in middle of UTF-8 char...
            text = text.decode('utf-8', 'ignore')
        # Needed for Google
        while ',,' in text:
            text = text.replace(',,', ',null,')

        # Parse JSON
        response = json.loads(text)

        # Return data
        return response

    def json_status_req(self, url, http_post=False, skip_auth=False, **kwargs):
        '''
        Performs JSON request with checking response status.
        '''
        # Perform request
        response = self.json_req(url, http_post, skip_auth, **kwargs)

        # Check response status
        if response['responseStatus'] != 200:
            raise MachineTranslationError(response['responseDetails'])

        # Return data
        return response

    def download_languages(self):
        '''
        Downloads list of supported languages from a service.
        '''
        return []

    def download_translations(self, language, text, unit):
        '''
        Downloads list of possible translations from a service.
        '''
        raise NotImplementedError()

    def convert_language(self, language):
        '''
        Converts language to service specific code.
        '''
        return language

    @property
    def supported_languages(self):
        '''
        Returns list of supported languages.
        '''
        cache_key = '%s-languages' % self.mtid

        # Try using list from cache
        languages = cache.get(cache_key)
        if languages is not None:
            return languages

        # Download
        try:
            languages = self.download_languages()
        except Exception as exc:
            weblate.logger.error(
                'Failed to fetch languages from %s, using defaults (%s: %s)',
                self.name,
                exc.__class__.__name__,
                str(exc)
            )
            if settings.DEBUG:
                raise
            return self.default_languages

        # Update cache
        cache.set(cache_key, languages, 3600 * 48)

        return languages

    def is_supported(self, language):
        '''
        Checks whether given language combination is supported.
        '''
        return language in self.supported_languages

    def translate(self, language, text, unit):
        '''
        Returns list of machine translations.
        '''
        language = self.convert_language(language)
        if not self.is_supported(language):
            return []

        try:
            translations = self.download_translations(language, text, unit)

            return [
                {
                    'text': trans[0],
                    'quality': trans[1],
                    'service': trans[2],
                    'source': trans[3]
                }
                for trans in translations
            ]
        except Exception as exc:
            weblate.logger.error(
                'Failed to fetch translations from %s (%s: %s)',
                self.name,
                exc.__class__.__name__,
                str(exc)
            )
            raise
