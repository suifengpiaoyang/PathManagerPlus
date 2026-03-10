import sys
import os

path = os.path.dirname(os.path.abspath('.'))
sys.path.insert(0, path)

from PathManagerPlus.handle_data import DataStorage

d = DataStorage()
node_a = d.add_node('A')
d.add_item('A', node_a)
d.add_item('D', node_a)
d.add_item('B', node_a)
d.add_item('C', node_a)
for item_id in d['nodes'][node_a]['items']:
    print(d['items'][item_id]['name'], end='')
print()
# 升序
d.sort_items_within_node(node_a)
for item_id in d['nodes'][node_a]['items']:
    print(d['items'][item_id]['name'], end='')
print()
# 降序
d.sort_items_within_node(node_a, reverse=True)
for item_id in d['nodes'][node_a]['items']:
    print(d['items'][item_id]['name'], end='')
print()
