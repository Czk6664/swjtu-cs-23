# Direct2D (D2D1) 完全指南

## 一、什么是 Direct2D？

### 1.1 简单理解

**Direct2D 就是微软提供的一个画图工具包**，让你可以在 Windows 窗口上画各种图形。

**类比**：
- 就像你用画笔在纸上画画
- Direct2D 是画笔
- 窗口是纸
- 你写的代码告诉画笔怎么画

### 1.2 为什么用 Direct2D？

**传统 GDI 的问题**：
```cpp
// 传统 GDI（老技术）
HDC hdc = GetDC(hWnd);
MoveToEx(hdc, 0, 0, NULL);
LineTo(hdc, 100, 100);  // 画一条线
ReleaseDC(hWnd, hdc);
```
- ❌ 速度慢（用 CPU 画图）
- ❌ 不支持抗锯齿
- ❌ 不支持透明度

**Direct2D 的优势**：
```cpp
// Direct2D（新技术）
g_pRenderTarget->DrawLine(
    D2D1::Point2F(0, 0),
    D2D1::Point2F(100, 100),
    g_pBrush
);
```
- ✅ 速度快（用 GPU 画图）
- ✅ 自动抗锯齿（线条平滑）
- ✅ 支持透明度和特效

## 二、Direct2D 的核心概念

### 2.1 四大核心对象

Direct2D 就像一个画画工具箱，有4个核心工具：

```
┌─────────────────────────────────────┐
│         Direct2D 工具箱              │
├─────────────────────────────────────┤
│ 1. 工厂 (Factory)                   │
│    作用：生产其他工具                │
│                                     │
│ 2. 画布 (RenderTarget)              │
│    作用：在上面画图                  │
│                                     │
│ 3. 画刷 (Brush)                     │
│    作用：设置颜色                    │
│                                     │
│ 4. 几何图形 (Geometry)              │
│    作用：复杂形状                    │
└─────────────────────────────────────┘
```

### 2.2 详细解释

#### ① 工厂 (ID2D1Factory)

**作用**：创建其他 Direct2D 对象的"工厂"

**类比**：就像一个工厂，可以生产画布、几何图形等

```cpp
// 创建工厂
ID2D1Factory* g_pD2DFactory = nullptr;

D2D1CreateFactory(
    D2D1_FACTORY_TYPE_SINGLE_THREADED,  // 单线程（性能更好）
    &g_pD2DFactory                       // 输出：工厂指针
);
```

**什么时候用**：程序启动时创建一次，一直用到程序结束

---

#### ② 画布 (ID2D1HwndRenderTarget)

**作用**：你在上面画图的"画布"

**类比**：就像一张纸，所有图形都画在上面

```cpp
// 创建画布
ID2D1HwndRenderTarget* g_pRenderTarget = nullptr;

g_pD2DFactory->CreateHwndRenderTarget(
    D2D1::RenderTargetProperties(),           // 渲染属性
    D2D1::HwndRenderTargetProperties(
        hWnd,                                  // 窗口句柄
        D2D1::SizeU(width, height)            // 画布大小
    ),
    &g_pRenderTarget                          // 输出：画布指针
);
```

**什么时候用**：
- 开始画图前：`BeginDraw()`
- 画完后：`EndDraw()`

---

#### ③ 画刷 (ID2D1SolidColorBrush)

**作用**：设置画图的颜色

**类比**：就像画笔的颜色

```cpp
// 创建画刷
ID2D1SolidColorBrush* g_pBrush = nullptr;

g_pRenderTarget->CreateSolidColorBrush(
    D2D1::ColorF(D2D1::ColorF::Black),  // 黑色
    &g_pBrush                            // 输出：画刷指针
);

// 随时改变颜色
g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Red));  // 改成红色
```

**什么时候用**：每次画图前设置颜色

---

#### ④ 几何图形 (ID2D1PathGeometry)

**作用**：创建复杂的形状（如多边形、曲线）

**类比**：就像用模板画复杂图案

```cpp
// 创建路径几何
ID2D1PathGeometry* pPath = nullptr;
g_pD2DFactory->CreatePathGeometry(&pPath);

ID2D1GeometrySink* pSink = nullptr;
pPath->Open(&pSink);

// 定义形状
pSink->BeginFigure(startPoint, D2D1_FIGURE_BEGIN_HOLLOW);
pSink->AddLine(point1);
pSink->AddLine(point2);
pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
pSink->Close();

// 绘制
g_pRenderTarget->DrawGeometry(pPath, g_pBrush);

// 释放
pSink->Release();
pPath->Release();
```

