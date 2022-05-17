import mysql.connector
import argparse
import datetime
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import interpolate

import pyodbc

from utility import gen_sql_in_tup

x = datetime.datetime.now()

current_year = int(x.year)


def store_keywords(db,keyword_ids, make_copy=True):
    """
    Stores top 10 similar keywords for each input keyword
    Arguments:
    - keyword_ids: list of ids of input keywords
    - cur: db cursor
    Returns: None. each entry in Top_Keywords table is of the form (parent_id, keyword_id, npmi).
    - parent_id: id of the original input keyword
    - keyword_id: id of similar keyword
    - npmi is a similarity score between the two keywords
    Note: the identity row for each keyword_id is included by default with
    similarity score 1 (i.e. for each kw_id in keywords_ids, there will be a
    row in Top_Keywords of (kw_id, kw_id, 1))
    """
    fields_in_sql = gen_sql_in_tup(len(keyword_ids))
    cur = db.cursor()
    drop_table_sql = "DROP TABLE IF EXISTS Top_Keywords"
   
    cur.execute(drop_table_sql)
   

    get_related_keywords_sql = """
        CREATE TABLE Top_Keywords (
            parent_id INT,
            id INT,
            npmi DOUBLE,
            PRIMARY KEY(parent_id, id)
        )
        SELECT parent_id, id, npmi
        FROM
        (
            SELECT parent_id, id, npmi,
            @kw_rank := IF(@current_parent = parent_id, @kw_rank + 1, 1) AS kw_rank,
            @current_parent := parent_id
            FROM
            (
                (SELECT id2 AS parent_id,
                id1 AS id, npmi
                FROM FoS_npmi_Springer
                WHERE id2 IN """ + fields_in_sql + """)
                UNION
                (SELECT
                id1 AS parent_id,
                id2 as id, npmi
                FROM FoS_npmi_Springer
                WHERE id1 IN """ + fields_in_sql + """)
            ) as top_keywords
            ORDER BY parent_id, npmi DESC
        ) AS ranked_keywords
        WHERE kw_rank <= 10
    """
    
    get_related_query_params = 2 * keyword_ids
    cur = db.cursor()
    cur.execute(get_related_keywords_sql, get_related_query_params)
   

    append_given_sql = """
        INSERT INTO Top_Keywords
        (parent_id, id, npmi)
        VALUES
        """ + ",\n".join(["(%s, %s, 1)"] * len(keyword_ids))

    append_given_query_params = [id for id in keyword_ids for i in range(2)]
    cur = db.cursor()
    cur.execute(append_given_sql, append_given_query_params)

def author_count_per_paper(db):
    """
    Stores the number of authors that co-authored a singular paper
    Arguments:
    - db: The current database
    Returns: None
    """
    cur = db.cursor()
    drop_table_sql = "DROP TABLE IF EXISTS Author_count_per_paper"
    cur.execute(drop_table_sql)

    Author_count_per_paper = """
       CREATE TABLE Author_count_per_paper (
        publication_id BIGINT NOT NULL,
        author_count INT,
        PRIMARY KEY(publication_id)
    )
     SELECT publication_mag_id as publication_id, COUNT(author_id) as author_count
     FROM Publication_Author
     GROUP BY publication_mag_id
    """

    cur = db.cursor()
    cur.execute(Author_count_per_paper)

    cur.close()


def compute_author_keyword_ranks(db,year_flag, author_count_per_paper_flag, pioneer_flag):
    """
    Computes and stores score for each publication
    Arguments:
    - cur: db cursor
    Returns: None
    Each publication has an associated score for each input keyword.
    The score between an input keyword and a paper is computed by determining if there is any match between the top ten similar keywords for the input keyword and the paper's keyword assignments (see assign_paper_kwds.py for details on  how keywords are assigned to papers).
    The maximum scoring match is picked and the final score for an input
    keyword is computed as max_npmi * citation. A score is computed for each
    publication-keyword pair.
    """

    cur = db.cursor()
    drop_table_sql = "DROP TABLE IF EXISTS Author_Keyword_Scores"
    cur.execute(drop_table_sql)

    create_author_ranks_sql = """
        CREATE TABLE Author_Keyword_Scores (
            author_id BIGINT,
            parent_id INT,
            kw_id BIGINT,
            citation INT,
            publication_id BIGINT,
            year INT,
            comp_score DECIMAL,
            title VARCHAR(255),
            PRIMARY KEY(author_id, publication_id, parent_id)
        )
        SELECT author_id,
        parent_id,
        MIN(FoS_id) AS kw_id,
        MAX(max_npmi) AS max_npmi,
        citation,
        Publication_Scores.publication_id as publication_id,
        year, 
        CASE
           WHEN """ + str(author_count_per_paper_flag) +""" = 1 THEN int_score*MAX(max_npmi) * citation/Author_count_per_paper.author_count
        ELSE MAX(max_npmi) * citation*int_score
        END AS comp_score,
        Publication_Scores.publication_title AS title
        FROM
        (
            SELECT author_id, Publication_FoS.publication_id, Publication.year AS year, 
            MAX(npmi) as max_npmi, Publication.title as publication_title,
            IFNULL(citation, 0) AS citation,
            CASE 
            WHEN """ + str(year_flag) +""" = 1 THEN POWER(0.9,(%s-year))
            ELSE 1
            END AS int_score
            FROM Top_Keywords
            JOIN Publication_FoS ON Top_Keywords.id = FoS_id
            JOIN Publication_Author ON publication_mag_id = Publication_FoS.publication_id
            JOIN Publication ON Publication_FoS.publication_id = Publication.id
            GROUP BY author_id, Publication.id, parent_id
        ) AS Publication_Scores
        JOIN 
        (
            SELECT publication_id,
            parent_id, FoS_id, npmi
            FROM Top_Keywords
            JOIN Publication_FoS ON FoS_id = id
        ) AS Publication_Top_Keywords
        ON ABS(max_npmi - npmi) < 0.000001
        AND Publication_Top_Keywords.publication_id = Publication_Scores.publication_id 
        JOIN Author_count_per_paper ON Author_count_per_paper.publication_id = Publication_Top_Keywords.publication_id
        GROUP BY author_id, Publication_Scores.publication_id, parent_id
    """
   
    cur = db.cursor()
    cur.execute(create_author_ranks_sql, (current_year,))

    cur.close()

