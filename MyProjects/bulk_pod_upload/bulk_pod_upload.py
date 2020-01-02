""" a program which accepts 2 arguments, the tripcode and the filename of a POD to be uploaded.
the program will then add that POD to every delivery under the named tripcode AND update the status to PODed 
AND actual delivery time to planned delivery time
"""
import configparser
import os
import re

import sqlalchemy

# instatiate the list of alpha ids
alphaids = []

# read in the program variables
config = configparser.ConfigParser()
config.read("C:\Script\Batch_Upload\config.ini")
dir_path = config["VARS"]["dir_path"]
pod_dir = config["VARS"]["pod_dir"]

# read in the DB variables
user = config["DATABASE"]["user"]
password = config["DATABASE"]["password"]
servername = config["DATABASE"]["servername"]
database = config["DATABASE"]["database"]

pod_file = input(
    "Filename of the POD file you have pasted into the pod folder: "
)
while not os.path.exists(pod_dir+pod_file):
    pod_file = input(f"'{pod_file}' does not exist in dir: {pod_dir}\n\nEnter a valid filename: ")

# SQL global vars
connection_string = f"mssql+pymssql://{user}:{password}@{servername}/{database}"
engine = sqlalchemy.create_engine(connection_string)
conn = engine.connect()

# retrieve a list of all shipmentmasterIDs for the named tripcode
def sql_import():
    trip_code = input("What is the trip code: ")
    sql_query = """select ALPHAID from SHIPMENT SHP 
        JOIN TRANSPORTREQUESTSHIPMENTS TRS ON SHP.SHIPMENTID = TRS.SHIPMENTID 
        JOIN TRANSPORTREQUEST TR ON TR.TRANSPORTREQUESTID = TRS.TRANSPORTREQUESTID
        WHERE TR.CODE = '"""
    rs = conn.execute(sql_query+trip_code+"'")

    while rs.rowcount == 0:
        trip_code = input("No such trip code exists, enter a valid trip code: ")
        rs = conn.execute(sql_query+trip_code+"'")

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
def sql_insert_update():
    update = input("Would you like to update all deliveries to PODed status AND update delivered times to planned delivery time? (y/n)")
    while update not in ('y','n'):
        update = input("Please enter a valid selection (y/n): ")
    for alphaid in alphaids:
        conn.execute(
            f"""INSERT INTO SHIPMENTMASTERCOMMENT(SHIPMENTMASTERID,COMMENTTYPEID,SUBJECT,CONTENT,CREATEDON,CREATEDBYID)
                VALUES({alphaid},
                (SELECT
                CASE WHEN (SELECT MAX(SHIPMENTMASTERID) FROM SHIPMENTMASTERCOMMENT WHERE SHIPMENTMASTERID = {alphaid} AND COMMENTTYPEID BETWEEN 961 AND 969) IS NULL 
                THEN 961
                ELSE (SELECT MAX(COMMENTTYPEID)+1 FROM SHIPMENTMASTERCOMMENT WHERE SHIPMENTMASTERID = {alphaid} AND COMMENTTYPEID BETWEEN 961 AND 969)
                END)
                ,'MaasaiPath','{pod_file}',GETDATE(),1)"""
        )
        if update == 'y':
            conn.execute(
            f"""UPDATE SHIPMENT SET ACTUALCOLLECTDATE = DELIVERYDATE, 
					ACTUALDELIVERDATE = DATEADD(minute, 7, DELIVERYDATE), 
					CUSTOMCOMMENT13 = 'ON TIME', 
					CUSTOMCOMMENT14 = 'DOTHit', 
					PHYSICALSTATUSNAMEID = 4100 
		        WHERE ALPHAID = {alphaid}
            """
            )
         
    conn.close()

try:
    sql_import()
    create_and_copy()
    sql_insert_update()
except Exception as ex:
    print("The below error occured:\n\n",ex)

input("Completed Successfully, press any key to exit")