ClassifyHub - User guide
   by Marcus Soll and Malte Vosgerau

-------------------------------------------------------------------------------

Contents:
   0.   Introduction
   1.1. Dependencies
   1.2. Dependencies GUI
   2.   GitHub API setup
   3.   Learning
   4.   Batch processing
   5.   Performance validation
   6.   Graphical User Interface
   7.   Unit tests
   8.   Documentation

-------------------------------------------------------------------------------

0. Introduction

ClassifyHub is an algorithm to tackle the 'GitHub Classification Problem'.
The goal is to classify GitHub (https://github.com/) repositories into the
following categories:
 * DEV: software development projects
 * HW: Solutions for homeworks, exercises and similar
 * EDU: Repositories for didactic content
 * DOCS: Non-didactic documents
 * WEB: (Personal) web pages
 * DATA: Datasets
 * OTHER: Anything not contained in the above categories

-------------------------------------------------------------------------------

1.1. Dependencies

ClassifyHub requires Python 3. The following additional packages need to be
installed:
   requests (https://pypi.python.org/pypi/requests)
   lockfile (https://pypi.python.org/pypi/lockfile)
   scikit-learn (http://scikit-learn.org/stable/index.html)

On most systems these can be installed using pip. Depending on your 
distribution you might have to install pip (Python 3 version) manually. First
ensure you have an up-to-date pip version installed:
   sudo pip3 install --upgrade pip

After this you can install the required packages by using the following 
commands:

   pip3 install --user --upgrade requests
   pip3 install --user lockfile
   pip3 install --user numpy scipy scikit-learn

If you are a Windows 10 user you need to get Python 3 first. Please use this
site to get the latest version: 

   https://www.python.org/downloads/

Please mark the box "Add Python 3.5 to PATH".

After the install is complete open a commandline and use following commands:

   pip3 install --user requests
   pip3 install --user lockfile
   pip3 install --user numpy
   pip3 install --user scikit-learn

scpipy has to be installed manually. Please download the proper version for
you system from

   http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy

e.g. scipy-0.18.1-cp35-cp35m-win_amd64.whl is suitable for Python 3.5.x on a 
64bit windows. After your download is complete please use following command
in the file directory:

   pip install "scipy-0.18.1-cp35-cp35m-win_amd64.whl"

This should install the last needed dependencie.

Tested distributions:
   OpenSUSE 42.2
   Ubuntu 16.04
   Windows 10

NOTE TO WINDOWS USERS: Please ensure that both Python 3 is running correctly
(and in PATH) and all dependencies are installed correctly - especially numpy.
See https://www.scipy.org/install.html for more information on how to install
numpy / scipy.

-------------------------------------------------------------------------------

1.2. Dependencies GUI

To run the graphical user interface (GUI) some additional dependencies are
required:
   PyQt5 (https://riverbankcomputing.com/software/pyqt/intro)

PyQt5 offers packages only for very recent versions of the python interpreter,
we therefore recommend installing it through your packet manager, e.g.:
   OpenSUSE 42.2: sudo zypper install python3-qt5
   Ubuntu 16.04: sudo apt-get install python3-pyqt5 python3-pyqt5.qtquick qml-module-qtquick-controls

PLEASE NOTE: Depending on your distribution, the QML part of PyQt5 might be
seperated from the main PyQt5 package.

UBUNTU: Due to a bug in Ubuntu (see 
https://bugs.launchpad.net/appmenu-qt5/+bug/1323853) the menu bar of the GUI
is not visible. Unfortunately this is nothing we can fix. Hopefully this will
be fixed by Ubuntu.

If you have a recent python version installed on Windows, you can use:
   pip3 install --user pyqt5

Tested distributions:
   OpenSUSE 42.2
   Ubuntu 16.04
   Windows 10

-------------------------------------------------------------------------------

2. GitHub API setup

The amount of unauthenticated requests to the GitHub API is very limited 
(https://developer.github.com/v3/#rate-limiting). Therefore it is adviced to
use authentificated requests, especially for operations which need a huge
amount of requests (like learning and validation). For this an
"access token" is needed.

The username for the authentification is stored as plain text in a USER file
(default location: "./user"). The access token for the authentification is 
stored as plain text in a SECRET file (default location: "./secret"). The
file names are case sensitive and do not have an extension (unless you change
the paths through command line arguments).

Requestst are automatically authentificated once this two files are found.

-------------------------------------------------------------------------------

3. Learning

The learning process fits the different classifiers to the provided data.
The learning data is considered to be placed in a folder 
(defaut: "./data/learning/"), where each class has an own file containing the 
repositories of the class in the input format.

The learning process has to be run at least once before the batch processing
can be performed. It is also necessary to run it whenever the scikit-learn
version has changed.

The learning process can be started by running run_learning.py, e.g.:

   python3 run_learning.py

The parameter of the learning process can be controlled through command line 
arguments. For more information run

   python3 run_learning.py --help

-------------------------------------------------------------------------------

4. Batch processing

NOTE: The learning process has to be run at least once before batch processing
can be run! See section 3 for more information.

The batch processing script processes a text file (default location: 
"./data/input.txt") containing repositories in the specified input format and
stores the results in an output file (default location: "./data/output.txt")
in the specified output format. The script is started by running 
run_batch.py, e.g.:

   python3 run_batch.py

Please use the command line option "--help" to display detailed information on
available command line options, e.g.

   python3 run_batch.py --help

-------------------------------------------------------------------------------

5. Performance validation

To evaluate the performance of our algorithm (in terms of precision/recall) a
validation script is provided. This script runs a k-fold cross-validation 
(default: k=10) on the learning data (see section 2). The result is printed as
well as written to the output file (default location: "./data/output.txt"). 
The script is started by running run_batch.py, e.g.:

   python3 run_validate.py

The parameter of the validation process can be controlled through command line 
arguments. For more information run

   python3 run_validate.py --help

-------------------------------------------------------------------------------

6. Graphical User Interface

The application comes with a graphical user interface. It is recommended to
run the learning process (see section 3) before starting the user interface.
To start the user interface simply run:

   python3 run_gui.py

The parameter of the computation can be controlled through command line
arguments as well as through the user interface itself. The command line
arguments overwrite previous preferences. For more information run

   python3 run_gui.py --help

or look at 'Edit -> Preferences' in the user interface.

-------------------------------------------------------------------------------

7. Unit tests

The application's unit tests can be performed by running run_test.py, e.g.

   python3 run_tests.py

-------------------------------------------------------------------------------

8. Documentation


The source code documentation can be build by using Doxygen
(doxygen.org). By default doxygen creates output as html and latex files.

To generate the documentation switch the working directory to the ClassifyHub
directory and use the following command:
   doxygen
