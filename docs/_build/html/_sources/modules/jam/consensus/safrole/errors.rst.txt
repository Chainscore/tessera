Safrole Errors
===================================

.. automodule:: jam.consensus.safrole.errors
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Error Types
===========

The Safrole consensus protocol defines specific error types for handling various failure cases.

SafroleErrorCode
--------------
Enumeration of possible error conditions:

* ``BAD_SLOT`` - Invalid slot number in block header
* ``UNEXPECTED_TICKET`` - Ticket received when not expected
* ``BAD_TICKET_ORDER`` - Tickets not in sorted order by VRF output
* ``BAD_TICKET_PROOF`` - Invalid VRF proof for ticket
* ``BAD_TICKET_ATTEMPT`` - Invalid ticket attempt index
* ``RESERVED`` - Reserved for future use
* ``DUPLICATE_TICKET`` - Duplicate ticket submission

SafroleError
----------
Base error class that wraps error codes with descriptive messages. Used throughout the protocol implementation to signal specific failure conditions.

Example Usage
-----------

.. code-block:: python

    # Verify ticket order
    if not is_ordered(tickets):
        raise SafroleError(
            SafroleErrorCode.BAD_TICKET_ORDER,
            "Tickets must be ordered by VRF output"
        )

    # Check for duplicates
    if is_duplicate(ticket):
        raise SafroleError(
            SafroleErrorCode.DUPLICATE_TICKET,
            f"Ticket {ticket.id} already exists"
        )

Handle Them
----------
.. code-block:: python

    try:
        process_tickets(block)
    except SafroleError as e:
        if e.code == SafroleErrorCode.BAD_TICKET_PROOF:
            # Handle invalid VRF proof
            pass
        elif e.code == SafroleErrorCode.BAD_TICKET_ORDER:
            # Handle ordering violation
            pass

API Reference
-----------

.. automodule:: jam.consensus.safrole.errors
   :members:
   :undoc-members:
   :show-inheritance:
