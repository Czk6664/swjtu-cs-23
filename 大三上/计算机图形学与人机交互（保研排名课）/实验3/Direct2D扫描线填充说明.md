# Direct2D版本扫描线填充法修改线宽

## 概述

完全使用Direct2D实现扫描线填充算法,不使用任何GDI函数。所有绘制操作都通过Direct2D的硬件加速渲染完成。

## 核心实现

### 1. ScanlineFillD2D类

新增的`ScanlineFillD2D.h`文件包含完全基于Direct2D的扫描线填充实现:

```cpp
class ScanlineFillD2D {
public:
    // 使用D2D绘制粗线(扫描线填充法)
    static void DrawThickLine(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                              float x1, float y1, float x2, float y2, 
                              float width, D2D1_COLOR_F color);
    
    // 使用D2D绘制粗圆(扫描线填充法)
    static void DrawThickCircle(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                                float cx, float cy, float radius, 
                                float width, D2D1_COLOR_F color);
    
    // 使用D2D填充多边形
    static void FillPolygon(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                           D2D1_POINT_2F* vertices, int count, D2D1_COLOR_F color);
};
```

## 实现原理

### 直线的扫描线填充 (Direct2D版本)

**算法步骤**:
1. 计算直线的垂直方向向量
2. 根据线宽在两侧偏移,得到4个顶点
3. 使用`ID2D1PathGeometry`创建矩形路径
4. 使用`FillGeometry`填充矩形

**代码实现**:
```cpp
static void DrawThickLine(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                          float x1, float y1, float x2, float y2, 
                          float width, D2D1_COLOR_F color) {
    // 计算垂直方向
    float dx = x2 - x1;
    float dy = y2 - y1;
    float len = sqrt(dx * dx + dy * dy);
    
    float perpX = -dy / len * (width / 2.0f);
    float perpY = dx / len * (width / 2.0f);
    
    // 计算4个顶点
    D2D1_POINT_2F vertices[4];
    vertices[0] = D2D1::Point2F(x1 + perpX, y1 + perpY);
    vertices[1] = D2D1::Point2F(x1 - perpX, y1 - perpY);
    vertices[2] = D2D1::Point2F(x2 - perpX, y2 - perpY);
    vertices[3] = D2D1::Point2F(x2 + perpX, y2 + perpY);
    
    // 使用D2D填充多边形
    FillPolygon(pRT, pBrush, vertices, 4, color);
}
```

**优势**:
- ✅ 硬件加速渲染
- ✅ 抗锯齿效果
- ✅ 高性能
- ✅ 无GDI依赖

### 圆的扫描线填充 (Direct2D版本)

**算法步骤**:
1. 计算外圆半径 = radius + width/2
2. 计算内圆半径 = radius - width/2
3. 使用`ID2D1PathGeometry`创建环形路径
4. 外圆顺时针,内圆逆时针,形成环形
5. 使用`FillGeometry`填充环形