## 三、Direct2D 绘图流程

### 3.1 完整流程图

```
程序启动
    ↓
创建工厂 (D2D1CreateFactory)
    ↓
创建画布 (CreateHwndRenderTarget)
    ↓
创建画刷 (CreateSolidColorBrush)
    ↓
═══════════════════════════════════
    ↓
收到 WM_PAINT 消息
    ↓
BeginDraw() ← 开始画图
    ↓
Clear() ← 清空背景
    ↓
DrawLine() / DrawEllipse() / ... ← 画各种图形
    ↓
EndDraw() ← 结束画图
    ↓
═══════════════════════════════════
    ↓
程序退出
    ↓
释放资源 (Release)
```

### 3.2 代码示例

```cpp
// ========== 第1步：程序启动时初始化 ==========
int APIENTRY wWinMain(...)
{
    // 1. 初始化 COM（必须！）
    CoInitialize(nullptr);
    
    // 2. 创建工厂
    D2D1CreateFactory(
        D2D1_FACTORY_TYPE_SINGLE_THREADED,
        &g_pD2DFactory
    );
    
    // ... 创建窗口等 ...
    
    // 消息循环
    while (GetMessage(&msg, nullptr, 0, 0)) {
        DispatchMessage(&msg);
    }
    
    // 清理
    if (g_pD2DFactory) g_pD2DFactory->Release();
    CoUninitialize();
}

// ========== 第2步：第一次绘制时创建资源 ==========
HRESULT CreateDeviceResources(HWND hWnd)
{
    if (g_pRenderTarget) return S_OK;  // 已创建，直接返回
    
    // 1. 获取窗口大小
    RECT rc;
    GetClientRect(hWnd, &rc);
    
    // 2. 创建画布
    HRESULT hr = g_pD2DFactory->CreateHwndRenderTarget(
        D2D1::RenderTargetProperties(),
        D2D1::HwndRenderTargetProperties(
            hWnd,
            D2D1::SizeU(rc.right, rc.bottom)
        ),
        &g_pRenderTarget
    );
    
    // 3. 创建画刷
    if (SUCCEEDED(hr)) {
        hr = g_pRenderTarget->CreateSolidColorBrush(
            D2D1::ColorF(D2D1::ColorF::Black),
            &g_pBrush
        );
    }
    
    return hr;
}

// ========== 第3步：每次绘制 ==========
void OnPaint(HWND hWnd)
{
    PAINTSTRUCT ps;
    BeginPaint(hWnd, &ps);
    
    // 创建资源（如果还没创建）
    CreateDeviceResources(hWnd);
    
    if (g_pRenderTarget) {
        // 1. 开始画图
        g_pRenderTarget->BeginDraw();
        
        // 2. 清空背景（白色）
        g_pRenderTarget->Clear(D2D1::ColorF(D2D1::ColorF::White));
        
        // 3. 画一条黑色直线
        g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Black));
        g_pRenderTarget->DrawLine(
            D2D1::Point2F(0, 0),      // 起点
            D2D1::Point2F(100, 100),  // 终点
            g_pBrush,                 // 画刷
            2.0f                      // 线宽
        );
        
        // 4. 画一个红色圆形
        g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Red));
        D2D1_ELLIPSE ellipse = D2D1::Ellipse(
            D2D1::Point2F(200, 200),  // 圆心
            50,                        // X半径
            50                         // Y半径
        );
        g_pRenderTarget->DrawEllipse(ellipse, g_pBrush, 2.0f);
        
        // 5. 结束画图
        HRESULT hr = g_pRenderTarget->EndDraw();
        
        // 6. 检查设备丢失
        if (hr == D2DERR_RECREATE_TARGET) {
            // 设备丢失，需要重建
            g_pBrush->Release();
            g_pRenderTarget->Release();
            g_pBrush = nullptr;
            g_pRenderTarget = nullptr;
        }
    }
    
    EndPaint(hWnd, &ps);
}
```

## 四、常用绘图函数详解

### 4.1 画直线 (DrawLine)

