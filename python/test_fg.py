# comment main() at end of fg.py and run this with python$ python -m unittest test_fg.py

import unittest
from datetime import datetime, timedelta, timezone
import fg
from fg import *

class TestFgTestCase(unittest.TestCase):
    # def setUp(self):
    #     pass

    def test_parse_time_string(self):
        self.assertEqual(parse_time_string("17h 39m 23s"), timedelta(days=0, hours=17, minutes=39, seconds=23))
        self.assertEqual(parse_time_string("1day 10h 18m 6s"), timedelta(days=1, hours=10, minutes=18, seconds=6))
        self.assertEqual(parse_time_string("2days 10h 18m 6s"), timedelta(days=2, hours=10, minutes=18, seconds=6))
        self.assertEqual(parse_time_string("2days 5h 15m"), timedelta(days=2, hours=5, minutes=15, seconds=0))
        self.assertEqual(parse_time_string("2days 5h 6s"), timedelta(days=2, hours=5, minutes=0, seconds=6))
        self.assertEqual(parse_time_string("2days 5m 6s"), timedelta(days=2, hours=0, minutes=5, seconds=6))
    
    def test_parse_row(self):
        self.assertEqual(parse_row(r"| DdLwVYuvDz26JohmgSbA7mjpJFgX5zP2dkp8qsF2C33V | v1.16.0 | 497 | 557 | [Limit loaded data per transaction to a fixed cap](https://github.com/solana-labs/solana/issues/27839) | @taozhu-chicago | |"), 
                         FeatureGate("DdLwVYuvDz26JohmgSbA7mjpJFgX5zP2dkp8qsF2C33V", "v1.16.0", "497", "557", "Limit loaded data per transaction to a fixed cap", "https://github.com/solana-labs/solana/issues/27839", "@taozhu-chicago"))

