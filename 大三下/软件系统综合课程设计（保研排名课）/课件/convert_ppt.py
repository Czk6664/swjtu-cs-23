# -*- coding: utf-8 -*-
import os
import sys
from markitdown import MarkItDown

sys.stdout.reconfigure(encoding='utf-8')

md_converter = MarkItDown()

input_dir = r'D:\大三下\软件系统综合课程设计\课件'
output_dir = os.path.join(input_dir, '课件介绍')
os.makedirs(output_dir, exist_ok=True)

files = [f for f in os.listdir(input_dir) if f.endswith(('.pptx', '.ppt', '.pdf'))]

for idx, filename in enumerate(files, 1):
    filepath = os.path.join(input_dir, filename)
    print(f'\n[{idx}/{len(files)}] 处理: {filename}')
    
    try:
        result = md_converter.convert(filepath)
        content = result.text_content
        
        # 提取文件基本信息
        file_ext = os.path.splitext(filename)[1].lower()
        file_type = 'PPT演示文稿' if file_ext in ('.pptx', '.ppt') else 'PDF文档'
        file_size = os.path.getsize(filepath)
        size_str = f'{file_size/1024:.1f} KB' if file_size < 1024*1024 else f'{file_size/(1024*1024):.1f} MB'
        
        # 从文件名提取章节信息
        name_without_ext = os.path.splitext(filename)[0]
        name_clean = name_without_ext.replace(' - 副本', '').replace(' (1)', '')
        
        # 生成MD文件名
        md_filename = name_without_ext.replace('：', '-').replace('—', '-').replace(' ', '_') + '.md'
        md_filepath = os.path.join(output_dir, md_filename)
        
        # 生成MD内容
        md_content = f"""# {name_clean}

## 基本信息

| 项目 | 内容 |
|------|------|
| 文件名 | {filename} |
| 文件类型 | {file_type} |
| 文件大小 | {size_str} |

---

## 内容概览

{content}

---

*本文件由 markitdown 工具自动转换生成*
"""
        
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f'  ✓ 已生成: {md_filename}')
        
    except Exception as e:
        print(f'  ✗ 处理失败: {str(e)}')

print(f'\n处理完成！输出目录: {output_dir}')
