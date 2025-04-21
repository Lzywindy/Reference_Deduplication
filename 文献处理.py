"""
# 代码解释
该代码的主要功能是清理指定目录下的临时文件，并对参考文献进行去重、排序和格式化处理，最终生成新的参考文献文件和日志文件。具体逻辑如下：
1. 清理当前目录下以 `.bbl`, `.out`, `.toc`, `.blg`, `.aux` 结尾的临时文件。
2. 解析命令行参数，获取输入路径和输出文件名。
3. 读取并整理参考文献列表，替换部分类型（如将 `@misc` 替换为 `@techreport`）。
4. 对参考文献按标题去重，并生成新的参考文献文件。
5. 如果存在重复的参考文献，生成需要替换的建议日志文件。

# 控制流图
```mermaid
flowchart TD
    A[开始] --> B{清理临时文件}
    B -->|完成| C[解析命令行参数]
    C --> D[读取并整理参考文献]
    D --> E[去重和排序]
    E --> F[生成新的参考文献文件]
    F --> G{是否存在重复文献?}
    G -->|Yes| H[生成替换建议日志]
    G -->|No| I[结束]
    H --> I[结束]
```
"""

import re,os,argparse

DEBUG=False
def process_title(value:str):
    pure=re.sub(r"[ ]+|\t+|\n+"," ",value).replace("{","").replace("}","")
    pure=re.sub(r"[ ]*,[ ]+",", ",re.sub(r"[ ]+|\t+|\n+"," ",pure))
    return (value,pure)
def process_author(value:str):
    values=[n.strip() for n in  re.sub(r"[ ]+and[ \n\t]+"," and ",value).split(" and ") if n.strip()]
    return values
def check_stack_pairs(input_str: str,stack: list):
    ACCEPTABLE={"{","}","\"","(",")","[","]"}
    if input_str not in ACCEPTABLE:
        return False    
    if len(stack) < 1:
        if input_str in {"])}"}:
            return False
        stack.insert(0,input_str)
        return False
    if input_str=='{':
        stack.insert(0,input_str)
        return False
    elif (input_str=='}' and stack[0]=='{'):
        stack.pop(0)
        return True
    elif input_str=='"':
        if stack[0]=='"':
            stack.pop(0)
            return True
        else:
            stack.insert(0,input_str)
            return False
    # elif input_str=='\'':
    #     if stack[0]=='\'':
    #         stack.pop(0)
    #         return True
    #     else:
    #         stack.insert(0,input_str)
    #         return False
    return False
def skip_comment_blank(contents: str,index_cur:int,need_skip:bool=True):
    while  index_cur<len(contents) and contents[index_cur] in {'\n','\t',' '} and need_skip:
        index_cur+=1
    if index_cur>=len(contents):
        return index_cur
    if contents[index_cur] in {'%'}:
        while contents[index_cur] not in {'\n'}:
            index_cur+=1
    return index_cur
def process_line(line_content: str,lines_content: list,lines_content_debug: list):
    if DEBUG:  
        print(line_content)                   
    try:
        key,value= tuple([n.strip() for n in line_content.split("=",1) if n.strip()])
    except:
        print("Error: ",line_content)
        return
    key=key.strip()
    value=value.strip()
    if value.startswith("{") or value.startswith("\""):
        value=value[1:]
    if value.endswith("}") or value.endswith("\""):
        value=value[:-1]
    lines_content_debug.append(line_content)    
    if key=="author" or key=="editor":
        lines_content.append((key,process_author(value))) 
    elif key=="title":
        value,pure_title=process_title(value)
        lines_content.append((key,value))
        lines_content.append(("pure_title",pure_title))                    
    else:
        lines_content.append((key,value))
    pass
