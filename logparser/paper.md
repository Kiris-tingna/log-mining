## BSGI: A Practical Study for Online Log Parsing with Position Entropy

authors:  ...

(abstract) .. 





### Introduction

A. background

data sample

[引用插入]



B. Motivation



C. Originations



### Problem Description

A brief formulation give insights to how system logs are organized. Denote $L=\{l_1, l_2, \dots, l_n\}$ be instance records for log messages generated from real word system. Each log $l_i=(t_i, c_i, v_i, m_i)$ is a quadruplet consist of a time-stamp  $t_i$, at least one component (service) information $c_i$ which indicate where it come from (generated),  one level tag $v_i $ and log context  $m_i$ with textual information respectively. Values of $v_i$ make up  tag set $V = \{warn, info, trace, error, \dots\}$ . Unstructured logs $L$ can be mapped into event space $E=\{e_1, e_2, \dots, e_r\}$ where each event $e_j$ represent a cluster of similar records. A contextual signature, called template, belong to each event  $e_j$. Given an event id to distinguish different events in $E$, log parsers aim to find the right mapping $ P:\{ L\}_1^n \rightarrow \{E\}_1^r$ efficiently. 

A rough estimate of time consume for $P$. Pairwise comparison costs $O(n^2)$ of picking two instance from $L$ . Suppose the average length of log $l_i$ is $\bar{l} = \sum_{i=1}^n len(l_i)$. Thus finding event template based on longest common substring search ($LCS$) cost $O(\bar l^2)$,  which is done during comparison phase. Time complexity of $P$ can be up to $O(n^2 \bar l^2)$ in which case $P$ lose efficacy on millions of logs in $L$. Obviously, efficient of $P$ is central to evaluation and improvement.



### METHODOLOGY

In this section, we introduce the proposed method  basic signature generation based on gini split (BSGI). As illustrated in Fig xx, BSGI organizes a multi-layer search tree for fast match related logs and maintains special designed threshold  every time incoming log . Automatic split and merge strategy provide a flexible way to generate event templates with high quality. 

`Fig : BSGI design overview`

#### Search phase

The search phase here regard searching similar instance as matching right path on a search tree. There are many researches have proved that tree-based structure behave more efficiently for well formed logs [引用插入 Spell].  图xx将搜索树的结构完整的表述 . Give an overview of BSGI by illustrated in Figure xxx. Firstly, BSGI processes collected logs with domain knowledge and partitions them into different buckets according their length. Secondly, according the key words in log head or tail, it further assign logs into corresponding keyword layer. Finally, it compare all the templates in the leaf layer to generate the appropriate template.

*I. Preprocess*

It is necessary to do some cleaning and summary on $L$ before mining templates. Sometimes, parameters in $m_i $ are recorded as a long json, en or numeric string.  For example, system version (e.g. `v1.0.1`), component name, ip address (e.g. ipv4: `10.63.45.68`, ipv6: `::874B:2B34`) and url strings. However, some resource state representation characters (e.g. `GET POST START STOP RESUME`) are important because events exactly differ in these words.  Parameters in similar logs confuse parser doing combination with operating split.  Using rules such as regular express [引用插入] to filter irrelevant parameters benefit both parsing precision and time efficiency. Moreover, templates can be more consistent with the format of ground truth after normalization.  Table xx has shown our reg expressions for both IAAS[i as a ] and PAAS[] system in following  experiment. Actually, ....

Table. 正则



*II.  Length Layer*

Previous work obtained well-formed templates through log length[引用插入 Drain]. The underlying assumption is that logs form same event usually have fixed length. Similarly, BSGI record length information in the length layer.  However, an event signature can have different size. Sometimes they contain parameters in varying amount,  e.g. In Hadoop log, "delete block blk[]" and "delete block blk [] blk[]" are both delete event. BSGI merges these parameters in different buckets when output final templates to.

As fig xxx show, 解释长度层....



*III. Keyword Layer*

The modern research find that fixed groups of words are trend to appear at the beginning or end of  $ m_i $ when they are actually same event in running system.  For example, developers record message "Send file 01" starts with the filed word "Send". Contrast that with "10 file is send" which ends with the same word "send", implicit relation between them firmly indicate a true system event. Given this, BSGI focuses on the head and the end of $m_i $ in the keyword layer. A keyword should not contain any numbers or special characters, e.g. 10 in "10 file is send" is not keyword.  In table xx, we summaries all special characters such as `+!~*` and example instance in logs to prove they are not keyword. In particular, the keyword maybe empty in case both head and end word are invalid. BSGI takes all of them into consideration. In Figure xxx, a .（举例说明首位字符判断情况）

