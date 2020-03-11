from django.test import TestCase, Client

class ErrorPages(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_404(self):
        """ if page not found, return 404 """
        response = self.client.get('/a/page/that/definitely/does/not/exist/')
        self.assertEqual(response.status_code, 404, 
            "if page is not found, server must return status code 404")
