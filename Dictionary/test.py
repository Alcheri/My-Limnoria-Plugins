import unittest
from unittest.mock import patch, MagicMock
from supybot.test import PluginTestCase
from .plugin import Dictionary

# FILE: Dictionary/test.py


class TestDictionary(PluginTestCase):
    plugins = ('Dictionary',)

    @patch('Dictionary.plugin.utils.web.getUrl')
    def test_successful_response(self, mock_getUrl):
        mock_response = json.dumps([{
            'meanings': [{
                'partOfSpeech': 'noun',
                'definitions': [{'definition': 'A place where books are kept.'}]
            }]
        }])
        mock_getUrl.return_value = mock_response.encode('utf-8')

        self.assertNotError('dict library')
        self.assertResponse('dict library', 'library (noun): A place where books are kept.')

    @patch('Dictionary.plugin.utils.web.getUrl')
    def test_no_definitions(self, mock_getUrl):
        mock_response = json.dumps([])
        mock_getUrl.return_value = mock_response.encode('utf-8')

        self.assertError('dict nonexistentword')

    @patch('Dictionary.plugin.utils.web.getUrl')
    def test_unexpected_format(self, mock_getUrl):
        mock_response = json.dumps({})
        mock_getUrl.return_value = mock_response.encode('utf-8')

        self.assertError('dict unexpectedformat')

    @patch('Dictionary.plugin.utils.web.getUrl')
    def test_json_decode_error(self, mock_getUrl):
        mock_getUrl.return_value = b'invalid json'

        self.assertError('dict invalidjson')

    @patch('Dictionary.plugin.utils.web.getUrl')
    def test_web_error(self, mock_getUrl):
        mock_getUrl.side_effect = utils.web.Error('Web error')

        self.assertError('dict weberror')

    @patch('Dictionary.plugin.utils.web.getUrl')
    def test_unexpected_error(self, mock_getUrl):
        mock_getUrl.side_effect = Exception('Unexpected error')

        self.assertError('dict unexpectederror')

if __name__ == '__main__':
    unittest.main()