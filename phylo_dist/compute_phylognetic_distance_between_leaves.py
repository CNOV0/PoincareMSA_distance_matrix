#! /usr/bin/env python
import dendropy
from dendropy import treecalc
mytree="glob.phylip_phyml_tree.txt"
tree = dendropy.Tree.get_from_path(mytree, schema="newick")
maxdist=0
mindist=666
pdm = dendropy.PhylogeneticDistanceMatrix.from_tree(tree)
pdm.write_csv('output_phyl.csv')
# To compute distance only on specific id 
#mylist=[43,164,52,46,241,108,122,160,94,234,192,180]
mylist=[]
for i, t1 in enumerate(tree.taxon_namespace):
    for t2 in tree.taxon_namespace[i+1:]:
        #print(f'{t1.label} {t2.label} {pdm(t1, t2)}')
        #print(f'{t2.label}:{mylist.count(t2.label)} {t1.label}:{mylist.count(t1.label)}')
        if int(t2.label) in mylist and int(t1.label) in mylist: 
            print("%s %s %s" % (t1.label, t2.label, pdm(t1, t2)))
#        if maxdist < pdm(t1, t2): 
#            maxdist=pdm(t1, t2)
#            print(f'Max: {t1.label} {t2.label} {pdm(t1, t2)}') 
#        if mindist > pdm(t1, t2):
#            mindist=pdm(t1, t2)
#            print(f'Min: {t1.label} {t2.label} {pdm(t1, t2)}') 
#print(f'MaxDist:{maxdist}')
