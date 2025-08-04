import unittest, tempfile, os
from app import app, init_db

class AppTestCase(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp()
        app.config['DATABASE'] = path
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def tearDown(self):
        os.close(app.config['DATABASE'])
        os.unlink(app.config['DATABASE'])

    def test_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Court Data Fetcher', resp.data)

    def test_empty_search(self):
        resp = self.client.post('/search', data={})
        self.assertEqual(resp.status_code, 302)

if __name__ == '__main__':
    unittest.main()
