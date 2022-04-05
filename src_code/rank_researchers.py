#from utils import gen_sql_in_tup, drop_table
import mysql.connector
import argparse
import datetime

x = datetime.datetime.now()

current_year = int(x.year)


def gen_sql_in_tup(num_vals):
    if num_vals == 0:
        return "(FALSE)"
    return "(" + ",".join(["%s"] * num_vals) + ")"

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
    #print("here2")
    cur.execute(drop_table_sql)
   
    #print("here1")

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

    #print("here2")
   

    append_given_sql = """
        INSERT INTO Top_Keywords
        (parent_id, id, npmi)
        VALUES
        """ + ",\n".join(["(%s, %s, 1)"] * len(keyword_ids))

    append_given_query_params = [id for id in keyword_ids for i in range(2)]
    cur = db.cursor()
    cur.execute(append_given_sql, append_given_query_params)

    




def compute_author_keyword_ranks(db,year_flag):
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
            WHEN """ + str(year_flag) +""" = 1 THEN POWER(0.9,(%s-year))*MAX(max_npmi) * citation
            ELSE MAX(max_npmi) * citation
        END AS comp_score,
        CASE
            WHEN Publication_Scores.publication_title LIKE %s THEN SUBSTRING(Publication_Scores.publication_title, 1, LENGTH(Publication_Scores.publication_title) - 1)
            ELSE Publication_Scores.publication_title
        END AS title
        FROM
        (
            SELECT author_id, publication_id, Publication.year AS year, 
            MAX(npmi) as max_npmi, Publication.title as publication_title,
            IFNULL(citation, 0) AS citation
            FROM Top_Keywords
            JOIN Publication_FoS ON Top_Keywords.id = FoS_id
            JOIN Publication_Author ON publication_mag_id = publication_id
            JOIN Publication ON publication_id = Publication.id
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
        GROUP BY author_id, Publication_Scores.publication_id, parent_id
    
    """
   
    cur = db.cursor()
    cur.execute(create_author_ranks_sql, (current_year,'%.'))

    cur.close()

    

    # copy_temporary_table(cur, "Author_Keyword_Scores")




def rank_authors_keyword(keyword_ids, db, year_flag, citation_flag, frequency_of_publication_flag):
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

    # Compute scores between each publication and input keyword

    compute_author_keyword_ranks(db,year_flag)


    # Aggregate scores for each author
    dict_of_authors = {}
    dict_of_author_keywords = {}

    get_author_papers = """
        SELECT TABLE1.author_id, Author.name, TABLE1.title, row_number() over (partition by Author.id order by TABLE1.comp_score desc) as publication_rank, TABLE1.parent_id
        FROM Author JOIN(
            SELECT author_id, Author_Keyword_Scores.title as title, parent_id, comp_score
            FROM Author_Keyword_Scores
            GROUP BY Author_Keyword_Scores.title
        ) AS TABLE1 ON TABLE1.author_id = Author.id
        GROUP BY TABLE1.title
    """
    cur = db.cursor()
    cur.execute(get_author_papers)
    author_papers = cur.fetchall()
    for each_record in author_papers:
        if each_record[0] not in dict_of_author_keywords:
              dict_of_author_keywords[each_record[0]] = [each_record[4]]
        else:
                dict_of_author_keywords[each_record[0]].append(each_record[4])
    for each_record in author_papers:
        if set(keyword_ids) == set(dict_of_author_keywords[each_record[0]]): #only get the authors that have all parent keywords
            if each_record[3] <=5: # restrict to top 5 entries
                if each_record[0] not in dict_of_authors: # only then add author and its list of titles
                    dict_of_authors[each_record[0]] = [each_record[2]] 
                else:
                    dict_of_authors[each_record[0]].append(each_record[2])
        list_of_authors = tuple(dict_of_authors.keys()) # get all relevant authors
   
    #print("here4")

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

    #print("here3")

    print(max_value)

    # get_author_ranks_sql = """
    #     SELECT Author.id, Author.name, Author_Keyword_Scores.title,SUM(comp_score) as score
    #     FROM Author_Keyword_Scores
    #     JOIN Author ON Author.id = Author_Keyword_Scores.author_id
    #     GROUP BY Author_Keyword_Scores.author_id
    #     ORDER BY score DESC
    #     LIMIT 15
    # """

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
        GROUP BY Author_Keyword_Scores.author_id
        ORDER BY score DESC
        LIMIT 15    
    """
    

    #cur.execute(get_author_ranks_sql)
    cur.execute(get_author_ranks_sql, (current_year,current_year,))
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
    password="14converseS@",
    database="database_week_4"
    )
    
    cur = db.cursor()

    parser = argparse.ArgumentParser()
    parser.add_argument('keywords', type=str, nargs='+',
                        help='keywords in search query. Separate with spaces')
    parser.add_argument('year_flag', type = int)
    parser.add_argument('citation_flag', type = int)
    parser.add_argument('frequency_of_publication_flag', type = int)
    args = parser.parse_args()

    # Ids of all keywords can be found in FoS table
    # Corresponds to keywords 'machine learning'

    fields_in_sql = gen_sql_in_tup(len(args.keywords))
    get_ids_sql =  """SELECT id FROM FoS where FoS_name IN """ + fields_in_sql + """;"""

    cur.execute(get_ids_sql, args.keywords)
    #print("here")
    result = cur.fetchall()
    keyword_ids = tuple(row_tuple[0] for row_tuple in result)

    #print(args.year_flag, args.citation_flag)

    top_authors = rank_authors_keyword(keyword_ids, db, args.year_flag, args.citation_flag,args.frequency_of_publication_flag)

if __name__ == '__main__':
    main()