def extract_reference_from_string(contents: str,reference_list: list):
    start_index=-1
    content_start_index=-1
    end_index=-1
    stack=[]
    index_cur=0
    max_index=len(contents)
    ref_type=""
    ref_id=""
    ref_content=""
    line_content=""
    lines_content=[]
    lines_content_debug=[]
    while index_cur<max_index:
        if DEBUG:
            # print(len(stack))
            print("当前索引：",index_cur)
        index_cur=skip_comment_blank(contents,index_cur,start_index==-1 and content_start_index==-1 and end_index==-1)
        if index_cur>=max_index:
            break
        if contents[index_cur]=="@" and start_index==-1: # 文献类型开始标志
            start_index=index_cur
            while contents[index_cur]!='{':
                ref_type+=contents[index_cur]
                index_cur+=1
            if DEBUG:
                print(ref_type)
            continue
        elif contents[index_cur]=="{" and content_start_index==-1 and start_index!=-1: # 内容开始标志，文献类型标志结束  
            check_stack_pairs(contents[index_cur],stack)    
            index_cur+=1
            content_start_index=index_cur
            while contents[index_cur]!=',':
                ref_id+=contents[index_cur]
                index_cur+=1
            index_cur+=1
            index_cur=skip_comment_blank(contents,index_cur,True)
            if DEBUG:
                print(ref_id)
            continue
        elif content_start_index==-1 and start_index!=-1: # 文献类型标志未结束，继续读取
            ref_type+=contents[index_cur]
            index_cur+=1
            continue
        else:            
        # elif start_index!=-1 and content_start_index!=-1 and end_index==-1: # 内容开始标志结束，继续读取  
            # index_cur=skip_comment_blank(contents,index_cur,True) 
            cur_char=contents[index_cur]
            if DEBUG:
                print(cur_char)
            # print(cur_char)
            check_stack_pairs(cur_char,stack)
            if DEBUG:
                print("Current Depth: ",len(stack))
                print("Current Stack: ",stack)
            if len(stack)==0:
                end_index=index_cur
                if line_content!="":
                    process_line(line_content,lines_content,lines_content_debug)
                if DEBUG:  
                    # print(line_content)                    
                    print(lines_content)
                if ref_type=="" or ref_id=="":
                    index_cur+=1
                    continue
                # if DEBUG:
                #     reference_list.append((ref_type,ref_id,dict(lines_content),lines_content_debug,ref_content,contents[start_index:end_index]))
                # else:
                    # reference_list.append((ref_type,ref_id,dict(lines_content)))
                re_dict=dict(lines_content)
                reference_list.append((ref_type,ref_id,re_dict))
                if DEBUG:
                    print(reference_list[-1])
                start_index=content_start_index=end_index=-1
                ref_type=""
                line_content=""
                ref_id=""
                ref_content=""
                lines_content=[]
                lines_content_debug=[]
                index_cur+=1
                continue
            if len(stack)==1:   
                if line_content.startswith("abstract") and DEBUG:
                    print(line_content)
                    print("{}/{}".format(index_cur,max_index)) 
                    print("Current Depth: ",len(stack))
                if cur_char==',':  
                    process_line(line_content,lines_content,lines_content_debug)
                    line_content=""
                    # if DEBUG:  
                    #     print(line_content)                   
                    # try:
                    #     key,value= tuple([n.strip() for n in line_content.split("=",1) if n.strip()])
                    # except:
                    #     print("Error: ",line_content)
                    #     return
                    # key=key.strip()
                    # value=value.strip()
                    # if value.startswith("{") or value.startswith("\""):
                    #     value=value[1:]
                    # if value.endswith("}") or value.endswith("\""):
                    #     value=value[:-1]
                    # lines_content_debug.append(line_content)
                    # line_content=""
                    # if key=="author" or key=="editor":
                    #     lines_content.append((key,process_author(value))) 
                    # elif key=="title":
                    #     value,pure_title=process_title(value)
                    #     lines_content.append((key,value))
                    #     lines_content.append(("pure_title",pure_title))                    
                    # else:
                    #     lines_content.append((key,value))
                    # if DEBUG:
                    #     print(lines_content[-1])
                    index_cur+=1
                    index_cur=skip_comment_blank(contents,index_cur,True)
                    # index_cur+=1
                    continue
            line_content+=cur_char
            ref_content+=cur_char
            if index_cur<max_index-1 and cur_char=="\\" and contents[index_cur+1] in {"\"","\'","%","`"}:
                if DEBUG:
                    print(contents[index_cur:index_cur+2])
                index_cur+=1
                line_content+=contents[index_cur]
                ref_content+=contents[index_cur]
            index_cur+=1
    pass
def SortFunction(data):
    if 'year' in data[2].keys():
        return int(re.findall(r'\d{4}',data[2]['year'])[0] )
    if 'journal' in data[2].keys() and data[2]['journal']=="CoRR":
        return -1
    return 0
