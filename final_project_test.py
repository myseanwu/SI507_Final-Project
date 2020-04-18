import unittest
import darksky_api as ds

# SI 507 Winter 2020
# Final Project: Hsin-Yuan Wu | wusean

class Test_location_check(unittest.TestCase):
    def setUp(self):
        self.location_1 = ds.location_check('Ann Arbor')
        self.location_2 = ds.location_check('taipei')

    def test_location_check_return_type(self):
        self.assertEqual(type(self.location_1), str)
        self.assertEqual(type(self.location_2), str)

    # def test_1_2_return_length(self):
    #     self.assertEqual(len(self.state_url), 56)
    
    def test_location_check_contents(self):
        self.assertEqual(self.location_1, '42.2682,-83.7312')
        self.assertEqual(self.location_2, '25.0333,121.6333')


class Test_weather(unittest.TestCase):
    def setUp(self):
        self.weather_aa = ds.weather_data('Ann Arbor') # Ann Arbor
        self.weather_tpe = ds.weather_data('taipei') # Taipei
    
    def test_weather_1_type(self):
        self.assertEqual(type(self.weather_aa.total), dict)
        self.assertEqual(type(self.weather_tpe.total), dict)
        self.assertEqual(type(self.weather_aa.wk_time), list)
        self.assertEqual(type(self.weather_tpe.wk_time), list)
        self.assertEqual(type(self.weather_aa.daily_sum), list)
        self.assertEqual(type(self.weather_tpe.daily_sum), list)
        self.assertEqual(type(self.weather_aa.comment), list)
        self.assertEqual(type(self.weather_tpe.comment), list)
        self.assertEqual(type(self.weather_aa.sunrise), list)
        self.assertEqual(type(self.weather_tpe.sunrise), list)
        self.assertEqual(type(self.weather_aa.sunset), list)
        self.assertEqual(type(self.weather_tpe.sunset), list)
        self.assertEqual(type(self.weather_aa.precipitation_prob), list)
        self.assertEqual(type(self.weather_tpe.precipitation_prob), list)
        self.assertEqual(type(self.weather_aa.temp_high), list)
        self.assertEqual(type(self.weather_tpe.temp_high), list)
        self.assertEqual(type(self.weather_aa.temp_low), list)
        self.assertEqual(type(self.weather_tpe.temp_low), list)
        self.assertEqual(type(self.weather_aa.humid), list)
        self.assertEqual(type(self.weather_tpe.humid), list)
        self.assertEqual(type(self.weather_aa.uv_index), list)
        self.assertEqual(type(self.weather_tpe.uv_index), list)

    def test_weather_2_len(self):
        self.assertEqual(len(self.weather_aa.daily_sum), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.daily_sum), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.comment), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.comment), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.sunrise), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.sunrise), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.sunset), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.sunset), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.precipitation_prob), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.precipitation_prob), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.temp_high), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.temp_high), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.temp_low), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.temp_low), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.humid), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.humid), len(self.weather_tpe.wk_time))
        self.assertEqual(len(self.weather_aa.uv_index), len(self.weather_aa.wk_time))
        self.assertEqual(len(self.weather_tpe.uv_index), len(self.weather_tpe.wk_time))


    def test_weather_3_timezone(self):
        self.assertEqual(self.weather_aa.timezone, "America/Detroit")
        self.assertEqual(self.weather_tpe.timezone, "Asia/Taipei")




if __name__ == '__main__':
    unittest.main()
