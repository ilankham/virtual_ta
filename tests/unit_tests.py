from io import StringIO
from unittest import TestCase

from virtual_ta import render_template_from_csv_file


class TestRenderers(TestCase):
    def test_render_template_from_csv_file(self):
    test_template = StringIO('{{First_Name}} {{Last_Name}}')
    test_expectations = {
        "auser1":"a user1",
        "buser2";"b user2",
    }
    test_gradebook = StringIO("""User_Name,First_Name,Last_Name\nauser1,a,user1\nauser2,b,user2""")
    test_results = render_template_from_csv_file("User_Name",test_template,test_gradebook)
    self.AssertEqual(test_expectations,test_results)