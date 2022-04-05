# find-professors-by-keyword
Algorithmic Design
-----------------------------
The goal of this module is to rank researchers given a set of keywords.

Obtain a set of keywords from the user and an input indication of which criteria we want to rank based on. The criteria ranking are based on the years of their publications, based on how active an author is in a field in more recent years and the amount of citations of the author.

1. The idea of ranking based on year of publication accounts for the year the paper was published in. If the paper was published more recently it should be more relevant and it is given a higher keyword similarity score compared to an older paper. This is done by weighting the score betweeen a keyword and paper with a higher weight for more recent years. This is done by using a geometric sequence (with constant as 0.9) formula to reduce the similarity value since the constant is below 1 and the exponent is the different between current year and year of publication.

Here this similarity is represented by s(in) where i is the paper being considered and n is the input keyword being considered. m iterates through 10 similar keywords for a keyword input.

![alt text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/equation_for_year_criteria.JPG)

This will affect the similarity value between papers and keywords so that papers that are too old by a specific author linked to these words will not be given as much importance.

2. The next criteria that is used for ranking is the amount of citations for that particular author. This ranking is based on the idea using a weight that is a result of adding up all citations across all papers of an author and dividing by the largest citations for a single author. This weight will be lowered the lower citations am author has to other similar authors related to these keywords. Here p refers to total published papers of an author and q refers to the specicifc author.

![alt text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/equation_for_citations.JPG)

If we do not choose to consider citations as a factor that contributes to 

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/without_citations.JPG)

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/rank_based_on_activity.JPG)