def get_authors(db, pioneer_flag, min_year, keyword_ids):
    """
    Stores the authors and the papers each author published as a dictionary,
    the main keywords inputted that are associated with each author and finally,
    the list of authors where keywords are related to all the input keywords.
    Arguments:
    - db: The current database
    - pioneer_flag: flag to determine whether to rank according to pioneers in a field
    - min_year : the earliest year one of the keyword input was related to a paper
    - keyword_ids: a list of the ids of the keywords that were input
    Returns: 
    -list_of_authors:the list of authors where keywords are related to all the input keywords
    - dict_of_authors:  a dictionary of the authors and the papers each author published
    -dict_of_author_keywords: a dictionary of the main keywords inputted that are associated with each author 

    """
    dict_of_authors = {}
    dict_of_author_keywords = {}
 
    get_author_papers = """
            SELECT author_id, Author_Keyword_Scores.title as title,row_number() over (partition by author_id order by comp_score desc) as publication_rank, parent_id, year
            FROM Author_Keyword_Scores
            WHERE year <=
            CASE %s 
            WHEN 1 THEN %s + 10
            WHEN 0 THEN %s + 2000
            END
            GROUP BY Author_Keyword_Scores.title
    """
    cur = db.cursor()
    cur.execute(get_author_papers, (pioneer_flag, min_year, min_year,))
    author_papers = cur.fetchall()
    for each_record in author_papers:
        if each_record[0] not in dict_of_author_keywords:
              dict_of_author_keywords[each_record[0]] = [each_record[3]]
        else:
                dict_of_author_keywords[each_record[0]].append(each_record[3])
    for each_record in author_papers:
        if set(keyword_ids) == set(dict_of_author_keywords[each_record[0]]): #only get the authors that have all parent keywords
            if each_record[2] <=5: # restrict to top 5 entries
                if each_record[0] not in dict_of_authors: # only then add author and its list of titles
                    dict_of_authors[each_record[0]] = [each_record[1]] 
                else:
                    dict_of_authors[each_record[0]].append(each_record[1])
        list_of_authors = tuple(dict_of_authors.keys()) # get all relevant authors
    
    return list_of_authors, dict_of_authors, dict_of_author_keywords

def get_author_citations(db):
    """
   To obtain maximum citations of any author that is related to all input keywords
    Arguments:
    - db: The current database
    Returns: 
    -dict_of_author_citation: total sum of citations of each author
    -max_value: get highest no of citations to normalize

    """
    dict_of_author_citation = {}

    get_author_citations = """
        SELECT author_id, SUM(citation)
        FROM Author_Keyword_Scores
        GROUP BY author_id
    """
    cur = db.cursor()
    cur.execute(get_author_citations)
    author_citations = cur.fetchall()

    for each_author_citation in author_citations:
         dict_of_author_citation[each_author_citation[0]] = each_author_citation[1]

    max_value = dict_of_author_citation[max(dict_of_author_citation, key=dict_of_author_citation.get)] # get key of highest value to normalize

    return dict_of_author_citation, max_value


