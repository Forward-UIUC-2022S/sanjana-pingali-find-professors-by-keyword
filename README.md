# find-professors-by-keyword
Algorithmic Design
-----------------------------
The goal of this module is to rank researchers given a set of keywords.

1. Obtain a set of keywords from the user and an input indication of which criteria we want to rank based on. The criteria ranking are based on the years of their publications, based on how active an author is in a field in more recent years and the amount of citations of the author.

The idea of ranking based on year of publication accounts for the year the paper was published in. If the paper was published more recently it should be more relevant and it is given a higher keyword similarity score compared to an older paper. This is done by weighting the score betweeen a keyword and paper with a higher weight for more recent years. This is done by using a geometric sequence (with constant as 0.9) formula to reduce the similarity value since the constant is below 1 and the exponent is the different between current year and year of publication.

Here this similarity is represented by s(in) where i is the paper being considered and n is the input keyword being considered. 

![alt text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/equation_for_year_criteria.JPG)

![alt text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/equation_for_citations.JPG)

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/without_citations.JPG)

![alt_text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/images/rank_based_on_activity.JPG)
