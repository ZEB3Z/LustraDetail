"""UI layer: the ONLY part of the app that prints or reads input.

Every screen receives the service `stack` and calls services for all
logic - which is why replacing this package later (Tkinter) requires
zero changes to models, storage, or services.
"""
