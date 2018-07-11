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

Note that MySQL 8.x does not include necessary development headers. Use MySQL 5.
If the test runs OK, you should be ready to roll!

## Citing

If you happen to have used (parts of) this project for your research, please refer to this paper:

[van der Klis, M., Le Bruyn, B., de Swart, H. (2017)](http://www.aclweb.org/anthology/E17-2080). Mapping the Perfect via Translation Mining. *Proceedings of the 15th Conference of the European Chapter of the Association for Computational Linguistics: Volume 2, Short Papers* 2017, 497-502.
