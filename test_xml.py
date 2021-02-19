import xml.etree.ElementTree as ET
import copy

tree = ET.parse('test_output_temp.xml')
root = tree.getroot()

d = {}
declear_history = []

for qs in root.iter('qualifiedVariables'):
    tmp_v = []
    tmp_mode = ''

    for v in qs.iter('variableIdentifier'):
        # print(f'variables:{v.attrib}')
        tmp_v.append(v.attrib['spelling'])
    
    for mode in qs.iter('modeSymbol'):
        # print(f'mode:{mode.attrib}')
        if 'spelling' in mode.attrib:
            tmp_mode = mode.attrib['spelling']
        else:
            tmp_mode = 'set'
    
    for v in tmp_v:
        d[v] = tmp_mode

    d_copy = copy.copy(d)
    declear_history.append(d_copy)
print(declear_history)
