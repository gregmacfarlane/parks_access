import sys
import os

import osmnx as ox
import networkx as nx
import math

import numpy as np
import pandas as pd
import multiprocessing as mp
import pickle
import time


def get_shortest_paths(df):
    """
    :param df:
    :return: dictionary
    """
    park_points = pd.read_csv("data/park_points.csv")
    # TODO: remove sampling
    park_sample_ids = park_points.sample(5).id
    park_points.set_index('id', inplace=True)
    park_points = park_points.loc[park_sample_ids]

    park_ids = park_points.index.unique()

    # get graph information
    print("Getting graph information")
    with open("data/graph.file", "rb") as f:
        graph = pickle.load(f)

    with open("data/graph_proj.file", "rb") as f:
        graph_proj = pickle.load(f)

    # output file
    write_file = "data/shortest_paths_" + str(os.getpid()) + ".csv"
    f = open(write_file, "w+")
    f.write("geoid, park_id, distance\n")

    i = 1
    for bg in df.itertuples():
        # update progress
        location = i / len(df) * 100
        sys.stdout.write("Getting block group %d, %d%% completed \r" % (i, location))
        sys.stdout.flush()
        i += 1

        # loop through parks
        for park in park_ids:
            these_points = park_points.loc[[park]]

            # loop through points
            min_dist = float("inf")
            for point in these_points.itertuples():
                # check euclidean distance
                dx = point.LONGITUDE - bg.LONGITUDE
                dy = point.LATITUDE - bg.LATITUDE
                euc_dist = math.sqrt(dx**2 + dy**2)
                if euc_dist > 5000:
                    min_dist = euc_dist
                    break

                # get length between park and this edge point
                try:
                    length = nx.astar_path_length(graph_proj, source=bg.node, target=point.node,
                                                     weight='length')
                except:
                    length = float("inf")

                # check if this is the shortest one we've found; if so, update.
                if length < min_dist:
                    min_dist = length

            # write out the length between the block group and this park
            f.write(str(bg.Index) + ", " + str(park) + ", " + str(min_dist) + "\n")

    # close the buffer
    f.close()



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



def get_graph(place, mode, crs):
    """
    Get a graph for the place and write both the original graph and the projected directed
    graph to file
    :param place:
    :param mode: One of "drive", "walk", etc.
    :return: OSMNX projected graph
    """

    # Get the graph and make it a non multigraph
    graph = ox.graph_from_place(place, network_type=mode)
    graph = nx.DiGraph(graph)

    # write to file
    with open("data/graph.file", "wb") as f:
        pickle.dump(graph, f)

    # project to UTM zone 18 N and simplify
    graph_proj = ox.project_graph(graph, to_crs=crs)
    graph_proj = nx.DiGraph(graph_proj)
    with open("data/graph_proj.file", "wb") as f:
        pickle.dump(graph_proj, f)

    return graph_proj


def create_ddict(id1, id2, value=float("inf")):
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



def find_node(df):
    """
    Function to find the nearest node in a network to lat,long columns in data frame
    :param df:  Pandas data frame with lat, long information
    """
    with open("data/graph.file", "rb") as f:
        graph = pickle.load(f)

    df['node'] = df.apply(lambda row:
      ox.get_nearest_node(graph, (row.LATITUDE, row.LONGITUDE)), axis=1)
    return df

def parallel_find_node(df):
    n_cores = mp.cpu_count()
    df_split = np.array_split(df, mp.cpu_count())
    pool = mp.Pool(n_cores)
    df = pd.concat(pool.map(find_node(df_split)))
    pool.close()
    pool.join()
    return df


if __name__ == "__main__":
    # get block groups
    blockgroups = pd.read_csv("data/blockgroups_nonode.csv")
    blockgroups.set_index('GEOID', inplace=True)
    blockgroups = blockgroups.sample(20)

    # get park points
    park_points = pd.read_csv("data/park_points_nonode.csv")
    park_points.set_index('id', inplace=True)

    # get node information
    print("Determining node locations")
    blockgroups = find_node(blockgroups)
    park_points = find_node(park_points)

    # create dictionary to fill with shortest paths
    print("Getting shortest paths")
    a = time.process_time()
    get_shortest_paths(blockgroups)
    b = time.process_time()
    b-a



