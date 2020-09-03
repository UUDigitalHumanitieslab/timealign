import csv

CSV = 'csv'
HTML = 'html'
XLSX = 'xlsx'
FORMATS = [CSV, HTML, XLSX]


def check_format(format_):
    if format_ and format_ not in FORMATS:
        raise ValueError('Incorrect formatting {} provided'.format(format_))


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [str(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def find_in_enum(key, enum):
    # the type of enum expected here is actually an iterable of key-value tuples
    return dict(enum).get(key, 'unknown')


COLOR_LIST = [
    '#1f77b4',
    '#ff7f0e',
    '#2ca02c',
    '#d62728',
    '#9467bd',
    '#8c564b',
    '#e377c2',
    '#7f7f7f',
    '#bcbd22',
    '#17becf',
    '#aec7e8',
    '#ffbb78',
    '#98df8a',
    '#ff9896',
    '#c5b0d5',
    '#c49c94',
    '#f7b6d2',
    '#f7b6d2',
    '#dbdb8d',
    '#9edae5',
]