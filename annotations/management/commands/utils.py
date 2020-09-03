import contextlib
import csv

from xlsxwriter import Workbook


class ExcelWriter:
    """
    Writes xlsx files while mimicking the CSV writer interface.
    """
    def __init__(self, filename):
        self._workbook = Workbook(filename)
        self._worksheet = self._workbook.add_worksheet()  # this assumes an empty file
        self._row = 0

    def writerow(self, contents, is_header=False):
        cell_format = None

        # Add bold formatting and an autofilter
        if is_header:
            cell_format = self._workbook.add_format({'bold': True})
            self._worksheet.autofilter(self._row, 0, 0, len(contents) - 1)

        self._worksheet.write_row(self._row, 0, contents, cell_format)
        self._row += 1

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def close(self):
        self._workbook.close()


@contextlib.contextmanager
def open_csv(filename):
    with open(filename, 'w') as fileobj:
        fileobj.write('\uFEFF')  # the UTF-8 BOM to hint Excel we are using that...
        yield csv.writer(fileobj, delimiter=';')


@contextlib.contextmanager
def open_xlsx(filename):
    writer = ExcelWriter(filename)
    yield writer
    writer.close()


def pad_list(orig_list, pad_length):
    """
    Pads a list with empty items
    Copied from http://stackoverflow.com/a/3438818/3710392
    :param orig_list: the original list
    :param pad_length: the length of the list
    :return: the resulting, padded list
    """
    return orig_list + [''] * (pad_length - len(orig_list))
