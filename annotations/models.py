from django.conf import settings
from django.db import models

from core.utils import check_format, CSV, HTML, XLSX, COLOR_LIST


class HasLabelsMixin:
    def labels_pretty(self):
        labels = []
        if self.tense:
            labels.append(self.tense.title)
        labels.extend(label.title for label in self.labels.all())
        return ', '.join(labels)

    def get_labels(self, as_pk=False, include_tense=True, include_labels=False, include_keys=None):
        if as_pk:
            out = []
            if include_tense and self.tense:
                out.append('Tense:{}'.format(self.tense.pk))
            if include_labels:
                if not include_keys:
                    out.extend('Label:{}'.format(label.pk) for label in self.labels.all())
                else:
                    out.extend('Label:{}'.format(label.pk) for label in self.labels.filter(key__in=include_keys))
            return tuple(out)
        return self.labels_pretty()

    @property
    def label(self):
        return self.get_labels()

    def label_colors(self):
        label_colors = dict()
        if self.tense:
            label_colors[self.tense.title] = (self.tense.category.title, self.tense.category.color)
        for i, label in enumerate(self.labels.all().prefetch_related('key')):
            label_colors[label] = (label.key.title, label.color or COLOR_LIST[i % len(COLOR_LIST)])
        return label_colors


class Language(models.Model):
    iso = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class TenseCategory(models.Model):
    title = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=10)

    class Meta:
        verbose_name_plural = 'Tense categories'

    def __str__(self):
        return self.title


