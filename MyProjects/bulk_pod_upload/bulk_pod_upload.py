""" a program which accepts 2 arguments, the tripcode and the path of a POD to be uploaded.
the program will then add that POD to every delivery under the named tripcode

To DO:
- error handling
- handle if attachment already exists (dontoverride 961 SMCid)
- bundle into .exe
- correct config variables
- update config read path
"""
import configparser
import os
import re

import sqlalchemy

# instatiate the list of alpha ids
alphaids = []
trip_code = input("What is the trip code: ")
pod_file = input(
    "Filename of the POD file you have pasted into the pod folder: "
)
correct = input("Are you sure the above variables are correct? (y/n): ")

while correct == "n":
    trip_code = input("What is the trip code: ")
    pod_file = input(
        "Filename of the POD file you have pasted into the pod folder: "
    )
    correct = input("Are you sure the above variables are correct? (y/n): ")

# read in the 2 program variables
config = configparser.ConfigParser()
config.read(r"MyProjects\bulk_pod_upload\config.ini")
dir_path = config["VARS"]["dir_path"]
pod_dir = config["VARS"]["pod_dir"]


# read in the DB variables
user = config["DATABASE"]["user"]
password = config["DATABASE"]["password"]
servername = config["DATABASE"]["servername"]
database = config["DATABASE"]["database"]

# SQL global vars
connection_string = f"mssql+pymssql://{user}:{password}@{servername}/{database}"
engine = sqlalchemy.create_engine(connection_string)
conn = engine.connect()

# validate the variables collecting in the first section
def validate_vars():
    pass
    
# retrieve a list of all shipmentmasterIDs for the named tripcode
def sql_import():
    sql_query = f"""select ALPHAID from SHIPMENT SHP 
        JOIN TRANSPORTREQUESTSHIPMENTS TRS ON SHP.SHIPMENTID = TRS.SHIPMENTID 
        JOIN TRANSPORTREQUEST TR ON TR.TRANSPORTREQUESTID = TRS.TRANSPORTREQUESTID
        WHERE TR.CODE = '{trip_code}'
        """
    rs = conn.execute(sql_query)
    # create a list with all the elements and remove parentheses and commas
    for row in rs:
        row = str(row)
        row = re.sub("[(),]", "", row)
        alphaids.append(row)


# create a new folder in directory for all shipmentmasterIDs and copy in the POD file
def create_and_copy():
    for alphaid in alphaids:

        if not os.path.exists(dir_path+alphaid):
            os.mkdir(dir_path + alphaid)
        os.popen(f"copy {pod_dir+pod_file} {dir_path+alphaid}")


# insert new line into shipmentmastercomment table for each delivery
def sql_insert():
    for alphaid in alphaids:
        conn.execute(
            f"""INSERT INTO SHIPMENTMASTERCOMMENT(SHIPMENTMASTERID,COMMENTTYPEID,SUBJECT,CONTENT,CREATEDBYID)
                VALUES({alphaid},961,'MaasaiPath','{pod_file}',1)"""
        )
    conn.close()


sql_import()
create_and_copy()

#sql_insert()
