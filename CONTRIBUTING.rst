DreamBoard — Notes For Developers
=============================

DreamBoard is written in Python and PyQt6.


Developing
----------

Clone the repository and install dreamboard and its dependencies::

  git clone https://github.com/rbreu/dreamboard.git
  cd dreamboard
  pip install -e .

Install additional development requirements::

  pip install -r requirements/dev.txt

Run unittests with::

  pytest .

Run codechecks with::

  flake8 .

Run unittests with coverage report::

  coverage run --source=dreamboard -m pytest
  coverage html

If your browser doesn't open automatically, view ``htmlcov/index.html``.

DreamBoardref files are sqlite databases, so they can be inspected with any sqlite browser.

For debugging options, run::

  dreamboard --help


Building the app
----------------

To build the app, run::

  pyinstaller --onefile DreamBoard.spec

You will find the generated executable in the folder ``dist``.


Website etc.
------------

The Python version badge in the README is generated with pybadges::

  python -m pybadges --left-text=Python --right-text="3.9 | 3.10" > images/python_version_badge.svg

The `website <https://rbreu.github.io/dreamboard/>`_ is hosted via Github pages from the gh-pages branch. You can run it locally if you have Ruby and bundler installed::

  bundle install
  bundle exec jekyll serve --baseurl ""
