
Release process
---------------

.. code-block:: bash

   export VERSION=a.b.c

   poetry version $VERSION
   dephell convert
   black setup.py

   git add .
   git commit -m "Releasing version $VERSION"

   git tag "v$VERSION"
   git branch "v$VERSION"
   git push origin \
       refs/tags/"v$VERSION" \
       refs/heads/"v$VERSION" \
       main

   # Wait for CI to pass

   poetry publish --build
