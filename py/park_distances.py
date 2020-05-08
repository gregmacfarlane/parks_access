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
    #park_sample_ids = "M010"
    #park_sample_ids = park_points.sample(20).id
    park_points.set_index('id', inplace=True)
    #park_points = park_points.loc[park_sample_ids]
    park_ids = park_points.index.unique()

    # get graph information
    print("Getting graph information")
    graph = ox.graph_from_place('New York City, New York, USA', network_type='walk')
    G = ox.project_graph(graph)

    # output file
    write_file = "data/shortest_paths_" + str(os.getpid()) + ".csv"
    f = open(write_file, "w+")
    f.write("geoid, park_id, distance, euc_dist\n")

    i = 1
    for bg in df.itertuples():
        # update progress
        location = (i - 1) / len(df) * 100
        sys.stdout.write("Getting block group %d, %d%% completed \r" % (i, location))
        sys.stdout.flush()
        i += 1

        source = ox.get_nearest_node(graph, (bg.LATITUDE, bg.LONGITUDE))
        # loop through parks
        for park in park_ids:
            these_points = park_points.loc[[park]]
            min_euc = float("inf")

            for point in these_points.itertuples():
                # find closest park point by Euclidean distance in projected coordinates
                dx = point.X - bg.X
                dy = point.Y - bg.Y
                euc_dist = math.sqrt(dx**2 + dy**2)

                if euc_dist < min_euc:
                    min_euc = euc_dist
                    closest_lat = point.LATITUDE
                    closest_lon = point.LONGITUDE

            try:
                target = ox.get_nearest_node(graph, (closest_lat, closest_lon))
                length = nx.shortest_path_length(G, source, target, weight='length')
            except:
                length = float("inf")

            # write out the length between the block group and this park
            f.write(str(bg.Index) + ", " + str(park) + ", " + str(length) + ", " + str(min_euc) + "\n")

    # close the buffer
    f.close()
    sys.stdout.write("\n ====== Finished ======\n")


def get_graph(place, mode):
    """
    Get a graph for the place and write both the original graph and the projected directed
    graph to file
    :param place:
    :param mode: One of "drive", "walk", etc.
    :return: OSMNX projected graph
    """

    # Get the graph and make it a non multigraph
    graph = ox.graph_from_place(place, network_type=mode)

    # project to specified CRS and simplify
    graph_proj = ox.project_graph(graph, to_crs=crs)

    return graph_proj



def find_node(df, G):
    """
    Function to find the nearest node in a network to lat,long columns in data frame
    :param df:  Pandas data frame with lat, long information
    """

    df['node'] = df.apply(lambda row:
      ox.get_nearest_node(G, (row.LATITUDE, row.LONGITUDE)), axis=1)
    return df


if __name__ == "__main__":
    #unit = int(sys.argv[1])
    #total_units = int(sys.argv[2])
    n_cores = mp.cpu_count() - 1

    # Read block group / tract centroid information
    print("====== Getting shortest paths =========")
    tracts = pd.read_csv("data/tract_centroids.csv")
    tracts.set_index('geoid', inplace=True)
    bg_split = np.array_split(tracts, n_cores)

    a = time.process_time()
    pool = mp.Pool(processes = n_cores)
    pool.map(get_shortest_paths, bg_split)
    b = time.process_time()
    b-a
    print(b-a)