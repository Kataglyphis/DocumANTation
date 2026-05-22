Usage
=====

Build the Docker image:

.. code-block:: bash

   nerdctl build . -t pandoc_all

Build the Sphinx documentation:

.. code-block:: bash

   uv run --with "sphinx>=8,<9" sphinx-build -W -b html docs docs/_build/html

Build the presentation:

.. code-block:: bash

   ./scripts/build_in_container.sh beamer

Build the book:

.. code-block:: bash

   ./scripts/build_in_container.sh book

Build the CV:

.. code-block:: bash

   ./scripts/build_in_container.sh cv

Enable strict warning checks:

.. code-block:: bash

   STRICT_WARNINGS=1 ./scripts/build_in_container.sh book
   STRICT_WARNINGS=1 ./scripts/build_in_container.sh cv