class Tense(models.Model):
    title = models.CharField(max_length=200)

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    category = models.ForeignKey(TenseCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('language', 'title', )

    def __str__(self):
        return self.title


class Corpus(models.Model):
    title = models.CharField(max_length=200, unique=True)
    languages = models.ManyToManyField(Language)
    annotators = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    current_subcorpus = models.ForeignKey(
        'SubCorpus', blank=True, null=True, related_name='current_subcorpus', on_delete=models.SET_NULL)

    tense_based = models.BooleanField(
        'Check this to use tenses for annotation, uncheck to configure labels',
        default=True)

    check_structure = models.BooleanField(
        'Check for formal structure in the Annotations',
        default=False)

    class Meta:
        verbose_name_plural = 'Corpora'

    def __str__(self):
        return self.title

    def get_languages(self):
        return ', '.join([language.iso for language in self.languages.all()])

    get_languages.short_description = 'Languages'

    def get_annotators(self):
        result = 'none'
        if self.annotators.exists():
            result = ', '.join(
                [user.username for user in self.annotators.all()])
        return result

    get_annotators.short_description = 'Annotators'


class Document(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True)

    corpus = models.ForeignKey(Corpus, related_name='documents', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('corpus', 'title', )

    def __str__(self):
        return '{} - {}'.format(self.corpus.title, self.title)


class LabelKey(models.Model):
    """Used to define what kind of labels should be used per corpus,
    and to group labels from different languages"""
    title = models.CharField(max_length=200, unique=True)

    corpora = models.ManyToManyField(Corpus, related_name='label_keys')
    language_specific = models.BooleanField(
        'Labels are language specific', default=False)
    open_label_set = models.BooleanField(
        'Anyone can add new labels', default=True)

    class Meta:
        verbose_name_plural = 'Label Keys'

    def symbol(self):
        return self.title.lower()

    def __str__(self):
        return self.title


class Label(models.Model):
    """freeform annotation labels"""
    title = models.CharField(max_length=200)
    key = models.ForeignKey(LabelKey, related_name='labels', on_delete=models.CASCADE)
    color = models.CharField(max_length=10, null=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ('key', 'language', 'title')
        ordering = ['key', 'language', 'title']

    def __str__(self):
        return self.title


def corpus_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<corpus>/<language>/<filename>
    return 'documents/{0}/{1}/{2}'.format(instance.document.corpus.pk, instance.language.iso, filename)


class Source(models.Model):
    xml_file = models.FileField(upload_to=corpus_path, blank=True)

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)


class Fragment(models.Model, HasLabelsMixin):
    FS_NONE = 0
    FS_NARRATION = 1
    FS_DIALOGUE = 2
    FORMAL_STRUCTURES = (
        (FS_NONE, 'none'),
        (FS_NARRATION, 'narration'),
        (FS_DIALOGUE, 'dialogue'),
    )

    SF_NONE = 0
    SF_DECLARATIVE = 1
    SF_INTERROGATIVE = 2
    SF_EXCLAMATORY = 3
    SF_IMPERATIVE = 4
    SENTENCE_FUNCTIONS = (
        (SF_NONE, 'none'),
        (SF_DECLARATIVE, 'declarative'),
        (SF_INTERROGATIVE, 'interrogative'),
        (SF_EXCLAMATORY, 'exclamatory'),
        (SF_IMPERATIVE, 'imperative'),
    )

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)

    tense = models.ForeignKey(Tense, null=True, on_delete=models.SET_NULL)
    other_label = models.CharField(max_length=200, blank=True)
    labels = models.ManyToManyField(Label)

    formal_structure = models.PositiveIntegerField(
        'Formal structure', choices=FORMAL_STRUCTURES, default=FS_NONE)
    sentence_function = models.PositiveIntegerField(
        'Sentence function', choices=SENTENCE_FUNCTIONS, default=SF_NONE)

    def to_html(self):
        result = '<ul>'
        for sentence in self.sentence_set.all():
            result += sentence.to_html()
        result += '</ul>'
        return result

    def targets(self):
        """
        Retrieves all target Words for this Fragment.
        :return: A QuerySet of Words.
        """
        return Word.objects.filter(sentence__in=self.sentence_set.all(), is_target=True)

    def target_words(self):
        """
        Retrieves the target words for this Fragment.
        :return: A string that consists of the target words.
        """
        # Check if we have the target words prefetched
        if hasattr(self, 'targets_prefetched'):
            target_words = [w.word for s in self.targets_prefetched for w in s.word_set.all()]
        else:
            target_words = [word.word for word in self.targets()]
        return ' '.join(target_words)

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
        annotations = Annotation.objects. \
            filter(alignment__original_fragment=self,
                   alignment__translated_fragment__language__in=other_languages). \
            select_related('tense', 'alignment__translated_fragment__language') . \
            prefetch_related('words', 'alignment__translated_fragment__sentence_set__word_set')
        # TODO: We currently consider only one Annotation per Alignment, YMMV.
        annotations_by_language = {a.alignment.translated_fragment.language: a for a in annotations}

        for language in other_languages:
            result.append((language, annotations_by_language.get(language)))

        return result

    def full(self, format_=False, annotation=None):
        check_format(format_)

        return '\n'.join([sentence.full(format_, annotation) for sentence in self.sentence_set.all()])

    def get_formal_structure(self):
        result = Fragment.FS_NONE

        if self.document.corpus.check_structure:
            result = Fragment.FS_NARRATION
            for sentence in self.sentence_set.all():
                for word in sentence.word_set.all():
                    if word.is_target and word.is_in_dialogue:
                        result = Fragment.FS_DIALOGUE

        return result

    def get_sentence_function(self):
        """Very simple way to acquire the sentence function."""
        result = Fragment.SF_NONE

        if self.document.corpus.check_structure:
            result = Fragment.SF_DECLARATIVE

            if self.tense and self.tense.title == 'imperative':
                result = Fragment.SF_IMPERATIVE

            for sentence in self.sentence_set.all():
                for word in sentence.word_set.all():
                    if word.word == '?':
                        result = Fragment.SF_INTERROGATIVE
                    if word.word == '!':
                        result = Fragment.SF_EXCLAMATORY

        return result

    def sort_key(self):
        from .utils import sort_key

        sentence = self.first_sentence()
        return sort_key(sentence.xml_id, sentence.XML_TAG)

    def first_sentence(self):
        # The following code is used instead of calling sentence_set.first()
        # because first() triggers a new DB query, while all() makes use
        # of prefetched values when they are available.
        try:
            return self.sentence_set.all()[0]
        except IndexError:
            return None

    def xml_ids(self):
        return ', '.join([s.xml_id for s in self.sentence_set.all()])

    def save(self, *args, **kwargs):
        """Sets the correct formal structure and sentence function on save of a Fragment"""
        self.formal_structure = self.get_formal_structure()
        self.sentence_function = self.get_sentence_function()
        super(Fragment, self).save(*args, **kwargs)

    def __str__(self):
        return self.full()[:100]


class Sentence(models.Model):
    XML_TAG = 's'

    xml_id = models.CharField(max_length=20)

    fragment = models.ForeignKey(Fragment, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['xml_id']),
        ]

    def to_html(self):
        result = '<li>'
        for word in self.word_set.all():
            result += word.to_html() + ' '
        result += '</li>'
        return result

    def full(self, format_=False, annotation=None):
        check_format(format_)

        words = []
        for word in self.word_set.all():
            is_target = word.is_target or (
                annotation and word in annotation.words.all())

            if is_target and format_:
                if format_ in [CSV, XLSX]:
                    words.append('*' + word.word + '*')
                if format_ == HTML:
                    words.append('<strong>' + word.word + '</strong>')
            else:
                words.append(word.word)

            if format_ == HTML and len(words) % 20 == 0:
                words.append('<br>')
        return ' '.join(words)

    def __str__(self):
        return self.full()[:100] + '...'


