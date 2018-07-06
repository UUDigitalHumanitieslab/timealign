from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, RequestFactory

from .views import IntroductionView


class ViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.u1 = User.objects.create_user(username='test1', email='test@test.com', password='secret', is_superuser=True)
        self.u2 = User.objects.create_user(username='test2', email='test@test.com', password='secret')

    def test_introduction(self):
        request = self.factory.get('/introduction')

        request.user = self.u1
        response = IntroductionView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        request.user = AnonymousUser()
        response = IntroductionView.as_view()(request)
        self.assertEqual(response.status_code, 200)

