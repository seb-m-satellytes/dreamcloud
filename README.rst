DreamBoard — A Simple Reference Image Viewer
========================================

.. raw:: html

   <img align="left" width="100" height="100" src="./dreamboard/assets/logo.png">

`DreamBoard <https://dreamboard.org>`_ lets you quickly arrange your reference images and view them while you create. Its minimal interface is designed not to get in the way of your creative process.

|python-version| |github-ci-flake8|

.. image:: ./images/screenshot.png

.. |python-version| image:: https://img.shields.io/badge/python%20-3.9%20%7C%203.10-blue
   :target: https://www.python.org/

.. |github-ci-flake8| image:: https://img.shields.io/badge/flake8-checked-blueviolet
   :target: https://github.com/mini-ninja-64/dreamboard/actions/workflows/flake8.yml

Installation
------------

Stable Release
~~~~~~~~~~~~~~

Get the file for your operating system (Windows, Linux, macOS) from the `latest release <https://github.com/rbreu/dreamboard/releases>`_.

**Linux users** need to give the file executable rights before running it. Optional: If you want to have DreamBoard appear in the app menu, save the desktop file from the `release section <https://github.com/rbreu/dreamboard/releases>`_ in ``~/.local/share/applications``, save the `logo <https://raw.githubusercontent.com/rbreu/dreamboard/main/dreamboard/assets/logo.png>`_, and adjust the path names in the desktop file to match the location of your DreamBoard installation.

**MacOS X users**, look at `detailed instructions <https://dreamboard.org/macosx-run.html>`_ if you have problems running DreamBoard.

Follow further releases via the `atom feed <https://github.com/rbreu/dreamboard/releases.atom>`_.


Development Version
~~~~~~~~~~~~~~~~~~~

To get the current development version, you need to have a working Python 3 environment. Run the following command to install the development version::

  pip install git+https://github.com/rbreu/dreamboard.git

Then run ``dreamboard`` or ``dreamboard filename.dreamb``.

If there are issues starting the application, run it with the environment variable ``QT_DEBUG_PLUGINS`` set to 1, for example from a Linux shell::

  QT_DEBUG_PLUGINS=1 dreamboard

This should tell you whether you need to install any additional libraries.


Features
--------

* Move, scale, rotate and flip images
* Mass-scale images to the same width, height or size
* Mass-arrange images vertically, horizontally or for optimal usage of space
* Add text notes
* Enable always-on-top-mode and disable the title bar to let the DreamBoard window unobtrusively float above your art program:

.. image:: https://github.com/rbreu/dreamboard/blob/main/images/screenshot.png


Regarding the dreamb file format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, all images are embedded into the dreamb file as png files. While png is a lossless format, it may also produce larger file sizes than compressed jpg files, so dreamb files may become bigger than the imported images on their own. More embedding options are to come later.

The dreamb file format is a sqlite database inside which the images are stored in an sqlar table—meaning they can be extracted with the `sqlite command line program <https://www.sqlite.org/cli.html>`_::

  sqlite3 myfile.dreamb -Axv

Options for exporting from inside DreamBoard are planned, but the above always works independently of DreamBoard.


Notes for developers
--------------------

DreamBoard is written in Python and PyQt6. For more info, see `CONTRIBUTING.rst <https://github.com/rbreu/dreamboard/blob/main/CONTRIBUTING.rst>`_.
