import re
import os

LATEX_PREAMBLE = r"""\documentclass[12pt,a4paper,openany]{ctexbook}
% 基础宏包
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{multirow}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{hyperref}
\usepackage{fancyhdr}
\usepackage{tikz}
\usetikzlibrary{shapes,arrows,positioning,calc,decorations.pathreplacing}
% 页面设置
\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm,headheight=15pt}
% 减少章节前后空白
\usepackage{titlesec}
\titlespacing*{\chapter}{0pt}{-20pt}{20pt}
\titlespacing*{\section}{0pt}{10pt}{5pt}
\titlespacing*{\subsection}{0pt}{8pt}{4pt}
% 超链接设置
\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}
% 代码样式
\lstset{basicstyle=\ttfamily\small,breaklines=true,frame=single,backgroundcolor=\color{gray!10}}
% 页眉页脚
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\leftmark}
\fancyhead[R]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
% 定义颜色盒子
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable}
\newtcolorbox{notebox}{colback=blue!5,colframe=blue!75!black,title=注意,fonttitle=\bfseries,breakable}
\newtcolorbox{tipbox}{colback=green!5,colframe=green!75!black,title=提示,fonttitle=\bfseries,breakable}
\newtcolorbox{formulabox}{colback=yellow!5,colframe=orange!75!black,title=公式,fonttitle=\bfseries,breakable}
\newtcolorbox{examplebox}[1][]{colback=gray!5,colframe=gray!75!black,title=#1,fonttitle=\bfseries,breakable}

\begin{document}
"""

def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update Chapter Title
    content = content.replace('\\chapter{填空题500题}', '\\chapter{计算机网络填空题知识清单}')

    # 2. Extract all sections
    sections = re.split(r'(\\section\{.*?\})', content)
    
    new_content = [LATEX_PREAMBLE]
    if sections[0].strip():
        new_content.append(sections[0].strip() + "\n\n")
    
    for i in range(1, len(sections), 2):
        header = sections[i]
        body = sections[i+1] if i+1 < len(sections) else ""
        
        # Parse answers
        ans_dict = {}
        ans_match = re.search(r'\\textbf\{答案\d+-\d+\}：(.*?)(\n\n|\Z)', body, re.DOTALL)
        if ans_match:
            ans_str = ans_match.group(1).strip()
            ans_markers = list(re.finditer(r'(?:^|\s)(\d+)\.', ans_str))
            for idx, m in enumerate(ans_markers):
                q_num = m.group(1)
                start_ans = m.end()
                if start_ans < len(ans_str) and ans_str[start_ans] == ' ':
                    start_ans += 1
                end_ans = ans_markers[idx+1].start() if idx + 1 < len(ans_markers) else len(ans_str)
                text = ans_str[start_ans:end_ans].strip()
                ans_dict[q_num] = [s.strip() for s in text.split('、') if s.strip()]

        # Process questions
        q_markers = list(re.finditer(r'(?m)^(\d+)\.\s+', body))
        last_pos = 0
        processed_body = []
        
        for idx, m in enumerate(q_markers):
            processed_body.append(body[last_pos:m.start()])
            q_num = m.group(1)
            ans_start_in_body = body.find('\\textbf{答案', m.end())
            if ans_start_in_body == -1: ans_start_in_body = len(body)
            next_q_start = q_markers[idx+1].start() if idx + 1 < len(q_markers) else ans_start_in_body
            limit = min(next_q_start, ans_start_in_body)
            q_content = body[m.end():limit]
            
            if q_num in ans_dict:
                answers = ans_dict[q_num]
                state = {'i': 0}
                def sub_func(match):
                    if state['i'] < len(answers):
                        res = r'\textbf{' + answers[state['i']] + '}'
                        state['i'] += 1
                        return res
                    return match.group(0)
                new_q_content = re.sub(r'\\underline\{\\hspace\{.*?\}\}', sub_func, q_content)
                processed_body.append(f"{q_num}. {new_q_content}")
            else:
                processed_body.append(body[m.start():limit])
            last_pos = limit

        new_content.append(header + "\n\n" + "".join(processed_body).strip() + "\n\n")

    new_content.append("\n\\end{document}\n")
    final_tex = "".join(new_content)
    final_tex = re.sub(r'\n{3,}', '\n\n', final_tex)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_tex)

if __name__ == "__main__":
    process_file(r'd:\study\计算机网络\chapters\ch8_exam.tex', r'd:\study\计算机网络\chapters\ch8_knowledge_list.tex')
    print("Done")
