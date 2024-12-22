import unittest
from unittest.mock import patch, MagicMock
from Weather.plugin import Weather, dd2dms, extract_address_details, colour

# Weather/test_plugin.py


class TestWeather(unittest.TestCase):

    def setUp(self):
        self.weather = Weather(MagicMock())

    def test_colour(self):
        self.assertEqual(colour(-5), '\x0312-5°C\x03')
        self.assertEqual(colour(0), '\x0310.0°C\x03')
        self.assertEqual(colour(5), '\x0311.0°C\x03')
        self.assertEqual(colour(15), '\x0309.0°C\x03')
        self.assertEqual(colour(25), '\x0308.0°C\x03')
        self.assertEqual(colour(35), '\x0307.0°C\x03')
        self.assertEqual(colour(45), '\x0304.0°C\x03')

    def test_dd2dms(self):
        self.assertEqual(dd2dms(53.3478, -6.2597), ('53°20\'52.08" E', '6°15\'34.92" S'))
        self.assertEqual(dd2dms(-53.3478, 6.2597), ('53°20\'52.08" W', '6°15\'34.92" N'))

    def test_extract_address_details(self):
        address_components = [
            {'types': ['locality'], 'short_name': 'Dublin'},
            {'types': ['administrative_area_level_1'], 'short_name': 'D'},
            {'types': ['country'], 'short_name': 'IE'},
            {'types': ['postal_code'], 'short_name': '12345'}
        ]
        location = 'Dublin'
        self.assertEqual(extract_address_details(address_components, location), ('Dublin, D, IE', '12345'))

    @patch('Weather.plugin.utils.web.getUrl')
    def test_google_maps(self, mock_getUrl):
        mock_getUrl.return_value = json.dumps({
            'status': 'OK',
            'results': [{
                'geometry': {'location': {'lat': 53.3478, 'lng': -6.2597}},
                'place_id': 'ChIJL6wn6oAOZ0gRoHExl6nHAAU',
                'address_components': [
                    {'types': ['locality'], 'short_name': 'Dublin'},
                    {'types': ['administrative_area_level_1'], 'short_name': 'D'},
                    {'types': ['country'], 'short_name': 'IE'},
                    {'types': ['postal_code'], 'short_name': '12345'}
                ]
            }]
        }).encode('utf-8')

        result = self.weather.google_maps('Dublin')
        self.assertEqual(result, ('Dublin, D, IE', 53.3478, -6.2597, '12345', 'ChIJL6wn6oAOZ0gRoHExl6nHAAU'))

    @patch('Weather.plugin.utils.web.getUrl')
    def test_weather(self, mock_getUrl):
        mock_getUrl.side_effect = [
            json.dumps({
                'status': 'OK',
                'results': [{
                    'geometry': {'location': {'lat': 53.3478, 'lng': -6.2597}},
                    'place_id': 'ChIJL6wn6oAOZ0gRoHExl6nHAAU',
                    'address_components': [
                        {'types': ['locality'], 'short_name': 'Dublin'},
                        {'types': ['administrative_area_level_1'], 'short_name': 'D'},
                        {'types': ['country'], 'short_name': 'IE'},
                        {'types': ['postal_code'], 'short_name': '12345'}
                    ]
                }]
            }).encode('utf-8'),
            json.dumps({
                'current': {
                    'weather': [{'icon': '01d', 'description': 'clear sky'}],
                    'clouds': 0,
                    'wind_deg': 90,
                    'feels_like': 15,
                    'humidity': 50,
                    'pressure': 1013,
                    'dew_point': 10,
                    'temp': 20,
                    'visibility': 10000,
                    'uvi': 5,
                    'wind_speed': 5
                },
                'lon': -6.2597,
                'lat': 53.3478,
                'timezone_offset': 0,
                'hourly': [{'rain': {'1h': 0}}],
                'daily': []
            }).encode('utf-8')
        ]

        irc = MagicMock()
        msg = MagicMock()
        args = []
        optlist = []

        self.weather.weather(irc, msg, optlist, 'Dublin')
        irc.reply.assert_called_once()

if __name__ == '__main__':
    unittest.main()