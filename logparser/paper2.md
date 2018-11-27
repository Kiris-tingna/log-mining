#### Adjustment phase

A. Step1:  Create /Update Bucket

A new bucket object will be created in the comparison layer if a suitable $b_k$ can not be found for incoming log $l_i$.  In contrast to updating appropriate buckets when $b_k$ is found , $S_k$ will be initialized with a default value and updating iteratively with the new bucket.  Tokens between the template and logs are compared respectively. TWDC  store constant token in template and get rid of parameter with a wild-card. Generally speaking, three kinds of position in $T_k$ are taken into consideration. The first is parameters. Positions in parameters should not be considered as entity token during work flow. Usually, parsers will skip them using a wild card $*$.  Then is constant position. Common tokens are shared at these position by all instances in bucket. Last is invalid position. Words in invalid position should be filtered at first in preprocessing layer.



##### Tricks 3 : Cache mechanism

As for bucket search, BSGI designed cache pointers for more faster hit of corresponding bucket in search tree.





B. Step2:  Bucket Refinement

Bucket refinement is the essence of BSGI. As a matter of fact, Ignoring local features will eventually lead to different events being considered the same.  However events with different semantics or parameter frequency should be separated. Analysis focus on log structure usually fail to distinguish them. For example, `up` and `down` in message "Network is up" and "Network is down" is the only difference which brings insight into weighted position. Obviously, two logs represent "the network has been connected" and "the network has been disconnected" respectively. Based on exploring structural similarity, they can be considered as the same event. But actually the third word can be more important than first or the second as shown previously.  In order to cut logs semantically  BSGI reserve historical statics using position entropy. 

Specifically, tokens in log message with a position entropy $R_k^j $ at $j$-th position. Denote counter matrix $Q$ record  occurrence of tokens. $Q_{kj}$ is a counter dictionary with word-count pair $W_{kj}: CT_{kj}$ about $k$-th bucket $b_k$ and $j$-th word in $T_k$. $\sum_{j=1}^{J}CT_{kj} = |b_k| = q_{k}$ is the current log amounts in bucket $b_k$.  
$$
R_k^j = 1- \frac{\sum_{j=1}^{J} CT_{kj} ^2}{q_{k}^2}
$$
 Higher $R_k^j$ implies higher possibility that $j$-th word is a parameter. BSGI extracts those key-words in buckets with lower $R_k^j $ finally.  The gini index is considered as  an approximation of entropy. BSGI takes advantage of  simplification of gini calculation and propose cluster refinement based on minimum gini split (CRMSG). 

```latex
Algrithom 2. Cluster Refinement based on Minimum Gini Split(CRMGS)
Input:  Bucket $b_k$, Min log tempalte $M_l$, Max token thresold $M_t$, Max Gini $M_g$   
Output: split position $P_s$ for current bucket
1. split pos $P_s \leftarrow -1 $, split gini $G_s \leftarrow 1$
2. \If {$|b_k| < M_l$}{return $P_s$}
3. $ T_k, S_k, N_k \leftarrow b_k$, $J \leftarrow |T_k|$
4. \For {$j \leftarrow 1$ \KwTo $J$}{
6.     \If {$T_k^j$ is a wildcard and $q_{kj} < M_t$} { 
7. 			get gini entropy $R_k^j $ with Equation above
8. 			\If {$R_k^j < M_g$ and $R_k^j  < G_s$}{
9. 				$ P_s \leftarrow j$
10.				$ G_s \leftarrow R_k^j $
11.			}
12.		}
13.	}
14.return $P_s$
```

CRMSG is limited by following thresholds:
(1) Minimum log template $M_l$: At the beginning of statics, BSGI do not believe enough instances have been gathered. With quiet limited log templates, that is, the parameters information is limited, signature will not be split when $|b_k| < M_l$. 
(2) Maximum token number $M_t$: There is strong possibility that the position is a parameter when a considerable amount of words has been reached here. If there are many kinds of parameters in a certain position, BSGI regard it as a definitely wild-card position for cheaper cost.  
(3) Maximum gini $M_g$: When the entropy $R_k^j$ exceeds the low boundary of all bucket, it can be used as a candidate for splitting position.



##### Tricks 4 : Using Gini

Gini index 



### BSGI highlights

In this section, we summary proposed approach basic signature generation base on gini split. BSGI has a evaluation 



Basic signature generation is similar to clustering of stream data. Unlike other log parsing methods that use implicit event features to guide parameter adjustment, we recommend a similar strategy in clustering validation to adjust the threshold st with only explicit features in our process. The adjustment of the threshold st is of great significance to the analytical accuracy and application performance. In basic event signature generation, threshold st boot algorithm establishes a new SigObj. Most existing log parsing methods first generate real log signatures (templates) based on regular expressions, and then adjust the parameters involved in log parsing methods according to these log templates. However, in fact, such as real events. Types (templates) are either not easy to obtain or cannot guarantee the accuracy of template acquisition.
Clustering verification is to verify that intra-frame similarity is high while inter-cluster similarity is low. Similar to clustering verification, in basic signature generation, we want logs with the same signature to be more similar to those with different signatures (i.e., compactness and separation). Compactness measures the close relationship of logs, and separation measures the degree of log separation of different signatures.
Define 1 signature compactness. Let CTR denote the number of constant fields in event signature r, and LR denote the length of R. Then the compactness of signature R is defined as follows:

Compactness g measures the ratio of constant number segments of signature, and the larger the ratio, the more compact the event signature is.
Just like the distance between clusters, we use the distance between logs with the same signature to measure the distance between clusters.
The degree of separation between classes is mainly to evaluate the degree of looseness between classes. In intuition, the greater the distance between classes, the better the degree of looseness. The distance between texts mainly includes Jaccard distance and cosine distance. Because the format of the log message text is fixed, events represented by the same token location are not necessarily the same. The distance between signatures needs to consider the location information of tokens and the length of event signatures. We use the Token Pairs pair to solve these two problems.
Field pairs can retain the order information of log message fields. Constructing field pairs has two advantages: (1) transformed field pairs retain the sequence information of message terms; (2) discrete item pairs are easier to compute than field sequences.
For example, there is a log template parsed from BGL:
RAS KERNEL INFO generating core [*]
We delete all parameters (wildcards) (marked [*]) and extract each pair of terms and preserve the order of the two terms. The converted pairs of terms are expressed as follows:
(RAS, KERNEL), RAS, INFO, RAS, generating,
(RAS, core), KERNEL (INFO), KERNEL (generating),
(KERNEL, core), INFO (generating), INFO (core), generating (core)
Define 2 signature separation degree. Jaccard distance uses the ratio of two fields to different elements and all elements in a set to measure the degree of distinction between two fields to a set. The Jaccard distance of field pairs is defined as follows:

For each term pair set, we use it and other field pairs to set the minimum Jaccard distance to describe the degree of dispersion between templates. In this log parsing task, we pay more attention to separation rather than compactness. We will score clustering as follows:

In practice, we sample the log data to select the best threshold, which can get the maximum value about scluster.



```latex
Algrithom 3: Online Classfication of BSGI
```



### Fine tuning by visualization