def rebuild_reference(item:tuple,replace_type_dict:dict[str,str]=None):
    item_0=item[0]
    if replace_type_dict:
        item_0=replace_type_dict.get(item_0,item_0)
    result="{}{{{},\n".format(item_0,item[1])
    for k,v in item[2].items():
        if k=="pure_title":
            continue
        _v=""
        if type(v)==list:
            _v=" and ".join(v)
        else:
            _v=re.sub(r'[\n\t ]+',' ',v) 
        if len(k)<4:
            result+="\t{}\t\t\t=\t{{{}}},\n".format(k,_v)
        elif len(k)<=7:            
            result+="\t{}\t\t=\t{{{}}},\n".format(k,_v)
        else:
            result+="\t{}\t=\t{{{}}},\n".format(k,_v)
    result+="}"
    if DEBUG:
        print(result)
    return result
def 读取并整理格式化文献(目录或者文献文件:str):
    文献列表=[]
    if os.path.isfile(目录或者文献文件):
        with open(目录或者文献文件,'r',encoding='utf-8') as f:
            内容=f.read()
            extract_reference_from_string(内容,文献列表)
            f.close()
    else:
        for 文件 in os.listdir(目录或者文献文件):            
            文件全名=os.path.join(目录或者文献文件,文件)
            if os.path.isdir(文件全名):
                continue
            with open(文件全名,'r',encoding='utf-8') as f:
                内容=f.read()
                extract_reference_from_string(内容,文献列表)
                f.close()
        pass
    return 文献列表

if __name__=="__main__":
    for f in [n for n in os.listdir() if n.endswith('.bbl') or n.endswith('.out') or n.endswith('.toc') or n.endswith('.blg') or n.endswith('.aux') ]:
        os.remove(f)
    parser = argparse.ArgumentParser(description='运行文献处理')
    parser.add_argument('--input_file_or_path', type=str,default='')
    parser.add_argument('--output_file', type=str,default='references.bib')
    
    # parser.add_argument('--ratios', type=int,default=100)
    args = parser.parse_args()
    dirpath=args.input_file_or_path
    output=args.output_file

    reference_list=[]
    # 类型替换(有些不识别"@misc"来源，但很多的"@misc"其实是"@techreport"或者其他说明类的，因此可以替换为techreport)
    replace_type_dict={"@misc": "@techreport"}
    reference_list=读取并整理格式化文献(dirpath)
    reference_map=dict()
    for reference in reference_list:
        try:
            pure_title=reference[2]['pure_title']
        except:
            print(reference)
            break    
        if pure_title not in reference_map.keys():
            reference_map[pure_title]=[reference]
        else:
            reference_map[pure_title].append(reference)
    # 排序，去重
    for key in reference_map.keys():
        if len(reference_map[key])>1:
            reference_map[key].sort(key=lambda x:SortFunction(x),reverse=True)
    # 得到去重后的列表
    reference_map_l=[v[0] for v in reference_map.values()]
    # 生成整理过的参考文献文件 # 如何需要
    current_path= dirpath if os.path.isdir(dirpath) else os.path.dirname(dirpath)
    new_ref_path=os.path.join(current_path,'new_references')
    if not os.path.exists(new_ref_path):
        os.makedirs(new_ref_path)
    count=1
    filecontent=[]
    for index,reference in enumerate(reference_map_l):
        filecontent.append(rebuild_reference(reference,replace_type_dict))    
        if (index+1)%20==0:
            with open(os.path.join(new_ref_path,'parical{}.bib'.format(count)),'w',encoding='utf-8') as f:
                f.write("\n".join(filecontent))
                f.close()
            count+=1
            filecontent=[]
            pass
        pass
    # 整合新的引用
    with open(output,'w',encoding='utf-8') as f:
        f.write("\n".join([rebuild_reference(item,replace_type_dict) for item in reference_map_l]) )
        f.close()
    # 生成需要替换的建议
    redo_map=[(k,v) for k,v in reference_map.items() if len(v)>1]
    if len(redo_map)>0:
        filename_log='references_need_rename.log'
        dirp=os.path.dirname(output)
        if dirp:
            filename_log=os.path.join(dirp,filename_log)
        with open(filename_log,'w',encoding='utf-8') as f:
            for item in redo_map:
                text="引用标题: {}\n".format(item[0])
                bibid_rc=item[1][0][1]
                text+="\t\t建议的bibId:\t{}\n".format(bibid_rc)
                l=len(text)
                for subitem in item[1][1:]:
                    if subitem[1]==bibid_rc:
                        continue
                    text+="\t\t需要替换的bibId:\t{}\n".format(subitem[1])
                if len(text)==l:
                    continue
                f.write(text)
            f.close()
        pass
    pass
    # print("重复的引用：",len(redo_map))
    
# python 文献处理.py --input_file_or_path=prereferences.bib --output_file=references.bib
# python 文献处理.py --input_file_or_path=references_dir --output_file=references.bib