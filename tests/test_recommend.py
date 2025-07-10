import unittest
from app import app
from flask import url_for
from io import BytesIO

class RecommendBlogTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()

        # Login simulasi (ganti dengan user test ID nyata jika perlu)
        with self.app.session_transaction() as sess:
            sess['_user_id'] = "2"  # diasumsikan ada user dengan ID 2 selain admin

    def tearDown(self):
        self.ctx.pop()

    def test_upload_recommendation_form(self):
        data = {
            'title': 'Judul Test',
            'notes': 'Catatan test',
            'file': (BytesIO(b"isi file test"), 'test_upload.pdf')
        }

        response = self.app.post(
            "/recommend",
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Rekomendasi berhasil dikirim", response.data)

if __name__ == "__main__":
    unittest.main()
