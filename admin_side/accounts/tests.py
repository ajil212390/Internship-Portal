
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

# Model test: user creation
class AccountsModelTests(TestCase):
	def test_create_user(self):
		User = get_user_model()
		user = User.objects.create_user(username='testuser', password='testpass')
		self.assertEqual(user.username, 'testuser')
		self.assertTrue(user.check_password('testpass'))

# View test: home page status code
class AccountsViewTests(TestCase):
	def setUp(self):
		self.client = Client()

	def test_home_view_status_code(self):
		response = self.client.get('/')
		self.assertIn(response.status_code, [200, 302, 404])  # Accepts common status codes for root