Table. 特殊字符 通配符 日志举例



Items in keyword layer, called log bucket $b_k$, form a list called signature map.  In figure xxx, structure $ b_k= (T_k, S_k, N_k)$ where  $T_k$ is the template string for $b_k$, $S_k$ is internal record of similarity threshold vary from buckets to buckets. $N_k$ is the number of common tokens in $T_k$ where all samples in $b_k$ share. Each bucket $b_k$ stores historical statics of parsed events in logs. In Spell[引文插入], meta-data information are recorded similarly .



IV. Comparison Layer

Featuring signature of different logs in same event  is essentially longest common subsequence (LCS) problem, which is proved to be a NP hard problem when numbers of sequences are not defined. Therefore, this paper makes some preliminary discussion about LCS reduction in this problem. Technically,  when two instance $l_i$ and $l_j$ ensure formal dissimilarity, there can be designed to avoid LCS comparison since it is unlikely to conclude them as same event. Secondary, as logs in one bucket definitely acquire same length, edit distance is a low-cost alternative. Taking place of LCS summarization in one log bucket, BSGI designs token-wise distance comparisons algorithm (TWDC) as is shown in algorithm xxx. In details, given current summarized template $T_k$ which contains numbers of  common tokens $N_k$ (length of words exclude special chars and number chars in $T_k$) in bucket $b_k$ where $k=1, 2,\dots K$  is subscript of bucket index, and a new incoming log content $l_i$ which is assigned to $b_k$, BSGI calculate new similarity $s_i^k$ and output new template when achieve largest $s_i^k$ among all buckets.  Define $\Delta(m_i, T_k)$ the number of different tokens between $l_i$ and $T_k$, then 
$$
s_i^k = 1-\frac{\Delta(m_i, T_k)}{N_k}\\
N_k^{'} = |m_i| - \Delta(m_i, T_k)
$$

```latex
Algrithom 1. Token-Wise Distance Comparison in BSGI (TWDC)
Input: incoming log $m_i$, bucket $b_k$ 
Output: similarity $s_i^k$, length of common tokens $N_k$
1. $ T_k, S_k, N_k \leftarrow b_k$ 
2. threshold $\leftarrow \ceil (1-s_k) \dot N_k $
3. $diff = 0$, $T_k^{'}=\Phi$
4. for $token$ in $m_i$
5.     compare $c_1$ in $T_k$ and $c_2$ in $l_i$ token-wise	
6.     if $c_1 \neq c_2$
7. 			record different with $diff \leftarrow diff +1$
8. 			if $diff > threshold$
9. 				return -1, -1, Null
10. 		contact $T_k^{'}$ with wildcard $*$
11.     otherwise, contact $T_k^{'}$ with $c_1$
12. $s_i^k \leftarrow 1- diff / N_K$, $N_k^{'} \leftarrow |m_i| - diff$
12.return  $s_i^k$, $N_k^{'}$, and $T_k^{'}$
```

TWDC aims to find most consistent bucket that $l_i$ should be assigned to. BSGI draw lessons from Spell [引用插入] in order to do analytic stream mining. When a new log message $m_i$ arrives, we first find all $b_k$ in signature map which has same length with $m_i$. Then, the new signature $T_k^{'}$ is generated by comparing $m_i$ with all $b_k$. 



#### Adjustment phase

A. Step1:  Create /Update Bucket

A new bucket object will be created in the comparison layer if a suitable $b_k$ can not be found for incoming log $l_i$. 

Three kinds of position exist in signature $T_k$. The first is parameters. Positions in parameters should not be considered during parsing work flow. Usually, parsers will skip them using a wild card $*$.  Next is constant position. Common tokens are shared at these position by all instances in bucket. Last one is invalid position. Generally speaking, words in invalid position should be filtered at first.





where the object's template is the log message. When the appropriate insertion template is found in the log, the template to be inserted into the SigObj object is updated. 



Each field of the template is compared with the corresponding field of the log message one by one. If the same, the field is reserved as a constant field. Otherwise, the tag template field is a variable field and is represented by a parameter (wildcard).



B. Step2:  Bucket Refinement



C. Step3:  Rebuild Template



### BSGI

In this section, we summary proposed approach basic signature generation base on gini split. BSGI ...

```latex
Algrithom: Online Classfication in BSGI
```



### Highlights

#### Incorporate Level Information



#### Early Abandon Strategy



#### Cache mechanism



#### Using Gini Replace Entropy

Gini index





### Fine tuning





### 