```cpp
g_pRenderTarget->DrawLine(
    D2D1::Point2F(x1, y1),  // 起点坐标
    D2D1::Point2F(x2, y2),  // 终点坐标
    g_pBrush,                // 画刷（颜色）
    2.0f                     // 线宽（像素）
);
```

**示例**：
```cpp
// 画一条从 (0,0) 到 (100,100) 的红色直线
g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Red));
g_pRenderTarget->DrawLine(
    D2D1::Point2F(0, 0),
    D2D1::Point2F(100, 100),
    g_pBrush,
    2.0f
);
```

### 4.2 画圆/椭圆 (DrawEllipse)

```cpp
// 定义椭圆
D2D1_ELLIPSE ellipse = D2D1::Ellipse(
    D2D1::Point2F(cx, cy),  // 圆心坐标
    radiusX,                 // X方向半径
    radiusY                  // Y方向半径
);

// 绘制
g_pRenderTarget->DrawEllipse(ellipse, g_pBrush, 2.0f);
```

**示例**：
```cpp
// 画一个圆心在 (100,100)，半径为 50 的圆
D2D1_ELLIPSE circle = D2D1::Ellipse(
    D2D1::Point2F(100, 100),
    50,  // X半径
    50   // Y半径（相等就是圆）
);
g_pRenderTarget->DrawEllipse(circle, g_pBrush, 2.0f);
```

### 4.3 画矩形 (DrawRectangle)

```cpp
// 定义矩形
D2D1_RECT_F rect = D2D1::RectF(
    left,    // 左边界
    top,     // 上边界
    right,   // 右边界
    bottom   // 下边界
);

// 绘制
g_pRenderTarget->DrawRectangle(rect, g_pBrush, 2.0f);
```

**示例**：
```cpp
// 画一个左上角 (50,50)，右下角 (150,150) 的矩形
D2D1_RECT_F rect = D2D1::RectF(50, 50, 150, 150);
g_pRenderTarget->DrawRectangle(rect, g_pBrush, 2.0f);
```

### 4.4 画文字 (DrawText)

```cpp
// 需要先创建文字格式
IDWriteTextFormat* pTextFormat = nullptr;
g_pDWriteFactory->CreateTextFormat(
    L"Arial",                      // 字体名称
    nullptr,                       // 字体集合
    DWRITE_FONT_WEIGHT_NORMAL,     // 字重
    DWRITE_FONT_STYLE_NORMAL,      // 样式
    DWRITE_FONT_STRETCH_NORMAL,    // 拉伸
    24.0f,                         // 字号
    L"zh-cn",                      // 区域
    &pTextFormat
);

// 绘制文字
D2D1_RECT_F textRect = D2D1::RectF(10, 10, 300, 100);
g_pRenderTarget->DrawText(
    L"Hello Direct2D!",  // 文字内容
    16,                   // 文字长度
    pTextFormat,          // 文字格式
    textRect,             // 文字区域
    g_pBrush              // 画刷（颜色）
);
```

## 五、复杂图形：路径几何 (PathGeometry)

### 5.1 什么时候用路径几何？

**简单图形**：用 DrawLine、DrawEllipse 等
**复杂图形**：用 PathGeometry（多边形、曲线等）

### 5.2 画三角形示例

```cpp
// 1. 创建路径
ID2D1PathGeometry* pPath = nullptr;
g_pD2DFactory->CreatePathGeometry(&pPath);

// 2. 打开路径
ID2D1GeometrySink* pSink = nullptr;
pPath->Open(&pSink);

// 3. 定义三角形的三个顶点
D2D1_POINT_2F p1 = D2D1::Point2F(100, 50);   // 顶点1
D2D1_POINT_2F p2 = D2D1::Point2F(50, 150);   // 顶点2
D2D1_POINT_2F p3 = D2D1::Point2F(150, 150);  // 顶点3

// 4. 开始图形（从顶点1开始）
pSink->BeginFigure(p1, D2D1_FIGURE_BEGIN_HOLLOW);

// 5. 添加线段
pSink->AddLine(p2);  // 从p1到p2
pSink->AddLine(p3);  // 从p2到p3

// 6. 结束图形（自动连回p1，形成闭合）
pSink->EndFigure(D2D1_FIGURE_END_CLOSED);

// 7. 关闭路径
pSink->Close();

// 8. 绘制
g_pRenderTarget->DrawGeometry(pPath, g_pBrush, 2.0f);

// 9. 释放资源
pSink->Release();
pPath->Release();
```

