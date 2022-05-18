# find-professors-by-keyword
-----------------------------
Overview
-----------------------------
The goal of this module is to be able to rank professors whose papers appear in the MAG dataset based on their relation to keywords in a field. keywords are given as an input and this module ranks these professors based on two main categories. 

The first metric is ranking professors based on whether they are pioneers in a field. The second metric, on the other hand, takes in different features that affect the ranking of professors to related keywords by impacting the score of the professors. These factors in the last metric include a ranking based on year of publication of the papers of the professors, based on the total number of citations of the professor, based on frequency of publications of the professor especially in more recent years and finally, based on whether there were more co-authors to papers they published (as opposed to them being the sole publisher).
<br/>

Demo
-----------------------------
[![Watch the video](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/video3605113157.mp4)

Setup
-----------------------------
- Clone the repository
- do 'pip install -r requirements'
- cd into the src_code directory
- run
<pre> python [keywords] [score rank] [pioneer rank] </pre>
- If a ranking based on score is chosen then four more arguments must be entered:
<pre> [year factor] [citation] [frequency of publication] [author count] </pre>
Project Structure
-----------------------------
sanjana-pingali-find-professors-by-keyword/
</br>
├── src_code    &nbsp;   &nbsp;                                  # main bulk of the code for the module </br> 
&nbsp;   &nbsp;   &nbsp;├── rank_researchers.py    # main file that contains code for ranking </br> 
&nbsp;   &nbsp;   &nbsp;└── utility.py             # helper file to help ranking  </br>  
├── images    &nbsp;   &nbsp;                                  # images for the README </br>  
├── requirements.txt </br>
└── README.md </br>

Functional Design
-----------------------------
store_keywords: For each input keyword this function generates 10 similar keywords to it.  </br>
author_count_per_paper: Stores number of authors for each paper  </br>
compute_author_keyword_ranks: finds the score of how much each keyword matches a given paper.  </br>
get_authors: Stores information related to authors such as the keywords associated with each, the papers associated with each and also gets list of viable authors for consideration.  </br>
get_author_citations: obtains citation count for each author and also maximum citations for any author relating to all parent keywords.  </br>
rank_authors_keyword:function that ranks the authors.  </br>



Algorithmic Design
-----------------------------
The goal of this module is to rank researchers given a set of keywords.
1. The keywords (k_i) we recieve from the user are k1...kn.
2. All keywords (ak_j) are represented as ak_1... ak_x
3. Papers are represented as p1...py.
4. The similarity score between a paper and keyword is s_j,y.

Ranking based on Score: </br>

Obtain a set of keywords from the user and an input indication of which criteria we want to rank based on. If the ranking criteria is based on score,  the criteria for a score ranking can be based on the years of their publications, the amount of citations of the author based on how active an author is in a field in more recent years and how many co-authors tend to contibute to this authors papers.


1. The idea of ranking based on year of publication accounts for the year the paper was published in. If the paper was published more recently it should be more relevant and it is given a higher paper-keyword similarity score compared to an older paper. This is done by weighting the score betweeen a keyword and paper with a higher weight for more recent years. This is done by using a geometric sequence (with constant as 0.9) formula to reduce the similarity value since the constant is below 1 and the exponent is the different between current year and year of publication.

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/year_.JPG)


This will affect the similarity value between papers and keywords so that papers that are too old by a specific author linked to these words will not be given as much importance.

2. The next criteria that is used for ranking is the amount of citations for that particular author. The paper-keyword similarity score that is generated is reduced for authors with lower number of citations compared to others with authors related to these similar keywords. This is done by adding up the sum of citations of a certain author across all papers and dividing it by the largest number of citations for a single author and then scaling the paper-keyword similarity score according to this value.

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/cit_.JPG)

3. The third metric that can contribute to the ranking of a researcher based on their score is basing it on how active a researcher has been in a field. A researchers activity in a field can be computed by finding the sum of total papers published by the researcher in the past five years divided by the total number of papers the researcher had published. This then gives a weightage of the relative publications of a researcher in more recent years as compared to the rest of their career. This weight is then multiplied by the sum of the paper-keyword rankings for a particular author. 

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/freq_of_words.JPG)

4. The fourth and final metric when it comes to ranking an author based on score is based on the number of authors that contribute to a paper. This metric scales the paper-keyword similarity score of a paper based on how much eah author has contributed to that paper. If more authors contibute that paper paper-keyword similiarity score goes down. This is done by dividing the score by the total number of authors that have contributed to it.

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/no_of_authors.JPG)


After these criteria we get a final rank value for the authors given a keyword based on score.

Ranking based on Initial Contributions to the field: </br>

This module is separate of score and depends on the ranking of a researcher in a field if they had contributed a large amount in the beginning when the field was first recognized. This module does this by finding out the year one of the input keywords was first coined or the first time a paper was based on an input keyword and finds only papers that were published earlier than 10 years after that. These researchers are then ranked according to descending order of score and researchers that contributed the most in that time period should be ranked higher.

Future Work
-----------------------------
I had also started work on another module which is ranking professors in a field based on the criteria of whether they were upcoming and publishing more recent years. I was aiming at using linear regression to predict the trend of their publications in the last 5 years and extrapolate these datapoints to predict for the next few years too. This module unfortunatley, was not able to be completed.
