from .imports import ImportsView
from .delete import DeleteView
from .nodes import NodesView
from .updates import UpdatesView
from .history import HistoryView

HANDLERS = [ImportsView, DeleteView, NodesView, UpdatesView, HistoryView]
