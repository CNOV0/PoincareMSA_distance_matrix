# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

from sklearn.neighbors import kneighbors_graph
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise
from sklearn.neighbors import NearestNeighbors
from sklearn.manifold import MDS
from scipy.sparse import csgraph
import matplotlib.pyplot as plt


import pandas as pd
import numpy as np
import torch
import os

import timeit
import re
from argparse import ArgumentParser

def create_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--path", type=str,
        required=True,
        help="Path of aatmx file"
    )
    parser.add_argument(
        "--maxlen",
        type=int,
        default=872,
        help="Max length",
    )
    return parser

# Construct a padded numpy matrices for a given PSSM matrix
def construct_tensor(fpath):
    ansarr = np.loadtxt(fpath).reshape(-1)
    # ansarr = np.zeros((maxlen, 20))
    # ansarr[:arr.shape[0], :] = arr
    return np.array(ansarr)


def prepare_data(fpath, withroot = True, fmt='.aamtx'):
    # print([x[0] for x in os.walk(fpath)])
    # subfolders = [f.path for f in os.listdir(fpath) if f.is_dir() ]   
    # fmt = '.aamtx'
    proteins = [s for s in os.listdir(fpath) if fmt in s]
    n_proteins = len(proteins)
    print(f"{n_proteins-1} proteins found in folder {fpath}.")

    if not withroot:
        proteins.remove("0.aamtx")
        n_proteins = len(proteins)
        print("No root detected")

    protein_file = proteins[0]
    #print(protein_file)
    fin = f'{fpath}/{protein_file}'    

    a = construct_tensor(fin)

    features = np.zeros([n_proteins, len(a)])
    labels = []
    print("Prepare data: tensor construction")
    for i, protein_name in enumerate(proteins):
        #print(i, protein_name)
        fin = f'{fpath}/{protein_name}'
        features[i, :] = construct_tensor(fin)
        labels.append(protein_name.split('.')[0])
    print("Prepare data: successfully terminated")
    return torch.Tensor(features), np.array(labels)



# def prepare_data(fin, with_labels=True, normalize=False, n_pca=0):
#     """
#     Reads a dataset in CSV format from the ones in datasets/
#     """
#     df = pd.read_csv(fin + '.csv', sep=',')
#     n = len(df.columns)

#     if with_labels:
#         x = np.double(df.values[:, 0:n - 1])
#         labels = df.values[:, (n - 1)]
#         labels = labels.astype(str)
#         colnames = df.columns[0:n - 1]
#     else:
#         x = np.double(df.values)
#         labels = ['unknown'] * np.size(x, 0)
#         colnames = df.columns

#     n = len(colnames)

#     idx = np.where(np.std(x, axis=0) != 0)[0]
#     x = x[:, idx]

#     if normalize:
#         s = np.std(x, axis=0)
#         s[s == 0] = 1
#         x = (x - np.mean(x, axis=0)) / s

#     if n_pca:
#         if n_pca == 1:
#             n_pca = n

#         nc = min(n_pca, n)
#         pca = PCA(n_components=nc)
#         x = pca.fit_transform(x)

#     labels = np.array([str(s) for s in labels])

#     return torch.DoubleTensor(x), labels


def connect_knn(KNN, distances, n_components, labels):
    """
    Given a KNN graph, connect nodes until we obtain a single connected
    component.
    """
    c = [list(labels).count(x) for x in np.unique(labels)]

    cur_comp = 0
    while n_components > 1:
        idx_cur = np.where(labels == cur_comp)[0]
        idx_rest = np.where(labels != cur_comp)[0]
        d = distances[idx_cur][:, idx_rest]
        ia, ja = np.where(d == np.min(d))
        i = ia
        j = ja

        KNN[idx_cur[i], idx_rest[j]] = distances[idx_cur[i], idx_rest[j]]
        KNN[idx_rest[j], idx_cur[i]] = distances[idx_rest[j], idx_cur[i]]

        nearest_comp = labels[idx_rest[j]]
        labels[labels == nearest_comp] = cur_comp
        n_components -= 1

    return KNN


def compute_rfa(features, distfile, mode='features', k_neighbours=15, distfn='sym', 
    connected=False, sigma=1.0, distlocal='minkowski'):
    """
    Computes the target RFA similarity matrix. The RFA matrix of
    similarities relates to the commute time between pairs of nodes, and it is
    built on top of the Laplacian of a single connected component k-nearest
    neighbour graph of the data.
    """
    start = timeit.default_timer()
    if mode == 'features':
        KNN = kneighbors_graph(features,
                               k_neighbours,
                               mode='distance',
                               metric=distlocal,
                               include_self=False).toarray()
    # precomputed matrix
    else:
        # read distance matrix
        distance_matrix = pd.read_csv(distfile)
        
        # Holds the trained KNN model, which can be used to find the k nearest neighbors for any new data point based on the precomputed distances stored in distance_matrix.
        knn_distance_based = NearestNeighbors(n_neighbors=k_neighbours,
                                metric="precomputed").fit(distance_matrix)

        # computes the k-nearest neighbors graph based on the provided distance matrix. It returns a sparse matrix representation of the graph.
        # The resulting KNN array will contain the distances between the data points, where each row corresponds to a data point and each column corresponds to a neighbor.
        # metric=distlocal not here because it has already been calculated
        # metrics allowed : cityblock, cosine, euclidean, haversine, l1, l2, manhattan, nan_euclidean
        KNN = knn_distance_based.kneighbors_graph(distance_matrix,
                                                  k_neighbours+1, 
                                                  mode='distance').toarray()

    if 'sym' in distfn.lower():
        KNN = np.maximum(KNN, KNN.T)
    else:
        KNN = np.minimum(KNN, KNN.T)    

    n_components, labels = csgraph.connected_components(KNN)

    if connected and (n_components > 1):
        from sklearn.metrics import pairwise_distances
        distances = pairwise_distances(features, metric=distlocal)
        print(len(distances))
        KNN = connect_knn(KNN, distances, n_components, labels)
        
    if distlocal == 'minkowski':
        # sigma = np.mean(features)
        S = np.exp(-KNN / (sigma*features.size(1)))
        # sigma_std = (np.max(np.array(KNN[KNN > 0])))**2
        # print(sigma_std)
        # S = np.exp(-KNN / (2*sigma*sigma_std))
    else:
        S = np.exp(-KNN / sigma)

    S[KNN == 0] = 0
    print("Computing laplacian...")    
    L = csgraph.laplacian(S, normed=False)
    print(f"Laplacian computed in {(timeit.default_timer() - start):.2f} sec")

    print("Computing RFA...")
    start = timeit.default_timer()
    RFA = np.linalg.inv(L + np.eye(L.shape[0]))
    RFA[RFA==np.nan] = 0.0
    
    print(f"RFA computed in {(timeit.default_timer() - start):.2f} sec")

    return torch.Tensor(RFA)

