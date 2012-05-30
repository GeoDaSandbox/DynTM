"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
import urllib

SERVICE_URI = "http://apps2.geodacenter.org/classifier"
class SimpleTest(TestCase):
    def test_quantile_get(self):
        """
        Test Case from the Docs...
        """
        url = "%s?METHOD=quantile&VALUES=1,2,3,4,5,6,7,8,9,10&NOCLS=2"%SERVICE_URI
        r = urllib.urlopen(url)
        expect_result = '{"status": "success", "k": 2, "id2colorclass": "2,2,2,2,2,3,3,3,3,3", "breakpoint": "1.00 -- 5.50,5.50 -- 10.00"}'
        self.failUnlessEqual(r.read(), expect_result)
    def test_quantile_post(self):
        """
        Test Case from the Docs...
        """
        data = {}
        data["METHOD"] = "quantile"
        data["VALUES"] = "1,2,3,4,5,6,7,8,9,10"
        data["NOCLS"] = "2"
        r = urllib.urlopen(SERVICE_URI,urllib.urlencode(data))
        expect_result = '{"status": "success", "k": 2, "id2colorclass": "2,2,2,2,2,3,3,3,3,3", "breakpoint": "1.00 -- 5.50,5.50 -- 10.00"}'
        self.failUnlessEqual(r.read(), expect_result)

