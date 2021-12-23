from importlib import import_module

from django.conf import settings
from django.test import Client
from django.urls import reverse

from annotations.test_models import BaseTestCase


class PublicViewsTestCase(BaseTestCase):

    def setUp(self):
        super(PublicViewsTestCase, self).setUp()

        self.client = Client()
        # http://code.djangoproject.com/ticket/10899
        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    def test_public_urls_before_and_after_captcha(self):
        public_url_patterns = """
            stats:scenarios
            stats:show
            stats:mds
            stats:fragment_table
            stats:fragment_table_mds
            stats:descriptive
            stats:upset
            stats:sankey
            stats:sankey_manual
            annotations:show
        """
        url_patterns = public_url_patterns.split('\n')
        for url_pattern in url_patterns:
            url_pattern = url_pattern.strip()
            if len(url_pattern) > 0:
                self.assertRedirects(self.client.get(reverse(url_pattern)), reverse('stats:captcha_test'), 302, 200)

        session = self.client.session
        session['succeed-captcha'] = True
        session.save()
        for url_pattern in url_patterns:
            url_pattern = url_pattern.strip()
            if len(url_pattern) > 0:
                self.assertEqual(self.client.get(reverse(url_pattern)).status_code, 200)

    def test_non_public_urls_even_with_captcha(self):
        non_public_url_patterns = """
            annotations:status
            annotations:create
            annotations:edit
            annotations:delete
            annotations:show
            annotations:show_plain
            annotations:edit_fragment
            annotations:corpora
            annotations:corpus
            annotations:document
            annotations:source
            annotations:list
            annotations:matrix
            annotations:tense_matrix
            annotations:tenses
            annotations:labels
            annotations:prepare_download
            annotations:import-labels
            annotations:add-fragments
            selections:introduction
            selections:instructions
            selections:status
            selections:create
            selections:edit
            selections:delete
            selections:choose
            selections:list
            selections:prepare_download
            selections:add-fragments
            selections:convert-selections
            stats:download
            admin:index
            admin:view_on_site
            admin:app_list
            perfectextractor_ui:home
            perfectextractor_ui:run
            perfectextractor_ui:status
            perfectextractor_ui:peek
            perfectextractor_ui:cancel
            perfectextractor_ui:download
            perfectextractor_ui:import_query
            perfectextractor_ui:help
        """
        session = self.client.session
        session['succeed-captcha'] = True
        session.save()

        url_patterns = non_public_url_patterns.split('\n')
        for url_pattern in url_patterns:
            url_pattern = url_pattern.strip()
            if len(url_pattern) > 0:
                self.assertEqual(self.client.get(reverse(url_pattern)).status_code, 302)

    # NOTE: These are helpers code

    # self.print_urls('root', get_resolver().url_patterns)

    # def print_urls(self, app_name, url_patterns):
    #     from django.urls import URLPattern
    #     from django.urls import URLResolver
    #     for url_item in url_patterns:
    #         if isinstance(url_item, URLPattern):
    #             print(app_name + ":" + str(url_item.name))
    #         elif isinstance(url_item, URLResolver):
    #             new_app_name = app_name + " _ " + str(url_item.app_name)
    #             self.print_urls(new_app_name, url_item.url_patterns)

    # public_url_patterns = """
    #     annotations:introduction
    #     annotations:instructions
    #     annotations:status
    #     annotations:create
    #     annotations:edit
    #     annotations:delete
    #     annotations:choose
    #     annotations:show
    #     annotations:show_plain
    #     annotations:edit_fragment
    #     annotations:corpora
    #     annotations:corpus
    #     annotations:document
    #     annotations:source
    #     annotations:list
    #     annotations:matrix
    #     annotations:tense_matrix
    #     annotations:tenses
    #     annotations:labels
    #     annotations:prepare_download
    #     annotations:download_start
    #     annotations:download_ready
    #     annotations:import-labels
    #     annotations:add-fragments
    #     selections:introduction
    #     selections:instructions
    #     selections:status
    #     selections:create
    #     selections:edit
    #     selections:delete
    #     selections:choose
    #     selections:list
    #     selections:prepare_download
    #     selections:download_start
    #     selections:download_ready
    #     selections:add-fragments
    #     selections:convert-selections
    #     stats:scenarios
    #     stats:scenarios_manual
    #     stats:show
    #     stats:download
    #     stats:mds
    #     stats:mds_old
    #     stats:fragment_table
    #     stats:fragment_table_mds
    #     stats:upset
    #     stats:sankey
    #     stats:sankey_manual
    #     stats:descriptive
    #     stats:captcha_test
    #     news:posts
    #     news:show
    #     admin:index
    #     admin:view_on_site
    #     admin:app_list
    #     home
    #     project
    #     nl-summary
    #     collaborations
    #     videos
    #     publications
    #     student-research
    #     workshops
    #     expert-meetings
    #     perfectextractor
    #     translation-mining
    #     contact
    #     perfectextractor_ui:home
    #     perfectextractor_ui:run
    #     perfectextractor_ui:status
    #     perfectextractor_ui:peek
    #     perfectextractor_ui:cancel
    #     perfectextractor_ui:download
    #     perfectextractor_ui:import_query
    #     perfectextractor_ui:help
    # """
