# - * - coding:utf8 - * - -
'''
@ Author : Tinkle G
'''
def checkdigits(s):
    try:
        float(s)
        return True
    except:
        return False


def checkdigits_(s):
    return any(char.isdigit() for char in s)

def jaccard_distance(tem,que):
    cnt = 0
    ret = []
    for idx in range(len(que)):
        if tem[idx] == que[idx] or tem[idx] == '*':
            cnt +=1
            ret.append(tem[idx])
        else:
            ret.append('*')
    return cnt,ret

def edit_distance(tem,que):
    ret = []
    for idx in range(len(que)):
        if tem[idx] == que[idx]:
            ret.append(tem[idx])
        else:
            ret.append('*')
    return ret