**代码实现**:
```cpp
static void DrawThickCircle(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                            float cx, float cy, float radius, 
                            float width, D2D1_COLOR_F color) {
    float outerRadius = radius + width / 2.0f;
    float innerRadius = radius - width / 2.0f;
    
    // 创建路径几何
    ID2D1Factory* pFactory = nullptr;
    pRT->GetFactory(&pFactory);
    
    ID2D1PathGeometry* pPathGeometry = nullptr;
    pFactory->CreatePathGeometry(&pPathGeometry);
    
    ID2D1GeometrySink* pSink = nullptr;
    pPathGeometry->Open(&pSink);
    
    // 绘制外圆(顺时针)
    pSink->BeginFigure(D2D1::Point2F(cx + outerRadius, cy), D2D1_FIGURE_BEGIN_FILLED);
    D2D1_ARC_SEGMENT arc;
    arc.size = D2D1::SizeF(outerRadius, outerRadius);
    arc.sweepDirection = D2D1_SWEEP_DIRECTION_CLOCKWISE;
    arc.arcSize = D2D1_ARC_SIZE_SMALL;
    
    arc.point = D2D1::Point2F(cx - outerRadius, cy);
    pSink->AddArc(arc);
    arc.point = D2D1::Point2F(cx + outerRadius, cy);
    pSink->AddArc(arc);
    pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
    
    // 绘制内圆(逆时针,形成环形)
    if (innerRadius > 0) {
        pSink->BeginFigure(D2D1::Point2F(cx + innerRadius, cy), D2D1_FIGURE_BEGIN_FILLED);
        arc.size = D2D1::SizeF(innerRadius, innerRadius);
        arc.sweepDirection = D2D1_SWEEP_DIRECTION_COUNTER_CLOCKWISE;
        
        arc.point = D2D1::Point2F(cx - innerRadius, cy);
        pSink->AddArc(arc);
        arc.point = D2D1::Point2F(cx + innerRadius, cy);
        pSink->AddArc(arc);
        pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
    }
    
    pSink->Close();
    
    // 填充环形
    pBrush->SetColor(color);
    pRT->FillGeometry(pPathGeometry, pBrush);
    
    // 清理资源
    pSink->Release();
    pPathGeometry->Release();
    pFactory->Release();
}
```

**优势**:
- ✅ 完美的圆形(使用弧线而非像素)
- ✅ 抗锯齿
- ✅ 硬件加速
- ✅ 支持任意线宽

## 使用方法

### Line类使用扫描线填充

```cpp
// 在Line类中
void DrawWithScanlineFill(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
    float width = selected ? (float)lineWidth + 1.0f : (float)lineWidth;
    D2D1_COLOR_F drawColor = selected ? D2D1::ColorF(D2D1::ColorF::Red) : color;
    ScanlineFillD2D::DrawThickLine(pRT, pBrush, start.x, start.y, end.x, end.y, width, drawColor);
}

// 使用示例
Line* line = new Line(D2D1::Point2F(100, 100), D2D1::Point2F(300, 200));
line->lineWidth = 10;
line->DrawWithScanlineFill(pRT, pBrush);
```

### Circle类使用扫描线填充

```cpp
// 在Circle类中
void DrawWithScanlineFill(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
    float width = selected ? (float)lineWidth + 1.0f : (float)lineWidth;
    D2D1_COLOR_F drawColor = selected ? D2D1::ColorF(D2D1::ColorF::Red) : color;
    ScanlineFillD2D::DrawThickCircle(pRT, pBrush, center.x, center.y, radius, width, drawColor);
}

// 使用示例
Circle* circle = new Circle(D2D1::Point2F(200, 200), 80);
circle->lineWidth = 8;
circle->DrawWithScanlineFill(pRT, pBrush);
```

### 在绘图循环中使用

```cpp
void OnPaint(HWND hwnd) {
    PAINTSTRUCT ps;
    HDC hdc = BeginPaint(hwnd, &ps);
    
    // 使用Direct2D绘制
    g_pRenderTarget->BeginDraw();
    g_pRenderTarget->Clear(D2D1::ColorF(D2D1::ColorF::White));
    
    // 遍历所有图形
    for (auto& shape : g_shapes) {
        if (shape->type == ShapeType::LINE) {
            Line* line = static_cast<Line*>(shape);
            // 使用扫描线填充法绘制
            line->DrawWithScanlineFill(g_pRenderTarget, g_pBrush);
        } else if (shape->type == ShapeType::CIRCLE) {
            Circle* circle = static_cast<Circle*>(shape);
            // 使用扫描线填充法绘制
            circle->DrawWithScanlineFill(g_pRenderTarget, g_pBrush);
        } else {
            // 其他图形使用普通Draw方法
            shape->Draw(g_pRenderTarget, g_pBrush);
        }
    }
    
    g_pRenderTarget->EndDraw();
    EndPaint(hwnd, &ps);
}
```

## Direct2D vs GDI 对比

