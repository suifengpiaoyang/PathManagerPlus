import sys
import os

path = os.path.dirname(os.path.abspath('.'))
sys.path.insert(0, path)

from PathManagerPlus.handle_data import DataStorage


d = DataStorage()
node_a = d.add_node('A')
node_b = d.add_node('B', node_a)
d.add_item('b1', node_b)
d.add_item('b2', node_b)
d.pretty_print()
