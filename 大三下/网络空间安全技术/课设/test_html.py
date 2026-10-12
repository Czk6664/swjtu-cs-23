from app import app
import db

db.init_db()

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['username'] = 'czk2023'
    
    resp = c.get('/dashboard')
    html = resp.data.decode('utf-8')
    
    # 检查是否有内联CSS
    if '<style>' in html:
        print('[OK] 内联CSS存在')
    else:
        print('[MISSING] 内联CSS缺失')
    
    # 检查关键CSS类
    for cls in ['kv', 'grid', 'table-container', 'card']:
        if f'class="{cls}"' in html:
            print(f'[OK] {cls} 类存在')
        else:
            print(f'[MISSING] {cls} 类缺失')
    
    # 检查CSS样式
    if 'background: var(--apple-gray)' in html:
        print('[OK] Apple Gray 样式存在')
    else:
        print('[MISSING] Apple Gray 样式缺失')
    
    # 输出前2000字符看看
    print('\n=== HTML Preview (first 2000 chars) ===')
    print(html[:2000])