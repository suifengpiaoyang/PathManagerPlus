import sys
import os

path = os.path.dirname(os.path.abspath('.'))
sys.path.insert(0, path)

from PathManagerPlus.handle_data import DataStorage


d = DataStorage()
node_a = d.add_node('A')
node_b = d.add_node('B', node_a)
node_c = d.add_node('C', node_b)
node_d = d.add_node('D', node_b)
d.add_item('b1', node_b)
d.add_item('b2', node_b)
item1 = d.add_item('c1', node_c)
item2 = d.add_item('c2', node_c)
item3 = d.add_item('c3', node_c)
d.pretty_print()
d.move_item_to_node(item2, node_a)
d.pretty_print()
