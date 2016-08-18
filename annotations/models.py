from django.conf import settings
from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.title


class Fragment(models.Model):
    GERMAN = 'de'
    ENGLISH = 'en'
    SPANISH = 'es'
    FRENCH = 'fr'
    DUTCH = 'nl'
    LANGUAGES = (
        (GERMAN, 'German'),
        (ENGLISH, 'English'),
        (SPANISH, 'Spanish'),
        (FRENCH, 'French'),
        (DUTCH, 'Dutch'),
    )
    language = models.CharField(max_length=2, choices=LANGUAGES)
    speaker_language = models.CharField(max_length=2, choices=LANGUAGES)

    document = models.ForeignKey(Document)

    def to_html(self):
        result = '<ul>'
        for sentence in self.sentence_set.all():
            result += sentence.to_html()
        result += '</ul>'
        return result

    def target_words(self):
        """
        Retrieves the target words for this Fragment.
        :return: A list of Strings with the target words.
        """
        result = []
        for sentence in self.sentence_set.all():
            result.extend([word.word for word in sentence.word_set.filter(is_target=True)])
        return ' '.join(result)

    def get_annotations(self):
        """
        Returns all Annotations for this Fragment, in all selected LANGUAGES
        :return: A list of Annotations per LANGUAGE, with None if there's no Annotation or Alignment for this Fragment.
        """
        result = []
        other_languages = [l for l, _ in self.LANGUAGES if l != self.language]
        for language in other_languages:
            # Note that there should be only one Alignment per language, so we can use .first() here.
            alignment = self.original.filter(translated_fragment__language=language).first()
            if alignment:
                # TODO: We currently consider only one Annotation per Alignment, YMMV.
                annotation = alignment.annotation_set.first()
                if annotation:
                    result.append(annotation)
                else:
                    result.append(None)  # This happens if there's no Annotation yet
            else:
                result.append(None)  # This happens if there's no Alignment for this Fragment in the given language
        return result

    def full(self):
        return '\n'.join([sentence.full() for sentence in self.sentence_set.all()])

    def __unicode__(self):
        return self.full()[:100]


class Sentence(models.Model):
    xml_id = models.CharField(max_length=20)

    fragment = models.ForeignKey(Fragment)

    def to_html(self):
        result = '<li>'
        for word in self.word_set.all():
            result += word.to_html() + ' '
        result += '</li>'
        return result

    def full(self):
        return ' '.join([word.word for word in self.word_set.all()])

    def __unicode__(self):
        return self.full()[:100] + '...'


class Word(models.Model):
    xml_id = models.CharField(max_length=20)
    word = models.CharField(max_length=200)
    pos = models.CharField(max_length=10)
    lemma = models.CharField(max_length=200, null=True)
    is_target = models.BooleanField(default=False)

    sentence = models.ForeignKey(Sentence)

    def to_html(self):
        return u'<strong>{}</strong>'.format(self.word) if self.is_target else self.word

    def __unicode__(self):
        return self.word


class Alignment(models.Model):
    type = models.CharField(max_length=10)

    original_fragment = models.ForeignKey(Fragment, null=True, related_name='original')
    translated_fragment = models.ForeignKey(Fragment, null=True, related_name='translated')


class Annotation(models.Model):
    is_no_target = models.BooleanField(
        'The selected words in the original fragment do not form a present perfect',
        default=False)
    is_translation = models.BooleanField(
        'This is a correct translation of the original fragment',
        default=True)

    words = models.ManyToManyField(Word, blank=True)
    alignment = models.ForeignKey(Alignment)

    annotated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='annotated_by')
    annotated_at = models.DateTimeField(auto_now_add=True)

    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='last_modified_by')
    last_modified_at = models.DateTimeField(auto_now=True)

    tense = models.CharField('Tense of translation', max_length=200, blank=True)
    # person = models.CharField(max_length=2, blank=True)  # single vs. plural
    # mood = models.CharField(max_length=2, blank=True)  # indicative (hard?)
    # voice = models.CharField(max_length=2, blank=True)  # active vs. passive (hard?)

    class Meta:
        unique_together = ('alignment', 'annotated_by', )

    def selected_words(self):
        # TODO: is there a way to order on part of the id?! Or add an extra field...
        return ' '.join([word.word for word in self.words.all().order_by('xml_id')])