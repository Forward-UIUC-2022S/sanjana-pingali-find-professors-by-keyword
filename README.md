# find-professors-by-keyword
Algorithmic Design
-----------------------------
The main schemas from the MAG dataset of siginificance to ranking papers by authors are the Authors, Papers and Paper Author Affiliations. 

![alt text](https://github.com/Forward-UIUC-2022S/sanjana-pingali-find-professors-by-keyword/blob/main/Untitled%20drawing%20(9).jpg)

Creating Embeddings
------------------------------
The algorithm will start off by creating embeddings for the Papers using the Papers schema in the MAG database, for the professors using the Authors schema from the MAG database. These embeddings help simplify the amount of data needed to be stored while computing this ranking and store only relevant data. 

Generate match scores for professors and papers
-------------------------------
Then using these embeddings and the Paper Author Affiliations the similarity can be generated between professors and papers.

Find highest ranked papers using embeddings
-------------------------------
Based on the similarity value or match score the professors inputted are compared to generate the ranking of papers based on professors.
