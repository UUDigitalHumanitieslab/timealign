import codecs
import contextlib
import csv
import cStringIO

from xlsxwriter import Workbook


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    Copied from https://docs.python.org/2/library/csv.html#examples
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode('utf-8') for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class ExcelWriter:
    """
    Writes xlsx files while mimicking the CSV writer interface.
    """
    def __init__(self, filename):
        self._workbook = Workbook(filename)
        self._worksheet = self._workbook.add_worksheet()  # this assumes an empty file
        self._row = 0

    def writerow(self, contents):
        self._worksheet.write_row(self._row, 0, contents)
        self._row += 1

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def close(self):
        self._workbook.close()


@contextlib.contextmanager
def open_csv(filename):
    with open(filename, 'wb') as fileobj:
        fileobj.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
        yield UnicodeWriter(fileobj, delimiter=';')


@contextlib.contextmanager
def open_xlsx(filename):
    writer = ExcelWriter(filename)
    yield writer
    writer.close()


def pad_list(l, pad_length):
    """
    Pads a list with empty items
    Copied from http://stackoverflow.com/a/3438818/3710392
    :param l: the original list
    :param pad_length: the length of the list
    :return: the resulting, padded list
    """
    return l + [''] * (pad_length - len(l))
