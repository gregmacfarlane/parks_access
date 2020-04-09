import sys

import osmnx as ox
import networkx as nx

import numpy as np
import pandas as pd
import multiprocessing as mp
import pickle


def get_shortest_paths(blockgroups, park_points, graph, ddict):
    """
    :param blockgroups:
    :param park_points:
    :param graph:
    :param ddict:
    :return: dictionary
    """
    i = 1
    for bg in blockgroups.itertuples():
        # update progress
        location = i / len(blockgroups) * 100
        sys.stdout.write("Handling dictionary progress: %d%%  \r" % (location))
        sys.stdout.flush()
        i += 1

        # loop through parks
        for park in park_ids:
            these_points = park_points.loc[[park]]

            # loop through points
            for point in these_points.itertuples():
                # get length between park and this edge point
                try:
                    length = nx.shortest_path_length(graph_proj, source=bg.node, target=point.node,
                                                     weight='length')
                except:
                    length = float("inf")

                # check if this is the shortest one we've found; if so, update.
                if length < ddict[bg.Index][park]:
                    ddict[bg.Index][park] = length

    return ddict


def get_blockgroups(url, counties):
    """
    Get block group centroid data from the Census bureau
    :param url:
    :return:
    """
    # get the coordinates from census
    blockgroups = pd.read_csv(url)

    # pad the county and tract strings, and get the proper data types
    blockgroups.STATEFP = blockgroups.STATEFP.apply(str)
    blockgroups.BLKGRPCE = blockgroups.BLKGRPCE.apply(str)
    blockgroups.COUNTYFP = blockgroups.COUNTYFP.apply('{0:0>3}'.format)
    blockgroups.TRACTCE = blockgroups.TRACTCE.apply('{0:0>6}'.format)
    blockgroups['GEOID'] = blockgroups[['STATEFP', 'COUNTYFP', 'TRACTCE', 'BLKGRPCE']].apply(lambda x: ''.join(x), axis=1)

    blockgroups['LATITUDE'] = blockgroups['LATITUDE'].astype(float)
    blockgroups['LONGITUDE'] = blockgroups['LONGITUDE'].astype(float)

    # filter to counties
    blockgroups = blockgroups[blockgroups.COUNTYFP.isin(counties)]
    blockgroups.set_index('GEOID', inplace=True)
    return blockgroups



def get_graph(place, mode):
    """
    Get a graph for the place
    :param place:
    :param mode: One of "drive", "walk", etc.
    :return: OSMNX projected graph
    """
    graph = ox.graph_from_place(place, network_type=mode)
    graph_proj = ox.project_graph(graph)
    return graph_proj

def create_ddict(id1, id2, value = float("inf")):
    """
    Create a two-index dictionary with a given value
    :param id1: first index
    :param id2: second index
    :param value: value to fill in the dictionary with
    :return: The dictionary[id1][id2]: value
    """
    dict = {}
    i1 = 1
    for i in id1:
        location = i1 / len(id1) * 100
        sys.stdout.write("Handling dictionary progress: %d%%  \r" % (location))
        sys.stdout.flush()
        i1 += 1
        dict[i] = {}  # create a dictionary for the parks
        for j in id2:
            dict[i][j] = value
    return dict



def find_node(df, graph):
    """
    Function to find the nearest node in a network to lat,long columns in data frame
    :param df:  Pandas data frame with lat, long information
    """
    df['node'] = df.apply(lambda row:
      ox.get_nearest_node(graph, (row.LATITUDE, row.LONGITUDE)), axis=1)
    return df

def parallel_find_node(df, graph):
    n_cores = mp.cpu_count()
    df_split = np.array_split(df, mp.cpu_count())


if __name__ == "__main__":
    # get blockgroups data frame
    print("Getting blockgroups data from Census")
    url = "https://www2.census.gov/geo/docs/reference/cenpop2010/blkgrp/CenPop2010_Mean_BG36.txt"
    counties = ["081", "047", "061", "005", "085"]
    blockgroups = get_blockgroups(url, counties)

    # get node information
    print("Determining node locations")

    # read block group information
    blockgroups = pd.read_csv("data/blockgroups.csv")
    blockgroups = blockgroups.sample(5)
    blockgroups.set_index('GEOID', inplace=True)

    # read park points information
    park_points = pd.read_csv("data/park_points.csv")
    # TODO: run for all park points
    park_ids = park_points.sample(2).id

    park_points.set_index('id', inplace=True)
    park_points = park_points.loc[park_ids]

    # get graph information
    print("Getting graph information")
    #graph = ox.graph_from_place('New York, New York, USA', network_type='walk')
    #graph_proj = ox.project_graph(graph)
    with open("data/graph.file", "rb") as f:
        graph = pickle.load(f)

    with open("data/graph_proj.file", "rb") as f:
        graph_proj = pickle.load(f)


    # locate nodes
    print("Locating nodes for points")
    #blockgroups = find_node(blockgroups, graph)
    #park_points = find_node(park_points, graph)

    # create dictionary to fill with shortest paths
    print("Getting shortest paths")
    ddict = create_ddict(blockgroups.index.unique().array, park_points.index.unique().array)
    ddict = get_shortest_paths(blockgroups, park_points, graph_proj, ddict)


