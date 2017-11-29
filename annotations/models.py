from django.conf import settings
from django.db import models


class Language(models.Model):
    iso = models.CharField(max_length=2, unique=True)
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return self.title


class TenseCategory(models.Model):
    title = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = 'Tense categories'

    def __unicode__(self):
        return self.title


class Tense(models.Model):
    title = models.CharField(max_length=200)

    language = models.ForeignKey(Language)
    category = models.ForeignKey(TenseCategory)

    class Meta:
        unique_together = ('language', 'title', )

    def __unicode__(self):
        return u'{} ({})'.format(self.title, self.language.iso)


class Corpus(models.Model):
    title = models.CharField(max_length=200, unique=True)
    languages = models.ManyToManyField(Language)
    annotators = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    check_structure = models.BooleanField(
        'Check for formal structure in the Annotations',
        default=False)

    class Meta:
        verbose_name_plural = 'Corpora'

    def __unicode__(self):
        return self.title

    def get_languages(self):
        return ', '.join([language.iso for language in self.languages.all()])

    get_languages.short_description = 'Languages'

    def get_annotators(self):
        result = 'none'
        if self.annotators.exists():
            result = ', '.join([user.username for user in self.annotators.all()])
        return result

    get_annotators.short_description = 'Annotators'


class Document(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True)

    corpus = models.ForeignKey(Corpus)

    class Meta:
        unique_together = ('corpus', 'title', )

    def __unicode__(self):
        return self.title


class Fragment(models.Model):
    language = models.ForeignKey(Language)
    document = models.ForeignKey(Document)

    tense = models.ForeignKey(Tense, null=True)
    other_label = models.CharField(max_length=200, blank=True)

    def to_html(self):
        result = '<ul>'
        for sentence in self.sentence_set.all():
            result += sentence.to_html()
        result += '</ul>'
        return result

    def target_words(self):
        """
        Retrieves the target words for this Fragment.
        :return: A list of Strings with the target Words.
        """
        result = []
        for sentence in self.sentence_set.all():
            result.extend([word.word for word in sentence.word_set.filter(is_target=True)])
        return ' '.join(result)

    def get_alignments(self, as_original=False, as_translation=False):
        alignments = Alignment.objects.none()
        if as_original:
            alignments |= Alignment.objects.filter(original_fragment=self)
        if as_translation:
            alignments |= Alignment.objects.filter(translated_fragment=self)
        return alignments

    def get_annotations(self):
        """
        Returns all Annotations for this Fragment, in all selected languages
        :return: A list of Annotations per language, with None if there's no Annotation or Alignment for this Fragment.
        """
        result = []
        other_languages = self.document.corpus.languages.exclude(pk=self.language.pk)
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

    def full(self, marked=False):
        return '\n'.join([sentence.full(marked) for sentence in self.sentence_set.all()])

    def label(self):
        return self.tense.title if self.tense else self.other_label

    def formal_structure(self):
        result = 'narration'
        for sentence in self.sentence_set.all():
            for word in sentence.word_set.all():
                if word.is_in_dialogue:
                    result = 'dialogue'
        return result

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

    def full(self, marked=False):
        words = []
        for word in self.word_set.all():
            if marked and word.is_target:
                words.append('<strong>' + word.word + '</strong>')
            else:
                words.append(word.word)
            if marked and len(words) % 20 == 0:
                words.append('<br>')
        return ' '.join(words)

    def __unicode__(self):
        return self.full()[:100] + '...'


class Word(models.Model):
    xml_id = models.CharField(max_length=20)
    word = models.CharField(max_length=200)
    pos = models.CharField(max_length=50)
    lemma = models.CharField(max_length=200, blank=True)

    is_target = models.BooleanField(default=False)

    is_in_dialogue = models.BooleanField(default=False)
    is_in_dialogue_prob = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

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
        'The selected words in the original fragment do not form an instance of (a/an) <em>{}</em>',
        default=False)
    is_translation = models.BooleanField(
        'This is a correct translation of the original fragment',
        default=True)

    is_not_labeled_structure = models.BooleanField(
        'The selected words in the original fragment are incorrectly marked as <em>{}</em>',
        default=False
    )
    is_not_same_structure = models.BooleanField(
        'The translated fragment is not in the same structure (dialogue/narrative) as the original fragment',
        default=False
    )

    words = models.ManyToManyField(Word, blank=True)
    comments = models.TextField(blank=True)
    alignment = models.ForeignKey(Alignment)

    annotated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='annotated_by')
    annotated_at = models.DateTimeField(auto_now_add=True)

    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='last_modified_by')
    last_modified_at = models.DateTimeField(auto_now=True)

    tense = models.ForeignKey(Tense, null=True)
    other_label = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('alignment', 'annotated_by', )

    def selected_words(self):
        # TODO: is there a way to order on part of the id?! Or add an extra field...
        return ' '.join([word.word for word in self.words.all().order_by('xml_id')])

    def label(self):
        return self.tense.title if self.tense else self.other_label
