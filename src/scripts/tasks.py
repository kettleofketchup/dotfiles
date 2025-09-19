from invoke import Collection

from .tools import general_ns, languages_ns, terminal_ns
from .sets.tasks import ns as sets_ns
ns = Collection()
ns.add_collection(general_ns)
ns.add_collection(languages_ns)
ns.add_collection(terminal_ns)
ns.add_collection(sets_ns)

