from django.conf import settings
from django.db import models

from core.utils import check_format, CSV, HTML, XLSX
from lxml import etree


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

    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    category = models.ForeignKey(TenseCategory, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('language', 'title', )

    def __unicode__(self):
        return u'{} ({})'.format(self.title, self.language.iso)


class Corpus(models.Model):
    title = models.CharField(max_length=200, unique=True)
    languages = models.ManyToManyField(Language)
    annotators = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    tense_based = models.BooleanField(
        'Whether this Corpus is annotated for tense/aspect, or something else',
        default=True)

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
            result = ', '.join(
                [user.username for user in self.annotators.all()])
        return result

    get_annotators.short_description = 'Annotators'


class Document(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True)

    upload = models.FileField(upload_to='uploads/', blank=True)

    corpus = models.ForeignKey(
        Corpus, related_name='documents', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('corpus', 'title', )

    def get_sentences(self, language):
        doc_fragments = [f.id for f in list(self.fragment_set.all())]
        if self.upload and hasattr(self.upload, 'path'):
            document_sentences = []
            tree = etree.parse(self.upload.path)
            for el in tree.iter():
                if ('id' in el.attrib.keys() and el.tag in ['p', 's']):
                    if el.tag == 's':
                        ss = Sentence.objects.filter(
                            xml_id=el.get('id'),
                            fragment__document__id=self.id,
                            fragment__language=language
                        )
                        sentence_content = Sentence.objects.filter(
                            xml_id=el.get('id')).first()
                    else:
                        sentence_content = None
                    document_sentences.append(
                        {'tag': el.tag,
                         'id': el.get('id'),
                         'content': sentence_content})
            return document_sentences

    def __unicode__(self):
        return self.title


class Fragment(models.Model):
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

    def target_words(self):
        """
        Retrieves the target words for this Fragment.
        :return: A list of Strings with the target Words.
        """
        result = []
        for sentence in self.sentence_set.all():
            result.extend(
                [word.word for word in sentence.word_set.filter(is_target=True)])
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
        other_languages = self.document.corpus.languages.exclude(
            pk=self.language.pk)
        for language in other_languages:
            # Note that there should be only one Alignment per language, so we can use .first() here.
            alignment = self.original.filter(
                translated_fragment__language=language).first()
            if alignment:
                # TODO: We currently consider only one Annotation per Alignment, YMMV.
                annotation = alignment.annotation_set.first()
                if annotation:
                    result.append((language, annotation))
                else:
                    # This happens if there's no Annotation yet
                    result.append((language, None))
            else:
                # This happens if there's no Alignment for this Fragment in the given language
                result.append((language, None))
        return result

    def full(self, format_=False, annotation=None):
        check_format(format_)

        return '\n'.join([sentence.full(format_, annotation) for sentence in self.sentence_set.all()])

    def label(self):
        return self.tense.title if self.tense else self.other_label

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

            if self.tense and self.tense.title == u'imperative':
                result = Fragment.SF_IMPERATIVE

            for sentence in self.sentence_set.all():
                for word in sentence.word_set.all():
                    if word.word == u'?':
                        result = Fragment.SF_INTERROGATIVE
                    if word.word == u'!':
                        result = Fragment.SF_EXCLAMATORY

        return result

    def first_sentence(self):
        return self.sentence_set.all().order_by('xml_id')[0]

    def xml_ids(self):
        return ', '.join([s.xml_id for s in self.sentence_set.all()])

    def save(self, *args, **kwargs):
        """Sets the correct formal structure and sentence function on save of a Fragment"""
        self.formal_structure = self.get_formal_structure()
        self.sentence_function = self.get_sentence_function()
        super(Fragment, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.full()[:100]


class Sentence(models.Model):
    xml_id = models.CharField(max_length=20)

    fragment = models.ForeignKey(Fragment, on_delete=models.CASCADE)

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

    def __unicode__(self):
        return self.full()[:100] + '...'


class Word(models.Model):
    xml_id = models.CharField(max_length=20)
    word = models.CharField(max_length=200)
    pos = models.CharField(max_length=50)
    lemma = models.CharField(max_length=200, blank=True)

    is_target = models.BooleanField(default=False)

    is_in_dialogue = models.BooleanField(default=False)
    is_in_dialogue_prob = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00)

    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)

    def to_html(self):
        return u'<strong>{}</strong>'.format(self.word) if self.is_target else self.word

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

    def __unicode__(self):
        return self.word


class Alignment(models.Model):
    type = models.CharField(max_length=10)

    original_fragment = models.ForeignKey(
        Fragment, null=True, related_name='original', on_delete=models.CASCADE)
    translated_fragment = models.ForeignKey(
        Fragment, null=True, related_name='translated', on_delete=models.CASCADE)


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
    alignment = models.ForeignKey(Alignment, on_delete=models.CASCADE)

    annotated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name='annotated_by', on_delete=models.SET_NULL)
    annotated_at = models.DateTimeField(auto_now_add=True)

    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, related_name='last_modified_by', on_delete=models.SET_NULL)
    last_modified_at = models.DateTimeField(auto_now=True)

    tense = models.ForeignKey(Tense, null=True, on_delete=models.SET_NULL)
    other_label = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('alignment', 'annotated_by', )

    def selected_words(self):
        """
        Retrieves the selected Words for this Annotation.
        Order is based on the xml_id, e.g. w18.1.10 should be after w18.1.9.
        :return: A space-separated string with the selected words.
        """
        ordered_words = sorted(self.words.all(), key=lambda w: map(
            int, w.xml_id[1:].split('.')))
        return ' '.join([word.word for word in ordered_words])

    def label(self):
        return self.tense.title if self.tense else self.other_label