### 5.3 画贝塞尔曲线

```cpp
// 创建路径
ID2D1PathGeometry* pPath = nullptr;
g_pD2DFactory->CreatePathGeometry(&pPath);

ID2D1GeometrySink* pSink = nullptr;
pPath->Open(&pSink);

// 起点
D2D1_POINT_2F start = D2D1::Point2F(50, 100);
pSink->BeginFigure(start, D2D1_FIGURE_BEGIN_HOLLOW);

// 二次贝塞尔曲线
D2D1_QUADRATIC_BEZIER_SEGMENT bezier;
bezier.point1 = D2D1::Point2F(150, 50);   // 控制点
bezier.point2 = D2D1::Point2F(250, 100);  // 终点
pSink->AddQuadraticBezier(bezier);

pSink->EndFigure(D2D1_FIGURE_END_OPEN);
pSink->Close();

// 绘制
g_pRenderTarget->DrawGeometry(pPath, g_pBrush, 2.0f);

// 释放
pSink->Release();
pPath->Release();
```

## 六、虚线样式 (StrokeStyle)

### 6.1 创建虚线

```cpp
// 1. 定义虚线模式
float dashes[] = { 5.0f, 2.0f };  // 5像素实线，2像素空白

// 2. 创建虚线样式
ID2D1StrokeStyle* pStrokeStyle = nullptr;
g_pD2DFactory->CreateStrokeStyle(
    D2D1::StrokeStyleProperties(
        D2D1_CAP_STYLE_FLAT,        // 线帽样式
        D2D1_CAP_STYLE_FLAT,
        D2D1_CAP_STYLE_FLAT,
        D2D1_LINE_JOIN_MITER,       // 线连接样式
        10.0f,
        D2D1_DASH_STYLE_CUSTOM,     // 自定义虚线
        0.0f
    ),
    dashes,                          // 虚线模式数组
    2,                               // 数组长度
    &pStrokeStyle
);

// 3. 使用虚线绘制
g_pRenderTarget->DrawLine(
    D2D1::Point2F(0, 0),
    D2D1::Point2F(100, 100),
    g_pBrush,
    2.0f,
    pStrokeStyle  // 传入虚线样式
);

// 4. 释放
pStrokeStyle->Release();
```

## 七、实战：本项目中的 Direct2D 使用

### 7.1 项目中的绘图流程

```cpp
void OnPaint(HWND hWnd)
{
    PAINTSTRUCT ps;
    BeginPaint(hWnd, &ps);
    
    CreateDeviceResources(hWnd);
    
    if (g_pRenderTarget) {
        // 开始绘制
        g_pRenderTarget->BeginDraw();
        
        // 清空背景
        g_pRenderTarget->Clear(D2D1::ColorF(D2D1::ColorF::White));
        
        // 绘制所有已完成的图形
        for (auto& shape : g_shapes) {
            shape->Draw(g_pRenderTarget, g_pBrush);  // 多态调用
        }
        
        // 绘制正在创建的图形
        if (g_currentShape) {
            g_currentShape->Draw(g_pRenderTarget, g_pBrush);
        }
        
        // 绘制状态文本
        if (!g_statusText.empty() && g_pTextFormat) {
            g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Blue));
            D2D1_RECT_F textRect = D2D1::RectF(10, 10, 800, 50);
            g_pRenderTarget->DrawText(
                g_statusText.c_str(),
                g_statusText.length(),
                g_pTextFormat,
                textRect,
                g_pBrush
            );
        }
        
        // 结束绘制
        HRESULT hr = g_pRenderTarget->EndDraw();
        
        // 检查设备丢失
        if (hr == D2DERR_RECREATE_TARGET) {
            DiscardDeviceResources();
        }
    }
    
    EndPaint(hWnd, &ps);
}
```

### 7.2 Line 类的 Draw 实现

```cpp
void Line::Draw(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush)
{
    // 1. 设置颜色（选中时红色，否则用图形自己的颜色）
    pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
    
    // 2. 如果选中，画虚线
    if (selected) {
        DrawDashed(pRT, pBrush, [&](ID2D1StrokeStyle* style) {
            pRT->DrawLine(start, end, pBrush, 2.0f, style);
        });
    }
    // 3. 否则画实线
    else {
        pRT->DrawLine(start, end, pBrush, 1.0f);
    }
}
```

