jam.types.base.null module
==========================

.. automodule:: jam.types.base.null
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

jam.types.base.null
================

Null type implementation for the JAM protocol.

Type Definitions
-------------

Null
^^^^
* Zero-sized type
* Represents absence of value
* No storage overhead
* Used in optional types

Encoding Format
-------------

Null::

   None -> []  # Zero bytes

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Null: No storage
* No padding or alignment
* Zero-copy for None


Examples
-------

Null Type
^^^^^^^
.. code-block:: python

    from jam.types.base.null import Null

    # Create and encode
    value = Null()
    encoded = value.encode()  # -> []

    # Decode
    decoded = Null.decode(encoded)
    assert decoded is None


API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.null.Null
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.null.Nullable
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.null.decodable_nullable
