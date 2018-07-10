Models generated using the `graph_models` command in [Django-extensions](http://django-extensions.readthedocs.io/en/latest/graph_models.html), using the following commands:

    sudo apt-get install graphviz libgraphviz-dev pkg-config
    pip install django-extensions
    
    # add 'django_extensions' to INSTALLED_APPS in settings.py
    
    python manage.py graph_models annotations -o annotations.png
    python manage.py graph_models selections -o selections.png
    python manage.py graph_models stats -o stats.png
