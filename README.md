# TimeAlign

TimeAlign allows you to easily annotate similar forms in aligned phrases.

## Installation

TimeAlign is created with the [Django web framework](https://www.djangoproject.com/) and requires Python 3.
After installing the dependencies for the MySQL database driver (see below), you can install the required python packages by running `pip install -r requirements.txt`

### MySQL Dependencies
If you want to use MySQL as your database backend (recommended) use the following commands to install a database server and the required packages for the python client.

#### CentOS 7.7
    sudo yum install mariadb-server mariadb-devel python3-devel
    sudo yum groupinstall 'Development Tools'

#### Ubuntu 18.04
    sudo apt-get install python3-dev default-libmysqlclient-dev libssl-dev mysql-server

### Setting up TimeAlign in a virtual environment
    # Clone the repository
    git clone [repository URL]
    cd timealign/

    # Create a virtual environment
    sudo apt-get install virtualenv
    virtualenv .env
    source .env/bin/activate
    pip install --upgrade pip wheel
    pip install -r requirements.txt

    # Create a database and change the databases section in timealign/settings.py accordingly
    # Migrate the database using:
    python manage.py migrate

    # Initialize revisions
    python manage.py createinitialrevisions

    # Run the tests
    python manage.py test

If the test runs OK, you should be ready to roll! Run the webserver using:

    # Start the (local) web server
    python manage.py runserver

## Documentation

You can find ERD diagrams of the applications in [`doc/models`](doc/models/README.md).

General information on the Time in Translation-project can be found on [our website](https://time-in-translation.hum.uu.nl/).

## Citing

If you happen to have used (parts of) this project for your research, please refer to this paper:

[van der Klis, M., Le Bruyn, B., de Swart, H. (2017)](http://www.aclweb.org/anthology/E17-2080). Mapping the Perfect via Translation Mining. *Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers* 2017, 497-502.
