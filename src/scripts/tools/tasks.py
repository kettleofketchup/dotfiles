from . import general_ns, languages_ns, terminal_ns
from invoke import Collection

ns = Collection("tools")
ns.add_collection(general_ns)
ns.add_collection(languages_ns)
ns.add_collection(terminal_ns)