# Run this with from inside the python directory
# ./python$ python -m unittest test_fg.py

import unittest
from datetime import datetime, timedelta, timezone

from fg_lib import *

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
    
    def test_parse_sember(self):
        self.assertEqual(parse_semver("v1.2.3"), (1,2,3))
        self.assertEqual(parse_semver("v0.12.30"), (0, 12, 30))
        self.assertEqual(parse_semver("v2.3.02"), (2, 3, 2))
        self.assertEqual(parse_semver("v1.12.23"), (1, 12, 23))
        self.assertEqual(parse_semver("v10.20.30"), (10, 20, 30))
        
        self.assertEqual(parse_semver("V1.2.3"), (1,2,3))

        self.assertEqual(parse_semver("0.2.3"), (0,2,3))
        self.assertEqual(parse_semver("10.20.30"), (10, 20, 30))

        self.assertRaises(ValueError, parse_semver, "10.20")
        self.assertRaises(ValueError, parse_semver, "1.2.a")

    def test_semver_compare(self):
        v1_2_3 = SemVer(1,2,3)
        v0_1_3 = SemVer(0,1,3)

        self.assertEqual(semver_compare(v1_2_3, v0_1_3), 1)
        self.assertEqual(semver_compare(v1_2_3, v1_2_3), 0)
        self.assertEqual(semver_compare(v0_1_3, v0_1_3), 0)
        self.assertEqual(semver_compare(v0_1_3, v1_2_3), -1)