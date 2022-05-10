# find-professors-by-keyword
-----------------------------
Overview
-----------------------------
The goal of this module is to be able to rank professors whose papers appear in the MAG dataset based on their relation to keywords in a field. keywords are given as an input and this module ranks these professors based on three main categories. 

The first metric is ranking professors based on whether they are pioneers in a field, the second ranks professors that are upcoming in a field and making more recent contributions higher and finally, the last metric takes in different features that affect the ranking of professors to related keywords by impacting the score of the professors. The factors in the last metric include a ranking based on year of citations of the professors, based in citations, based on frequency of publication and based on whether there were more co-authors to papers they published (as opposed to them being the sole publisher).
<br/>

Demo
-----------------------------

Setup
-----------------------------
- Clone the repository
- do 'pip install -r requirements'
- cd into the src_code directory
- run
<pre> python [keywords] [score rank] [pioneer rank] [upcoming researcher rank] </pre>
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

Algorithmic Design
-----------------------------
The goal of this module is to rank researchers given a set of keywords.

Obtain a set of keywords from the user and an input indication of which criteria we want to rank based on. The criteria ranking are based on the years of their publications, based on how active an author is in a field in more recent years and the amount of citations of the author.

1. The idea of ranking based on year of publication accounts for the year the paper was published in. If the paper was published more recently it should be more relevant and it is given a higher keyword similarity score compared to an older paper. This is done by weighting the score betweeen a keyword and paper with a higher weight for more recent years. This is done by using a geometric sequence (with constant as 0.9) formula to reduce the similarity value since the constant is below 1 and the exponent is the different between current year and year of publication.

Here this similarity is represented by s(in) where i is the paper being considered and n is the input keyword being considered. m iterates through 10 similar keywords for a keyword input.

![alt text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/equation_for_year_criteria.JPG)

This will affect the similarity value between papers and keywords so that papers that are too old by a specific author linked to these words will not be given as much importance.

2. The next criteria that is used for ranking is the amount of citations for that particular author. This ranking is based on the idea using a weight that is a result of adding up all citations across all papers of an author and dividing by the largest citations for a single author. This weight will be lowered the lower citations am author has to other similar authors related to these keywords. Here p refers to total published papers of an author and q refers to the specicifc author. The compscore is the score between each paper and author. This is added across all authors.

![alt text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/equation_for_citations.JPG)

If we do not choose to consider citations as a factor that contributes to this ranking we add across all authors without adding weights to this ranked value.

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/without_citations.JPG)

3. The final rank metric uses the previous rc_q rank obtained which was updated based on whether we wanted to consider citations and this ranking criteria adds a weight based on how active a researcher has been in a field in the past 5 years in terms of publishing papers as compared to their whole career. If they publish more papers recently then there will be a higher proportion value.

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/rank_based_on_activity.JPG)

After these criteria we get a final rank value for the authors given a keyword.

Pioneer Metric:
Pioneer: 
- Keyword input : find 10 similar
- Then find similarity score of a paper and keyword
- The earliest year an input keyword is coined is considered
- All papers are obtained within 10 years of that keyword coined
- Only obtain and rank authors that lie in this year range

References
-----------------------------
