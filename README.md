# TimeAlign

TimeAlign allows you to easily annotate similar forms in aligned phrases.

## Installation

TimeAlign is created with the [Django web framework](https://www.djangoproject.com/) and runs in both Python 2.7 and 3.5.
You can install the required packages by calling `pip install -r requirements.txt.`

Starting from an empty Ubuntu 16.04 installation, you will need the following to get you started:

    # Clone the repository
    git clone [repository URL]
    cd timealign/

    # Create a virtual environment
    sudo apt-get install python-dev virtualenv
    virtualenv .env
    source .env/bin/activate
    pip install -r requirements.txt

    # If you want to use MySQL as your database backend (recommended)
    sudo apt-get install mysql-server libmysqlclient-dev
    # Create a database and change the databases section in timealign/settings.py accordingly
    # Migrate the database using:
    python manage.py migrate
    
    # Run the tests
    python manage.py test

If the test runs OK, you should be ready to roll! Run the webserver using:

    python manage.py runserver

## Documentation

You can find ERD diagrams of the applications in [`doc/models`](doc/models/README.md).

General information on the Time in Translation-project can be found on [our website](https://time-in-translation.hum.uu.nl/). 

## Citing

If you happen to have used (parts of) this project for your research, please refer to this paper:

[van der Klis, M., Le Bruyn, B., de Swart, H. (2017)](http://www.aclweb.org/anthology/E17-2080). Mapping the Perfect via Translation Mining. *Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers* 2017, 497-502.
