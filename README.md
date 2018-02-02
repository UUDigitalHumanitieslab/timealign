# TimeAlign

TimeAlign allows you to easily annotate similar forms in aligned phrases.

## Installation

TimeAlign is created with the [Django web framework](https://www.djangoproject.com/) and runs in both Python 2.7 and 3.5.
You can install the required packages by calling `pip install -r requirements.txt.`

Starting from an empty Ubuntu 16.04 installation, you will need the following to get you started:

    git clone [repository URL]
    cd timealign/

    sudo apt-get install mysql-server libmysqlclient-dev

    sudo apt-get install python-dev virtualenv
    virtualenv .env
    source .env/bin/activate
    pip install -r requirements.txt

    python manage.py test

If the test runs OK, you should be ready to roll!