def rank_authors_keyword(keyword_ids, db, year_flag, citation_flag, frequency_of_publication_flag, author_count_per_paper_flag, pioneer_flag):
    """
    Main function that returns the top ranked authors for some keywords
    Arguments:
    - keyword_ids: list of keyword ids by which we must rank
    - cur: db cursor
    Returns: list of python dicts each representing an author.
    Each dict has keys 'name', 'id', and 'score' of author. During ranking
    each keyword is weighted separately and equally.
    """

    
    # Store top similar keywords
    store_keywords(db, keyword_ids)

    #obtains the total author count for each publication 
    author_count_per_paper(db)

    # Compute scores between each publication and input keyword
    compute_author_keyword_ranks(db,year_flag, author_count_per_paper_flag, pioneer_flag)

    min_year = 0

    if pioneer_flag == 1:
        cur = db.cursor()

        min_year_keywords = """
        SELECT MIN(T1.year) as min_year
        FROM (SELECT parent_id,year
        FROM Author_Keyword_Scores
        where year !=0 AND parent_id = kw_id
        ) as T1
        """

        cur.execute(min_year_keywords)

        min_year = cur.fetchall()[0][0]
        
        cur.close()

    list_of_authors, dict_of_authors, dict_of_author_keywords = get_authors(db, pioneer_flag, min_year, keyword_ids)

    dict_of_author_citation, max_value = get_author_citations(db)


    get_author_ranks_sql = """
        SELECT Author.id, Author.name, Author_Keyword_Scores.title,
        CASE 
            WHEN """ + str(frequency_of_publication_flag) +""" = 1 THEN (publication_count_5_years/publication_count)*int_score
            ELSE int_score
        END AS score
        FROM Author_Keyword_Scores
        JOIN Author ON Author.id = Author_Keyword_Scores.author_id JOIN
                                (SELECT Author_Keyword_Scores.author_id, COUNT(*) as publication_count, publication_count_5_years,
                                    CASE 
                                        WHEN """ + str(citation_flag) +""" = 1 THEN (SUM(Author_Keyword_Scores.citation)/%s)*SUM(comp_score)
                                        ELSE SUM(comp_score)
                                    END AS int_score
                                FROM Author_Keyword_Scores JOIN ( SELECT author_id, COUNT(*) as publication_count_5_years
                                                                    FROM Author_Keyword_Scores
                                                                    WHERE %s- year <=5
                                                                    GROUP BY author_id
                                ) inner_query ON inner_query.author_id = Author_Keyword_Scores.author_id  
                                WHERE Author_Keyword_Scores.author_id IN """ + str(list_of_authors) + """
                                GROUP BY Author_Keyword_Scores.author_id
                                ) as T1 ON T1.author_id = Author_Keyword_Scores.author_id
        WHERE year <=
        CASE %s 
        WHEN 1 THEN %s + 10
        WHEN 0 THEN %s + 2000
        END
        AND year !=
        CASE %s 
        WHEN 1 THEN 0
        WHEN 0 THEN 100000
        END
        GROUP BY Author_Keyword_Scores.author_id
        ORDER BY score DESC
        LIMIT 15    
    """
    cur = db.cursor()
    cur.execute(get_author_ranks_sql, (max_value,current_year,pioneer_flag, min_year,min_year,pioneer_flag,))
    author_ranks = cur.fetchall()



    res = [{
        'id': t[0], 
        'name': t[1],
        'score' : t[3],
        'titles' : dict_of_authors[t[0]]
        } for t in author_ranks]

    for t in author_ranks:
        print('id:', t[0])
        print('name:', t[1])
        print('score:', t[3])
        print('titles:')
        i=1
        for author_title in dict_of_authors[t[0]]:
                rank  = str(i) + "."
                print(rank, author_title)
                i= i+1


    top_author_ids = [t["id"] for t in res]

    author_id_to_idx = {}
    for i in range(len(top_author_ids)):
        author_id = top_author_ids[i]
        author_id_to_idx[author_id] = i

    cur.close()
    #return res


def main():

   # Setting up db
    db = mysql.connector.connect(
    host='localhost',
    user="root",
    password=<password>,
    database=<database>
    )
    
    cur = db.cursor()

    parser = argparse.ArgumentParser()
    parser.add_argument('keywords', type=str, nargs='+',
                        help='keywords in search query. Separate with spaces')
    parser.add_argument('score_flag', type = int)
    parser.add_argument('pioneer_flag', type = int)
    args = parser.parse_args()

    year_flag =0
    citation_flag =0
    frequency_of_publication_flag=0
    author_count_per_paper_flag=0
   
    if args.score_flag== 1:
        input_ = input("Which Features do you want to put emphasize on?")
        year_flag, citation_flag,frequency_of_publication_flag,author_count_per_paper_flag =  input_.split(" ")


    # Ids of all keywords can be found in FoS table
    # Corresponds to keywords 'machine learning'

    fields_in_sql = gen_sql_in_tup(len(args.keywords))
    get_ids_sql =  """SELECT id FROM FoS where FoS_name IN """ + fields_in_sql + """;"""

    cur.execute(get_ids_sql, args.keywords)
    result = cur.fetchall()
    keyword_ids = tuple(row_tuple[0] for row_tuple in result)

    top_authors = rank_authors_keyword(keyword_ids, db, year_flag,citation_flag, frequency_of_publication_flag, author_count_per_paper_flag, args.pioneer_flag)

if __name__ == '__main__':
    main()