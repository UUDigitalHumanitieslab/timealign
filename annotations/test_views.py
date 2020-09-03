from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from .test_models import BaseTestCase


class ViewsTestCase(BaseTestCase):
    def setUp(self):
        super(ViewsTestCase, self).setUp()

        self.client = Client()

    def test_introduction(self):
        response = self.client.get(reverse('annotations:introduction'))
        self.assertEqual(response.status_code, 200)

    def test_status(self):
        response = self.client.get(reverse('annotations:status'))
        self.assertEqual(response.status_code, 302)  # Login required!

        self.client.login(username=self.u1.username, password='secret')
        response = self.client.get(reverse('annotations:status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.u1)
        self.assertEqual(response.context['languages'][0], (self.en, self.nl, 0, 1))

    def test_annotation_create(self):
        response = self.client.get(reverse('annotations:create', args=(self.c1.pk, self.alignment.pk,)))
        self.assertEqual(response.status_code, 302)  # Login required!

        self.client.login(username=self.u1.username, password='secret')
        response = self.client.get(reverse('annotations:create', args=(self.c1.pk, self.alignment.pk,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(username=self.u2.username, password='secret')
        response = self.client.get(reverse('annotations:create', args=(self.c1.pk, self.alignment.pk,)))
        self.assertEqual(response.status_code, 403)  # Permission required!

        self.u2.user_permissions.add(Permission.objects.get(content_type__app_label='annotations',
                                                            codename='change_annotation'))
        response = self.client.get(reverse('annotations:create', args=(self.c1.pk, self.alignment.pk,)))
        self.assertEqual(response.status_code, 200)
