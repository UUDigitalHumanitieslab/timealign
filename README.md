# TimeAlign

TimeAlign allows you to easily annotate similar forms in aligned phrases.

## Installation

TimeAlign is created with the [Django web framework](https://www.djangoproject.com/) and runs in both Python 2.7 and 3.5.
You can install the required packages by calling `pip install -r requirements.txt.`

## Adding fragments

### Management command

You can add aligned fragments using the management command `add_sentences`.
This command reads a .csv-file with a specific format that is exported from the [time-in-translation project](https://github.com/UUDigitalHumanitieslab/time-in-translation).
