from lxml import etree

tree = etree.parse('/Users/3248526/corpora/camus(fr)/1t.xml')
# print(etree.tostring(tree.getroot(), pretty_print=True))


i = etree.ElementDepthFirstIterator(tree.getroot())

for entry in i:
    try:
        print entry.attrib['id']
    except:
        print "fail"