| 特性 | Direct2D版本 | GDI版本 |
|------|-------------|---------|
| **渲染方式** | GPU硬件加速 | CPU软件渲染 |
| **抗锯齿** | ✅ 自动抗锯齿 | ❌ 无抗锯齿 |
| **性能** | ⚡ 高性能 | 🐌 较慢 |
| **边缘质量** | 平滑 | 锯齿 |
| **颜色格式** | D2D1_COLOR_F (浮点) | COLORREF (整数) |
| **坐标系统** | 浮点坐标 | 整数坐标 |
| **透明度** | ✅ 完整支持 | ⚠️ 有限支持 |
| **API复杂度** | 较复杂 | 简单 |

## 技术优势

### 1. 完全Direct2D实现
- 不使用任何GDI函数(`SetPixel`, `GetDC`, `ReleaseDC`等)
- 所有操作都在Direct2D上下文中完成
- 统一的渲染管线

### 2. 硬件加速
- 利用GPU加速渲染
- 大量图形时性能优异
- 流畅的动画效果

### 3. 高质量渲染
- 自动抗锯齿
- 亚像素精度
- 平滑的边缘

### 4. 现代图形API
- 支持透明度混合
- 支持变换矩阵
- 支持复杂路径

## 关键Direct2D对象

### ID2D1PathGeometry
用于创建复杂的几何路径:
```cpp
ID2D1Factory* pFactory;
pRT->GetFactory(&pFactory);

ID2D1PathGeometry* pPathGeometry;
pFactory->CreatePathGeometry(&pPathGeometry);
```

### ID2D1GeometrySink
用于构建路径:
```cpp
ID2D1GeometrySink* pSink;
pPathGeometry->Open(&pSink);

pSink->BeginFigure(startPoint, D2D1_FIGURE_BEGIN_FILLED);
pSink->AddLine(point1);
pSink->AddArc(arcSegment);
pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
pSink->Close();
```

### FillGeometry
填充几何图形:
```cpp
pBrush->SetColor(color);
pRT->FillGeometry(pPathGeometry, pBrush);
```

## 资源管理

**重要**: Direct2D对象需要手动释放:

```cpp
// 使用完毕后释放
if (pSink) pSink->Release();
if (pPathGeometry) pPathGeometry->Release();
if (pFactory) pFactory->Release();
```

## 示例:完整的绘制流程

```cpp
// 1. 创建图形
Line* line = new Line(D2D1::Point2F(50, 50), D2D1::Point2F(350, 150));
line->lineWidth = 15;
line->color = D2D1::ColorF(D2D1::ColorF::Blue);

Circle* circle = new Circle(D2D1::Point2F(200, 300), 60);
circle->lineWidth = 12;
circle->color = D2D1::ColorF(D2D1::ColorF::Green);

// 2. 在绘制循环中
g_pRenderTarget->BeginDraw();
g_pRenderTarget->Clear(D2D1::ColorF(D2D1::ColorF::White));

// 3. 使用扫描线填充法绘制
line->DrawWithScanlineFill(g_pRenderTarget, g_pBrush);
circle->DrawWithScanlineFill(g_pRenderTarget, g_pBrush);

// 4. 结束绘制
HRESULT hr = g_pRenderTarget->EndDraw();
if (FAILED(hr)) {
    // 处理错误
}
```

## 性能优化建议

1. **批量绘制**: 在一个`BeginDraw/EndDraw`块中绘制多个图形
2. **避免频繁创建**: 重用PathGeometry对象
3. **使用合适的抗锯齿模式**: 根据需要调整
4. **资源池**: 对常用的几何对象使用对象池

## 总结

Direct2D版本的扫描线填充实现:
- ✅ 完全不使用GDI
- ✅ 硬件加速渲染
- ✅ 高质量抗锯齿
- ✅ 支持任意线宽
- ✅ 统一的API接口
- ✅ 现代化的图形渲染

这是一个完全基于Direct2D的专业级实现,适合现代Windows应用程序开发!
