import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """
    This procedure processes a song file whose filepath has been provided as an arugment.
    It extracts the song information in order to store it into the songs table.
    Then it extracts the artist information in order to store it into the artists table.

    INPUTS:
    * cur the cursor variable
    * filepath the file path to the song file
    
    artist_id
    artist_latitude
    artist_location
    artist_longitude
    artist_name
    duration
    num_songs
    song_id
    title
    year
    """
    # open song file
    df = pd.read_json(filepath, lines=True)
    # for col in df.columns: print(col)

    for value in df.values:
        # unpacking value 
        (artist_id, artist_latitude, artist_location, artist_longitude, artist_name, duration,
        num_songs, song_id, title, year) = value
        
        # insert artist record
        artist_data = [artist_id, artist_name, artist_location, artist_latitude, artist_longitude]
        cur.execute(artist_table_insert, artist_data)

        # insert song record
        song_data = [song_id, title, artist_id, year, duration]
        cur.execute(song_table_insert, song_data)
        
"""
also work:
        for artist in df[['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude']].values:
            cur.execute(artist_table_insert, artist)
"""   



def process_log_file(cur, filepath):
    """
    This procedure processes a log file whose filepath has been provided as an arugment.
    First, filtering by NextSong action to only keep the records with 'NextSong' in page.
    It extracts the time information in order to store it into the time table.
    Then it extracts the user information in order to store it into the user table.
    Also, it get songid and artistid from song and artist tables for the songplay table.
    Finally, ti extracts the required information for the songplay table.
    

    INPUTS:
    * cur the cursor variable
    * filepath the file path to the log file
    
    artist
    auth
    firstName
    print(df.head(1))
    gender
    itemInSession
    lastName
    length
    level
    location
    method
    page
    registration
    sessionId
    song
    status
    ts
    userAgent
    userId
    """
    # open log file
    df = pd.read_json(filepath, lines=True)
    # for col in df.columns: print(col)
    
    # filter by NextSong action
    # print(df['page'] == "NextSong") - boolean
    df = df[df['page'] == "NextSong"]

    # convert timestamp column to datetime
    # pd.to_datetime(1541262843796, unit='ms') -> Timestamp('2018-11-03 16:34:03.796000')
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')

    # insert time data records
    # create time table
    time_data = []
    for t in df['ts']:
        time_data.append([t, t.hour, t.day, t.week, t.month, t.year, t.day_name()])
    column_labels = ('start_time', 'hour', 'day', 'week', 'month', 'year', 'weekday')
    
    time_df = pd.DataFrame.from_records(time_data, columns=column_labels)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[["userId","firstName","lastName","gender","level"]]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
    
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        # total is 6820
        # song_id will auto increment in songplay_data
        songplay_data = (row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    """
    
    input: 
    cur: the cursor variable
    conn: connection to the database
    filepath: path to the song/log data
    func: the above 2 functions: process_song_file/process_log_file
    
    """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    """
    
    create connection to the database and the cursor
    call process_data to process all files
    
    """
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()