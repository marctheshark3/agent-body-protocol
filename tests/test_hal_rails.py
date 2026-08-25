import unittest

from mapper.hal_client import dispatch, get_power, refuse_power_write
from mapper.skills import dispatch_soft
from mapper.trajectory import read_body


class HalLoopbackPinTests(unittest.TestCase):
    def test_dispatch_soft_pins_loopback_and_refuses_power_write(self):
        led = '[HW:/led/solid:{"color":[1,2,3],"transient":true}]'
        with self.assertRaises(ValueError):
            dispatch_soft([led], "http://8.8.8.8:5001")
        with self.assertRaises(ValueError):
            dispatch_soft(['[HW:/power:{"voltage_v":12}]'], "http://127.0.0.1:5001")
        with self.assertRaises(ValueError):
            read_body("http://example.com:5001")
        with self.assertRaises(ValueError):
            get_power("http://example.com:5001")
        with self.assertRaises(ValueError):
            dispatch([led], "http://8.8.8.8:5001")
        with self.assertRaises(ValueError):
            refuse_power_write("/power")