### 7.3 Circle 类的 Draw 实现

```cpp
void Circle::Draw(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush)
{
    // 1. 设置颜色
    pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
    
    // 2. 定义椭圆（圆是特殊的椭圆）
    D2D1_ELLIPSE ellipse = D2D1::Ellipse(center, radius, radius);
    
    // 3. 绘制
    if (selected) {
        DrawDashed(pRT, pBrush, [&](ID2D1StrokeStyle* style) {
            pRT->DrawEllipse(ellipse, pBrush, 2.0f, style);
        });
    } else {
        pRT->DrawEllipse(ellipse, pBrush, 1.0f);
    }
}
```

## 八、常见问题解答

### Q1: BeginDraw 和 EndDraw 必须配对吗？

**A**: 是的！必须配对使用。

```cpp
// 正确
g_pRenderTarget->BeginDraw();
// ... 绘制代码 ...
g_pRenderTarget->EndDraw();

// 错误：忘记 EndDraw
g_pRenderTarget->BeginDraw();
// ... 绘制代码 ...
// 忘记调用 EndDraw() ← 错误！
```

### Q2: 为什么要检查 D2DERR_RECREATE_TARGET？

**A**: 设备可能丢失（如切换显示器、远程桌面等），需要重建资源。

```cpp
HRESULT hr = g_pRenderTarget->EndDraw();
if (hr == D2DERR_RECREATE_TARGET) {
    // 设备丢失，释放并重建
    DiscardDeviceResources();
}
```

### Q3: 什么是 COM？为什么要 CoInitialize？

**A**: COM 是微软的组件对象模型，Direct2D 基于 COM。

```cpp
// 程序启动时
CoInitialize(nullptr);  // 初始化 COM

// ... 使用 Direct2D ...

// 程序退出时
CoUninitialize();  // 清理 COM
```

### Q4: Release() 是什么？

**A**: 释放 COM 对象的内存。

```cpp
// 创建对象
ID2D1SolidColorBrush* pBrush = nullptr;
g_pRenderTarget->CreateSolidColorBrush(..., &pBrush);

// 使用对象
pBrush->SetColor(...);

// 不用了，释放内存
pBrush->Release();
pBrush = nullptr;  // 避免野指针
```

### Q5: 为什么画出来的图形有锯齿？

**A**: Direct2D 默认开启抗锯齿，如果有锯齿可能是：
- 线宽太细（建议至少 1.0f）
- 坐标不是整数（会导致模糊）

```cpp
// 好：整数坐标
g_pRenderTarget->DrawLine(
    D2D1::Point2F(100.0f, 100.0f),
    D2D1::Point2F(200.0f, 200.0f),
    g_pBrush,
    2.0f  // 线宽至少 1.0f
);

// 不好：非整数坐标
g_pRenderTarget->DrawLine(
    D2D1::Point2F(100.5f, 100.5f),  // 可能模糊
    D2D1::Point2F(200.5f, 200.5f),
    g_pBrush,
    0.5f  // 线宽太细
);
```

## 九、快速参考

### 初始化流程
```cpp
CoInitialize(nullptr);
D2D1CreateFactory(..., &g_pD2DFactory);
g_pD2DFactory->CreateHwndRenderTarget(..., &g_pRenderTarget);
g_pRenderTarget->CreateSolidColorBrush(..., &g_pBrush);
```

### 绘制流程
```cpp
g_pRenderTarget->BeginDraw();
g_pRenderTarget->Clear(D2D1::ColorF(D2D1::ColorF::White));
// ... 绘制代码 ...
g_pRenderTarget->EndDraw();
```

### 常用绘图函数
```cpp
DrawLine(start, end, brush, width);
DrawEllipse(ellipse, brush, width);
DrawRectangle(rect, brush, width);
DrawGeometry(geometry, brush, width);
DrawText(text, length, format, rect, brush);
```

### 清理流程
```cpp
if (g_pBrush) g_pBrush->Release();
if (g_pRenderTarget) g_pRenderTarget->Release();
if (g_pD2DFactory) g_pD2DFactory->Release();
CoUninitialize();
```

---

**现在你应该理解 Direct2D 了！** 🎉

**记住核心**：
1. 工厂创建对象
2. BeginDraw 开始画图
3. 用各种 Draw 函数画图
4. EndDraw 结束画图
5. Release 释放资源
