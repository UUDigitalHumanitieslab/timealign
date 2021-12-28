from importlib import import_module

from django.conf import settings
from django.test import Client
from django.urls import reverse

from annotations.test_models import BaseTestCase


def construct_url_from_pattern(url_pattern):
    url_pattern = url_pattern.strip()
    reversed_url = None
    if len(url_pattern) > 0:
        if "___" in url_pattern:
            url_parts = url_pattern.split("___")
            params = tuple([str(x) for x in url_parts[1].split(",")])
            reversed_url = reverse(url_parts[0], args=params)
        else:
            reversed_url = reverse(url_pattern)
    return reversed_url


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
            stats:show___1
            stats:mds___1
            stats:mds___1,1
            stats:mds___1,1,1,1
            stats:descriptive___1
            stats:upset___1
            stats:upset___1,1
            stats:sankey___1
            annotations:show___1

            stats:fragment_table
            stats:fragment_table_mds
        """
        url_patterns = public_url_patterns.split('\n')
        for url_pattern in url_patterns:
            reversed_url = construct_url_from_pattern(url_pattern)
            if reversed_url is not None:
                print("testing redirect on url:", reversed_url)
                self.assertRedirects(self.client.get(reversed_url), reverse('stats:captcha_test'), 302, 200)

        session = self.client.session
        session['succeed-captcha'] = True
        session.save()
        for url_pattern in url_patterns:
            reversed_url = construct_url_from_pattern(url_pattern)
            if reversed_url is not None:
                print("testing success on url:", reversed_url)
                http_code = self.client.get(reversed_url).status_code
                self.assertTrue(http_code == 200 or http_code == 404)

    def test_non_public_urls_even_with_captcha(self):
        non_public_url_patterns = """
            annotations:status
            annotations:status___1
            annotations:create___1,1
            annotations:edit___1
            annotations:delete___1
            annotations:show___1
            annotations:show_plain___1
            annotations:edit_fragment___1
            annotations:corpora
            annotations:corpus___1
            annotations:document___1
            annotations:source___1
            annotations:list___1,1
            annotations:matrix___1
            annotations:tense_matrix___1,1
            annotations:tenses
            annotations:labels
            annotations:labels___1
            annotations:import-labels
            annotations:add-fragments

            selections:instructions___1
            selections:status
            selections:status___1
            selections:create___1
            selections:edit___1
            selections:delete___1
            selections:choose___1,1
            selections:choose___1
            selections:list___1
            selections:add-fragments
            selections:convert-selections

            stats:download___1

            admin:index
            admin:view_on_site
            admin:app_list___1

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
            reversed_url = construct_url_from_pattern(url_pattern)
            if reversed_url is not None:
                print("testing unauthenticated on url:", reversed_url)
                http_code = self.client.get(reversed_url).status_code
                self.assertTrue(http_code == 302 or http_code == 403)

    # NOTE: These are helpers code

    # self.print_urls('root', get_resolver().url_patterns)

    # def print_urls(self, app_name, url_patterns):
    #     from django.urls import URLPattern
    #     from django.urls import URLResolver
    #     app_names_to_exclude = ["root", "None"]
    #     for url_item in url_patterns:
    #         if isinstance(url_item, URLPattern) and app_name not in app_names_to_exclude:
    #             pattern_to_print = app_name + ":" + str(url_item.name)
    #             url_pattern = str(url_item.pattern)
    #             if "(?P" in url_pattern:
    #                 parameters = "(" + ",".join(["\"1\"" for i in range(url_pattern.count("(?P"))]) + ")"
    #                 pattern_to_print += "___" + parameters
    #             print(pattern_to_print)
    #         elif isinstance(url_item, URLResolver):
    #             self.print_urls(str(url_item.app_name), url_item.url_patterns)

    # public_url_patterns = """
    #     annotations:introduction
    #     annotations:instructions___1
    #     annotations:status
    #     annotations:status___1
    #     annotations:create___1,1
    #     annotations:edit___1
    #     annotations:delete___1
    #     annotations:choose___1,1,1
    #     annotations:choose___1,1
    #     annotations:show___1
    #     annotations:show_plain___1
    #     annotations:edit_fragment___1
    #     annotations:corpora
    #     annotations:corpus___1
    #     annotations:document___1
    #     annotations:source___1
    #     annotations:list___1,1
    #     annotations:matrix___1
    #     annotations:tense_matrix___1,1
    #     annotations:tenses
    #     annotations:labels
    #     annotations:labels___1
    #     annotations:prepare_download___1,1
    #     annotations:prepare_download___1
    #     annotations:download_start
    #     annotations:download_ready
    #     annotations:import-labels
    #     annotations:add-fragments

    #     selections:introduction
    #     selections:instructions___1
    #     selections:status
    #     selections:status___1
    #     selections:create___1
    #     selections:edit___1
    #     selections:delete___1
    #     selections:choose___1,1
    #     selections:choose___1
    #     selections:list___1
    #     selections:prepare_download___1,1
    #     selections:prepare_download___1
    #     selections:download_start
    #     selections:download_ready
    #     selections:add-fragments
    #     selections:convert-selections

    #     stats:scenarios
    #     stats:scenarios_manual
    #     stats:show___1
    #     stats:download___1
    #     stats:mds___1
    #     stats:mds___1,1
    #     stats:mds___1,1,1,1
    #     stats:mds_old___1
    #     stats:mds_old___1,1
    #     stats:mds_old___1,1,1,1
    #     stats:fragment_table
    #     stats:fragment_table_mds
    #     stats:upset___1
    #     stats:upset___1,1
    #     stats:sankey___1
    #     stats:sankey_manual
    #     stats:descriptive___1
    #     stats:captcha_test

    #     news:posts
    #     news:show___1

    #     admin:index
    #     admin:login
    #     admin:logout
    #     admin:password_change
    #     admin:password_change_done
    #     admin:autocomplete
    #     admin:jsi18n
    #     admin:view_on_site
    #     admin:app_list___1
    #     admin:None___1

    #     perfectextractor_ui:home
    #     perfectextractor_ui:run
    #     perfectextractor_ui:status
    #     perfectextractor_ui:peek
    #     perfectextractor_ui:cancel
    #     perfectextractor_ui:download
    #     perfectextractor_ui:import_query
    #     perfectextractor_ui:help
    # """
