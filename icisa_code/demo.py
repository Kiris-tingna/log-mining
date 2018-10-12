import time
import re
import os
import gc
import collections
import numpy as np
import sys

from cal_func import *

class Para:
    def __init__(self, rex, path,savePath,saveFileName,
                 saveTempFileName,data,writebuffer=True,epsilon=-1):

        self.path = path
        self.savePath = savePath
        self.saveFileName = saveFileName
        self.saveTempFileName = saveTempFileName
        self.threshold = epsilon
        self.data = data
        self.writebuffer = writebuffer

        if rex is None:
            rex = []
        self.rex = rex


class Node(object):
    def __init__(self,templates):
        self.templates = templates
        self.star_cnt = 0
        self.listID = []

class Demo:
    def __init__(self, para):
        self.para = para

    def mainProcess(self):
        if self.para.threshold == -1:
            self.t1 = time.time()
            thresholds = []
            for x in [0.1,0.2,0.3,0.4,0.5,0.6, 0.7, 0.8,0.9]:
                threshold = x
                self.online(threshold)
                dict_line, map_dict = self.hier_step1()

                ave_threshold = []
                for a in dict_line.keys():
                    #tmp_threshold = []
                    for line in  map_dict[dict_line[a]]:
                        ave_threshold+= [1-float(line.templates.count('*'))/len(line.templates)]
                    #ave_threshold +=[np.mean(tmp_threshold)]
                mean_threshold = np.mean(ave_threshold)
                length =  len(dict_line.keys())
                sum_ = 0
                for i in range(len(dict_line.keys())):
                    tmp = 1
                    for j in range(len(dict_line.keys())):
                        if i!=j:
                            ix = dict_line.keys()[i]
                            iy = dict_line.keys()[j]
                            tmp = min(tmp,1-len(set(ix) & set(iy))*1.0/len(set(ix) | set(iy)))
                    sum_ +=tmp

                self.var = (mean_threshold)*(sum_/length)**2
                print (mean_threshold,sum_/length,self.var)
                thresholds.append((self.var,threshold))

            maxVal = -1
            para = -1
            for item in thresholds:
                print item
                if item[0]>maxVal:
                    para = item[1]
                    maxVal = item[0]
                elif item[0]==maxVal and item[1]>para:
                    para = item[1]
            print ('The best threshold is:')
            print (para)
            self.para.threshold = para#sorted(thresholds,key=lambda x:x[0],reverse=True)[0][1]

        t1 = time.time()
        self.online(self.para.threshold)
        t2 = time.time()

        if self.para.writebuffer:
            if not os.path.exists(self.para.path+self.para.savePath):
                os.makedirs(self.para.path+self.para.savePath)
            else:
                self.deleteAllFiles(self.para.path+self.para.savePath)

            self.outputResult()
            gc.collect()

        return t2-t1

    def online(self,threshold):
        self.dict_ = collections.defaultdict(list)
        self.templates_dict = collections.defaultdict(list)

        for line in self.para.data:
            logID = int(line.split('\t')[0])
            cookedLine = line.split('\t')[1]
            cookedLine = re.sub('[0-9]+','',cookedLine).split()
            #cookedLine = line.split('\t')[1].split()

            size = len(cookedLine)
            if size:

                search_state = False
                for templatesNode in self.templates_dict[size]:
                    flag, newtemplate = self.quickmatch(templatesNode, cookedLine,threshold)
                    if flag:
                        templatesNode.templates = newtemplate
                        templatesNode.star_cnt = newtemplate.count('*')
                        templatesNode.listID.append(logID)
                        search_state = True
                        break

                if not search_state:
                    newtemplateNode = Node(cookedLine)
                    newtemplateNode.listID.append(logID)
                    self.templates_dict[size].append(newtemplateNode)
                self.dict_[size].append(' '.join(cookedLine))


    def quickmatch(self,templateNode,cookedLine,threshold):
        '''
        matchNumber, ret = jaccard_distance(templateNode.templates, cookedLine)
        if (matchNumber-ret.count('*'))*1.0/len(cookedLine)>=threshold :#and templateNode.star_cnt<=0.8*len(cookedLine): #or matchNumber<=2:
            return True,ret
        else:
            return False,[]
        '''
        ret = edit_distance(templateNode.templates, cookedLine)
        if 1-float(ret.count('*'))/len(cookedLine)>=threshold:
            return True,ret
        else:
            return False,[]


    # hierarchical Clust Step1: translate initial template to term pairs
    def hier_step1(self):

        map_dict = {}
        for key in self.templates_dict.keys():
            for templatesNode in self.templates_dict[key]:
                #base_template = [tokens if not checkdigits(tokens) else '[digit]' for tokens in templatesNode.templates]
                #base_template = ' '.join(base_template)
                base_template = ' '.join(templatesNode.templates)
                #line = re.sub('\[digit\]','',base_template)
                line = base_template
                line = re.sub('\*','',line).split()
                line = [x.lower() for x in line]
                if len(line):
                    dict_key = {}
                    for i in range(len(line)):
                        if line[i] not in dict_key:
                            dict_key.setdefault(line[i], 0)
                        else:
                            dict_key[line[i]] += 1
                            line[i] = line[i] + '__' + str(dict_key[line[i]])
                    map_dict.setdefault(' '.join(line),[])
                    map_dict[' '.join(line)].append(templatesNode)
        dict_line = {}
        content = map_dict.keys()
        for line in content:
            line = line.split()
            temp = []
            if len(line) > 1:
                for i in range(len(line)):
                    for j in range(i + 1, len(line)):
                        temp.append((line[i], line[j]))
            elif len(line)==1:
                temp.append(line[0])
            dict_line.setdefault(tuple(temp), ' '.join(line))
        return dict_line,map_dict

    def deleteAllFiles(self, dirPath):
        fileList = os.listdir(dirPath)
        for fileName in fileList:
            os.remove(dirPath + "/" + fileName)

    def outputResult(self):
        remove_para = ['__digit__']
        for rex in self.para.rex:
            if not isinstance(rex,str):
                remove_para.append(rex[1])

        loglist = [0]*(len(self.para.data)+1)
        writeTemplate = open(self.para.path + self.para.saveTempFileName,'w')
        templatesdict = collections.defaultdict(list)
        for key in self.templates_dict.keys():
            for templatesNode in self.templates_dict[key]:
                templates = re.sub('\*','',' '.join(templatesNode.templates))#.split()
                for rex in remove_para:
                    templates = re.sub(rex,' ',templates)
                templates = ' '.join(templates.split())
                templatesdict[templates]+=templatesNode.listID

        idx = 1
        for key in templatesdict.keys():
            writeTemplate.write(str(idx)+'\t'+str(len(templatesdict[key]))+' '+key+ '\n')
            writeID = open(self.para.path+self.para.savePath + self.para.saveFileName + str(idx) + '.txt', 'w')
            for logID in sorted(templatesdict[key]):
                writeID.write(str(logID) + '\n')
                loglist[logID] = idx
            writeID.close()
            idx +=1
        writeTemplate.close()

        writeloglist = open(self.para.path + 'list.txt','w')
        for i in range(1,len(loglist)):
            writeloglist.write(str(i)+'\t'+str(loglist[i])+'\n')
        writeloglist.close()