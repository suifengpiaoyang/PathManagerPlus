import sys
import os

path = os.path.dirname(os.path.abspath('.'))
sys.path.insert(0, path)

from PathManagerPlus.handle_data import DataStorage

d = DataStorage()
node_a = d.add_node('A')
d.add_item('A', node_a)
d.add_item('d', node_a)
d.add_item('b', node_a)
# AI 的意思说 str.casefol 这种排序方式更加接近德语的逻辑。它说德语
# 的字典是这么排序的。但是目前我并不熟悉这一部分，就以 str.upper 作为
# 目前的排序方式。
d.add_item('Bß', node_a)     # 德语中的小写字母 "ß"(eszett)
d.add_item('cß', node_a)
d.add_item('C', node_a)
for item_id in d['nodes'][node_a]['items']:
    print(d['items'][item_id]['name'], end=',')
print()
# 升序
d.sort_items_within_node(node_a)
for item_id in d['nodes'][node_a]['items']:
    print(d['items'][item_id]['name'], end=',')
print()
# 降序
d.sort_items_within_node(node_a, reverse=True)
for item_id in d['nodes'][node_a]['items']:
    print(d['items'][item_id]['name'], end=',')
print()
