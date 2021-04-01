import xml.etree.ElementTree as ET
from pprint import pprint
from collections import deque

tree = ET.parse('./xmls/armstrng.wsx')
root = tree.getroot()
d = {}
count = 0
for child in root.iter('Explicitly-Qualified-Segment'):
    v = []
    t = []
    # if count > 10:
    #     break
    for grandchild in child.iter('Variable'):
        # print(f"変数名：{grandchild.attrib['spelling']}")
        v.append(grandchild.attrib['spelling'])

    for grandchild in child.iter('Standard-Type'):
        t.append(grandchild.attrib['spelling'])
    
    # for grandchild in child.iter('Adjective'):
    #     t.append(grandchild.attrib['spelling'])

    for grandchild in child.iter('Struct-Type'):
        t.append(grandchild.attrib['spelling'])
    
    for i in range(len(v)):
        # print(child.tag, child.attrib)
        print(v, t)
        if not v[i] in d:
            d[v[i]] = deque([t[0]])
        else:
            # print('testooooooooooooo')
            d[v[i]].append(t[0])
    count += 1

pprint(d)


# for child in root.iter():
#     if 'spelling' in child.attrib:
#         print(child.attrib['spelling'])
