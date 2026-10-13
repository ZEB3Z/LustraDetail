"""Service layer: ALL business rules live here.

Rules of the layer:
- never print and never call input(); raise typed exceptions instead
- never import anything from app.ui
- receive repositories/services via the constructor (dependency injection),
  which is what will make the future Tkinter UI a drop-in replacement.
"""