class Word(models.Model):
    XML_TAG = 'w'

    xml_id = models.CharField(max_length=20)
    word = models.CharField(max_length=200)
    pos = models.CharField(max_length=50)
    lemma = models.CharField(max_length=200, blank=True)

    is_target = models.BooleanField(default=False)

    is_in_dialogue = models.BooleanField(default=False)
    is_in_dialogue_prob = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00)

    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['xml_id']),
            models.Index(fields=['is_target']),
            models.Index(fields=['is_target', 'sentence']),
        ]

    def to_html(self):
        return '<strong>{}</strong>'.format(self.word) if self.is_target else self.word

    def index(self):
        """
        Returns the start index of the Word in the Sentence.
        """
        from .utils import is_before

        result = 0
        for word in self.sentence.word_set.all():
            if is_before(word.xml_id, self.xml_id):
                result += len(word.word) + 1
        return result

    def __str__(self):
        return self.word


class Alignment(models.Model):
    type = models.CharField(max_length=10)

    original_fragment = models.ForeignKey(
        Fragment, null=True, related_name='original', on_delete=models.CASCADE)
    translated_fragment = models.ForeignKey(
        Fragment, null=True, related_name='translated', on_delete=models.CASCADE)


class Annotation(models.Model, HasLabelsMixin):
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
    alignment = models.ForeignKey(Alignment, on_delete=models.CASCADE)

    annotated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name='annotated_by', on_delete=models.SET_NULL)
    annotated_at = models.DateTimeField(auto_now_add=True)

    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name='last_modified_by', on_delete=models.SET_NULL)
    last_modified_at = models.DateTimeField(auto_now=True)

    tense = models.ForeignKey(Tense, blank=True, null=True, on_delete=models.SET_NULL)
    other_label = models.CharField(max_length=200, blank=True)
    labels = models.ManyToManyField(Label)

    class Meta:
        unique_together = ('alignment', 'annotated_by', )
        permissions = (('edit_labels_in_interface', 'Can edit labels in the interface'),)
        indexes = [
            models.Index(fields=['is_no_target', 'is_translation']),
        ]

    def selected_words(self):
        """
        Retrieves the selected Words for this Annotation.
        Order is based on the xml_id, e.g. w18.1.10 should be after w18.1.9.
        :return: A space-separated string with the selected words.
        """
        from .utils import sort_key

        ordered_words = sorted(self.words.all(), key=lambda w: sort_key(w.xml_id, w.XML_TAG))
        return ' '.join([word.word for word in ordered_words])


class SubCorpus(models.Model):
    title = models.CharField(max_length=200)

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('corpus', 'title', )
        verbose_name_plural = 'SubCorpora'

    def get_fragments(self):
        fragments = Fragment.objects.none()

        for document in Document.objects.filter(corpus=self.corpus):
            xml_ids = SubSentence.objects.filter(document=document, subcorpus=self).values_list('xml_id', flat=True)
            fragments |= Fragment.objects.filter(
                language=self.language,
                document=document,
                sentence__xml_id__in=xml_ids)

        return fragments

    def __str__(self):
        return self.title


class SubSentence(models.Model):
    xml_id = models.CharField(max_length=20)

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    subcorpus = models.ForeignKey(SubCorpus, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('document', 'subcorpus', 'xml_id', )
        verbose_name_plural = 'SubSentences'

    def get_sentences(self):
        return Sentence.objects.filter(
            fragment__language=self.subcorpus.language,
            fragment__document=self.document,
            xml_id=self.xml_id)

    def get_fragments(self):
        return Fragment.objects.filter(
            language=self.subcorpus.language,
            document=self.document,
            sentence__xml_id=self.xml_id)

    def __str__(self):
        return self.xml_id
