import csv
import unicodedata

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from annotations.models import Language, Label, Corpus, Document, Fragment, Sentence, Word, Alignment, LabelKey, Annotation
from stats.models import Scenario, ScenarioLanguage
from stats.utils import run_mds


class Command(BaseCommand):
    help = 'Imports Fragments including Labels, directly ready for creating Scenarios'

    def add_arguments(self, parser):
        parser.add_argument('corpus', type=str)
        parser.add_argument('labelkey', type=str)
        parser.add_argument('filenames', type=str, nargs='+')

        parser.add_argument('--delete', action='store_true', dest='delete', default=False,
                            help='Delete existing Fragments (and contents) for this Corpus')

    def handle(self, *args, **options):
        # Retrieve the Corpus from the database, or create it
        corpus, _ = Corpus.objects.get_or_create(title=options['corpus'])
        corpus.tense_based = False
        corpus.save()

        # Retrieve the LabelKey from the database, or create it
        labelkey, _ = LabelKey.objects.get_or_create(title=options['labelkey'])
        labelkey.corpora.add(corpus)
        labelkey.language_specific = True
        labelkey.save()

        if len(options['filenames']) == 0:
            raise CommandError('No documents specified')

        if options['delete']:
            Fragment.objects.filter(document__corpus=corpus).delete()

        for filename in options['filenames']:
            with open(filename, 'r') as f:
                try:
                    process_file(f, corpus, labelkey)
                    self.stdout.write(self.style.SUCCESS('Successfully imported fragments'))
                except Exception as e:
                    raise e


def process_file(file_handler, corpus, key):
    lines = file_handler.read().splitlines()
    csv_reader = csv.reader(lines, delimiter=';')

    for n, row in enumerate(csv_reader):
        # Retrieve the languages from the first row of the .csv-file
        if n == 0:
            language_from, languages_to = retrieve_languages(row)
            continue

        # For every other line, create a Fragment and its Alignments
        with transaction.atomic():
            document_title = row[1]
            sentence_id = 's' + row[2].replace(':', '.')
            full_text = row[3]
            label_title = row[4]

            # Attach language_from to Corpus
            corpus.languages.add(language_from)

            # Create a Document and Fragment
            document, _ = Document.objects.get_or_create(corpus=corpus, title=document_title)
            from_fragment = Fragment.objects.create(language=language_from, document=document)

            # Add Labels or Tense (the default) to Fragment
            if label_title:
                label, _ = Label.objects.get_or_create(key=key, language=language_from, title=label_title)
                from_fragment.labels.add(label)
            from_fragment.save()

            # Add Sentence and Words
            sentence = Sentence.objects.create(fragment=from_fragment, xml_id=sentence_id)
            targets = attach_words(sentence, full_text, label_title)

            for target in targets:
                target.is_target = True
                target.save()

            for column, language_to in languages_to.items():
                label_title = row[column]
                full_text = row[column - 1]

                # Attach language_to to Corpus
                corpus.languages.add(language_to)

                # Create Fragment
                to_fragment = Fragment.objects.create(language=language_to, document=document)

                # Add Sentence and Words to Fragment
                sentence = Sentence.objects.create(fragment=to_fragment, xml_id=sentence_id)
                targets = attach_words(sentence, full_text, label_title)

                # Create Alignment and Annotation
                alignment = Alignment.objects.create(original_fragment=from_fragment,
                                                     translated_fragment=to_fragment,
                                                     type='1 => 1')
                annotation = Annotation.objects.create(alignment=alignment)

                # Add target Words to Annotation
                for target in targets:
                    annotation.words.add(target)

                # Add Label to Annotation
                if label_title:
                    label, _ = Label.objects.get_or_create(key=key, language=language_to, title=label_title)
                    annotation.labels.add(label)

    # Create default Scenario
    scenario, _ = Scenario.objects.get_or_create(corpus=corpus, title=corpus.title)
    scenario.description = 'Automatically generated Scenario for Corpus {}'.format(corpus.title)
    scenario.save()

    # Attach Languages to Scenario
    attach_language(scenario, language_from, key, as_from=True)
    for language_to in languages_to.values():
        attach_language(scenario, language_to, key, as_from=False)

    # Run multidimensional scaling
    run_mds(scenario)
    scenario.last_run = timezone.now()
    scenario.save()


def attach_language(scenario, language, key, as_from):
    """
    Attaches a Language to a Scenario via creating a ScenarioLanguage object.
    """
    as_to = not as_from
    sl, _ = ScenarioLanguage.objects.get_or_create(scenario=scenario, language=language,
                                                   as_from=as_from, as_to=as_to)
    sl.use_tenses = False
    sl.use_labels = True
    sl.include_keys.add(key)
    sl.save()


def attach_words(sentence, full_text, label_title):
    """
    Attached Words based on a tokenized full text to a Sentence and finds target Words.
    """
    targets = []
    label_parts = label_title.split('=')  # TODO: make this a parameter of some sort
    for i, word in enumerate(full_text.split(), start=1):  # Assumes that the input is tokenized
        xml_id = sentence.xml_id.replace('s', 'w') + '.' + str(i)
        w = Word.objects.create(sentence=sentence, xml_id=xml_id, word=word)

        # Find the target Words and add them to the list of targets.
        # This is a bit iffy as potentially this matches an earlier occurrence in the sentence.
        if label_parts and remove_accents(word.lower()) == label_parts[0].lower():
            targets.append(w)
            label_parts.pop(0)
    return targets


def retrieve_languages(row):
    """
    Retrieves the Languages based on the header row of the .csv-file.
    """
    language_from = Language.objects.get(iso=row[4])

    languages_to = dict()
    for i in range(6, len(row), 2):
        try:
            languages_to[i] = Language.objects.get(iso=row[i])
        except Language.DoesNotExist:
            raise ValueError('Unknown language code: {}'.format(row[i]))
    return language_from, languages_to


def remove_accents(input_str):
    """
    Removes accents from an input string.
    Solution taken from https://stackoverflow.com/a/517974/3710392
    """
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
