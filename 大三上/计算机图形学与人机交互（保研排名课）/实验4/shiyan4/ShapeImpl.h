#pragma once
#include "Shape.h"
#include "Algorithms.h"
#include "ScanlineFillD2D.h"
#include <sstream>
#include <vector>

// Drawing property enums for Experiment 3
enum class LineAlgorithm { DIRECT2D, MIDPOINT, BRESENHAM };
enum class CircleAlgorithm { DIRECT2D, MIDPOINT, BRESENHAM };
enum class LineStyleType { SOLID, DASH, DOT, DASHDOT };

// Line class
class Line : public Shape {
public:
    D2D1_POINT_2F start, end;
    LineAlgorithm lineAlgorithm;
    int lineWidth;
    LineStyleType lineStyle;
    
    Line() : Shape(ShapeType::LINE), start(), end(),
             lineAlgorithm(LineAlgorithm::DIRECT2D), 
             lineWidth(1), lineStyle(LineStyleType::SOLID) {}
    Line(D2D1_POINT_2F s, D2D1_POINT_2F e) : Shape(ShapeType::LINE), 
                                              start(s), end(e),
                                              lineAlgorithm(LineAlgorithm::DIRECT2D),
                                              lineWidth(1), lineStyle(LineStyleType::SOLID) {
        points.push_back(s);
        points.push_back(e);
    }
    
    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        if (!pRT || !pBrush) return;  // 安全检查
        
        float width = selected ? (float)lineWidth + 1.0f : (float)lineWidth;
        D2D1_COLOR_F drawColor = selected ? D2D1::ColorF(D2D1::ColorF::Red) : color;
        
        // 尝试使用扫描线填充法绘制粗实线 (线宽>1且为实线)
        bool usedScanlineFill = false;
        if (lineWidth > 1 && lineStyle == LineStyleType::SOLID) {
            ID2D1HwndRenderTarget* hwndRT = nullptr;
            if (SUCCEEDED(pRT->QueryInterface(__uuidof(ID2D1HwndRenderTarget), (void**)&hwndRT)) && hwndRT) {
                ScanlineFillD2D::DrawThickLine(hwndRT, pBrush, start.x, start.y, end.x, end.y, width, drawColor);
                hwndRT->Release();
                usedScanlineFill = true;
            }
        }
        
        // 如果没有使用扫描线填充，使用Direct2D绘制
        if (usedScanlineFill) return;
        
        pBrush->SetColor(drawColor);
        
        // Create stroke style based on lineStyle
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        ID2D1StrokeStyle* pStrokeStyle = nullptr;
        
        if (pFactory) {
            D2D1_STROKE_STYLE_PROPERTIES strokeProps = D2D1::StrokeStyleProperties();
            FLOAT* dashes = nullptr;
            UINT32 dashCount = 0;
            
            // Set custom dash patterns for better visual distinction
            switch (lineStyle) {
                case LineStyleType::DASH: {
                    // 虚线: 长划线 (8像素线段, 4像素间隔)
                    strokeProps.dashStyle = D2D1_DASH_STYLE_CUSTOM;
                    static FLOAT dashPattern[] = { 8.0f, 4.0f };
                    dashes = dashPattern;
                    dashCount = 2;
                    break;
                }
                case LineStyleType::DOT: {
                    // 点线: 短点 (1像素点, 3像素间隔)
                    strokeProps.dashStyle = D2D1_DASH_STYLE_CUSTOM;
                    static FLOAT dotPattern[] = { 1.0f, 3.0f };
                    dashes = dotPattern;
                    dashCount = 2;
                    break;
                }
                case LineStyleType::DASHDOT: {
                    // 点划线: 长划线+短点 (8像素线段, 3像素间隔, 1像素点, 3像素间隔)
                    strokeProps.dashStyle = D2D1_DASH_STYLE_CUSTOM;
                    static FLOAT dashDotPattern[] = { 8.0f, 3.0f, 1.0f, 3.0f };
                    dashes = dashDotPattern;
                    dashCount = 4;
                    break;
                }
                default:
                    strokeProps.dashStyle = D2D1_DASH_STYLE_SOLID;
                    break;
            }
            
            pFactory->CreateStrokeStyle(strokeProps, dashes, dashCount, &pStrokeStyle);
            pFactory->Release();
        }
        
        // Draw line with custom width and style
        pRT->DrawLine(start, end, pBrush, width, pStrokeStyle);
        
        if (pStrokeStyle) {
            pStrokeStyle->Release();
        }
    }
    
    // 使用扫描线填充法绘制粗线 (Direct2D版本)
    void DrawWithScanlineFill(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
        float width = selected ? (float)lineWidth + 1.0f : (float)lineWidth;
        D2D1_COLOR_F drawColor = selected ? D2D1::ColorF(D2D1::ColorF::Red) : color;
        ScanlineFillD2D::DrawThickLine(pRT, pBrush, start.x, start.y, end.x, end.y, width, drawColor);
    }
    
    bool HitTest(D2D1_POINT_2F point) override {
        return PointToLineDistance(point, start, end) < 5.0f;
    }
    
    void Move(float dx, float dy) override {
        start.x += dx; start.y += dy;
        end.x += dx; end.y += dy;
        points.clear();
        points.push_back(start);
        points.push_back(end);
    }
    
    void Rotate(D2D1_POINT_2F center, float angle) override {
        start = RotatePoint(start, center, angle);
        end = RotatePoint(end, center, angle);
        points.clear();
        points.push_back(start);
        points.push_back(end);
    }
    
    void Scale(D2D1_POINT_2F center, float factor) override {
        start = ScalePoint(start, center, factor);
        end = ScalePoint(end, center, factor);
        points.clear();
        points.push_back(start);
        points.push_back(end);
    }
    
    D2D1_POINT_2F GetCenter() override {
        return D2D1::Point2F((start.x + end.x) / 2, (start.y + end.y) / 2);
    }
    
    std::string Serialize() override {
        std::stringstream ss;
        ss << "LINE " << start.x << " " << start.y << " " << end.x << " " << end.y;
        return ss.str();
    }
    
    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        ss >> type >> start.x >> start.y >> end.x >> end.y;
        points.clear();
        points.push_back(start);
        points.push_back(end);
    }
};

// Circle class
class Circle : public Shape {
public:
    D2D1_POINT_2F center;
    float radius;
    CircleAlgorithm circleAlgorithm;
    int lineWidth;
    LineStyleType lineStyle;  // 添加线型属性
    
    Circle() : Shape(ShapeType::CIRCLE), center(), radius(0), 
               circleAlgorithm(CircleAlgorithm::DIRECT2D), lineWidth(1), lineStyle(LineStyleType::SOLID) {}
    Circle(D2D1_POINT_2F c, float r) : Shape(ShapeType::CIRCLE), 
                                        center(c), radius(r),
                                        circleAlgorithm(CircleAlgorithm::DIRECT2D),
                                        lineWidth(1), lineStyle(LineStyleType::SOLID) {
        points.push_back(c);
    }
    
    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        if (!pRT || !pBrush) return;  // 安全检查
        
        D2D1_ELLIPSE ellipse = D2D1::Ellipse(center, radius, radius);
        
        // Draw fill if enabled
        if (filled) {
            pBrush->SetColor(fillColor);
            pRT->FillEllipse(ellipse, pBrush);
        }
        
        // Draw outline with stroke style
        float width = selected ? (float)lineWidth + 1.0f : (float)lineWidth;
        D2D1_COLOR_F drawColor = selected ? D2D1::ColorF(D2D1::ColorF::Red) : color;
        
        // 尝试使用扫描线填充法绘制粗实线圆 (线宽>1且为实线)
        bool usedScanlineFill = false;
        if (lineWidth > 1 && lineStyle == LineStyleType::SOLID) {
            ID2D1HwndRenderTarget* hwndRT = nullptr;
            if (SUCCEEDED(pRT->QueryInterface(__uuidof(ID2D1HwndRenderTarget), (void**)&hwndRT)) && hwndRT) {
                ScanlineFillD2D::DrawThickCircle(hwndRT, pBrush, center.x, center.y, radius, width, drawColor);
                hwndRT->Release();
                usedScanlineFill = true;
            }
        }
        
        // 如果没有使用扫描线填充，使用Direct2D绘制
        if (usedScanlineFill) return;
        
        pBrush->SetColor(drawColor);
        
        // Create stroke style based on lineStyle
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        ID2D1StrokeStyle* pStrokeStyle = nullptr;
        
        if (pFactory) {
            D2D1_STROKE_STYLE_PROPERTIES strokeProps = D2D1::StrokeStyleProperties();
            FLOAT* dashes = nullptr;
            UINT32 dashCount = 0;
            
            switch (lineStyle) {
                case LineStyleType::DASH: {
                    strokeProps.dashStyle = D2D1_DASH_STYLE_CUSTOM;
                    static FLOAT dashPattern[] = { 8.0f, 4.0f };
                    dashes = dashPattern;
                    dashCount = 2;
                    break;
                }
                case LineStyleType::DOT: {
                    strokeProps.dashStyle = D2D1_DASH_STYLE_CUSTOM;
                    static FLOAT dotPattern[] = { 1.0f, 3.0f };
                    dashes = dotPattern;
                    dashCount = 2;
                    break;
                }
                case LineStyleType::DASHDOT: {
                    strokeProps.dashStyle = D2D1_DASH_STYLE_CUSTOM;
                    static FLOAT dashDotPattern[] = { 8.0f, 3.0f, 1.0f, 3.0f };
                    dashes = dashDotPattern;
                    dashCount = 4;
                    break;
                }
                default:
                    strokeProps.dashStyle = D2D1_DASH_STYLE_SOLID;
                    break;
            }
            
            pFactory->CreateStrokeStyle(strokeProps, dashes, dashCount, &pStrokeStyle);
            pFactory->Release();
        }
        
        pRT->DrawEllipse(ellipse, pBrush, width, pStrokeStyle);
        
        if (pStrokeStyle) {
            pStrokeStyle->Release();
        }
    }
    
    // 使用扫描线填充法绘制粗圆 (Direct2D版本)
    void DrawWithScanlineFill(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
        float width = selected ? (float)lineWidth + 1.0f : (float)lineWidth;
        D2D1_COLOR_F drawColor = selected ? D2D1::ColorF(D2D1::ColorF::Red) : color;
        ScanlineFillD2D::DrawThickCircle(pRT, pBrush, center.x, center.y, radius, width, drawColor);
    }
    
    bool HitTest(D2D1_POINT_2F point) override {
        float dx = point.x - center.x;
        float dy = point.y - center.y;
        float dist = sqrt(dx * dx + dy * dy);
        return fabs(dist - radius) < 5.0f;
    }
    
    void Move(float dx, float dy) override {
        center.x += dx; center.y += dy;
        points.clear();
        points.push_back(center);
    }
    
    void Rotate(D2D1_POINT_2F rotCenter, float angle) override {
        center = RotatePoint(center, rotCenter, angle);
        points.clear();
        points.push_back(center);
    }
    
    void Scale(D2D1_POINT_2F scaleCenter, float factor) override {
        center = ScalePoint(center, scaleCenter, factor);
        radius *= factor;
        points.clear();
        points.push_back(center);
    }
    
    D2D1_POINT_2F GetCenter() override { return center; }
    
    std::string Serialize() override {
        std::stringstream ss;
        ss << "CIRCLE " << center.x << " " << center.y << " " << radius;
        return ss.str();
    }
    
    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        ss >> type >> center.x >> center.y >> radius;
        points.clear();
        points.push_back(center);
    }
};

// Rectangle class
class RectangleShape : public Shape {
public:
    D2D1_POINT_2F p1, p2, p3, p4;  // Four corners of rectangle
    
    RectangleShape() : Shape(ShapeType::RECTANGLE) {}
    RectangleShape(D2D1_POINT_2F tl, D2D1_POINT_2F br) : Shape(ShapeType::RECTANGLE) {
        // Initialize as axis-aligned rectangle
        p1 = tl;
        p2 = D2D1::Point2F(br.x, tl.y);
        p3 = br;
        p4 = D2D1::Point2F(tl.x, br.y);
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        ID2D1PathGeometry* pPath = nullptr;
        pFactory->CreatePathGeometry(&pPath);
        ID2D1GeometrySink* pSink = nullptr;
        pPath->Open(&pSink);
        pSink->BeginFigure(p1, filled ? D2D1_FIGURE_BEGIN_FILLED : D2D1_FIGURE_BEGIN_HOLLOW);
        pSink->AddLine(p2);
        pSink->AddLine(p3);
        pSink->AddLine(p4);
        pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
        pSink->Close();
        
        // Draw fill if enabled
        if (filled) {
            pBrush->SetColor(fillColor);
            pRT->FillGeometry(pPath, pBrush);
        }
        
        // Draw outline
        pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
        if (selected) {
            DrawDashed(pRT, pBrush, [&](ID2D1StrokeStyle* style) {
                pRT->DrawGeometry(pPath, pBrush, 2.0f, style);
            });
        } else {
            pRT->DrawGeometry(pPath, pBrush, 1.0f);
        }
        
        pSink->Release();
        pPath->Release();
        pFactory->Release();
    }
    
    bool HitTest(D2D1_POINT_2F point) override {
        return PointToLineDistance(point, p1, p2) < 5.0f ||
               PointToLineDistance(point, p2, p3) < 5.0f ||
               PointToLineDistance(point, p3, p4) < 5.0f ||
               PointToLineDistance(point, p4, p1) < 5.0f;
    }
    
    void Move(float dx, float dy) override {
        p1.x += dx; p1.y += dy;
        p2.x += dx; p2.y += dy;
        p3.x += dx; p3.y += dy;
        p4.x += dx; p4.y += dy;
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    void Rotate(D2D1_POINT_2F center, float angle) override {
        p1 = RotatePoint(p1, center, angle);
        p2 = RotatePoint(p2, center, angle);
        p3 = RotatePoint(p3, center, angle);
        p4 = RotatePoint(p4, center, angle);
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    void Scale(D2D1_POINT_2F center, float factor) override {
        p1 = ScalePoint(p1, center, factor);
        p2 = ScalePoint(p2, center, factor);
        p3 = ScalePoint(p3, center, factor);
        p4 = ScalePoint(p4, center, factor);
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    D2D1_POINT_2F GetCenter() override {
        return D2D1::Point2F((p1.x + p2.x + p3.x + p4.x) / 4, (p1.y + p2.y + p3.y + p4.y) / 4);
    }
    
    std::string Serialize() override {
        std::stringstream ss;
        ss << "RECTANGLE " << p1.x << " " << p1.y << " " << p2.x << " " << p2.y << " "
           << p3.x << " " << p3.y << " " << p4.x << " " << p4.y;
        return ss.str();
    }
    
    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        ss >> type;
        // Try to read 4 points (new format)
        if (ss >> p1.x >> p1.y >> p2.x >> p2.y >> p3.x >> p3.y >> p4.x >> p4.y) {
            // New format with 4 points
        } else {
            // Old format with 2 points - convert to 4 corners
            ss.clear();
            ss.str(data);
            D2D1_POINT_2F tl, br;
            ss >> type >> tl.x >> tl.y >> br.x >> br.y;
            p1 = tl;
            p2 = D2D1::Point2F(br.x, tl.y);
            p3 = br;
            p4 = D2D1::Point2F(tl.x, br.y);
        }
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
};

// Triangle class
class Triangle : public Shape {
public:
    D2D1_POINT_2F p1, p2, p3;
    
    Triangle() : Shape(ShapeType::TRIANGLE) {}
    Triangle(D2D1_POINT_2F a, D2D1_POINT_2F b, D2D1_POINT_2F c) : Shape(ShapeType::TRIANGLE), p1(a), p2(b), p3(c) {
        points.push_back(a);
        points.push_back(b);
        points.push_back(c);
    }
    
    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        ID2D1PathGeometry* pPath = nullptr;
        pFactory->CreatePathGeometry(&pPath);
        ID2D1GeometrySink* pSink = nullptr;
        pPath->Open(&pSink);
        pSink->BeginFigure(p1, filled ? D2D1_FIGURE_BEGIN_FILLED : D2D1_FIGURE_BEGIN_HOLLOW);
        pSink->AddLine(p2);
        pSink->AddLine(p3);
        pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
        pSink->Close();
        
        // Draw fill if enabled
        if (filled) {
            pBrush->SetColor(fillColor);
            pRT->FillGeometry(pPath, pBrush);
        }
        
        // Draw outline
        pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
        if (selected) {
            DrawDashed(pRT, pBrush, [&](ID2D1StrokeStyle* style) {
                pRT->DrawGeometry(pPath, pBrush, 2.0f, style);
            });
        } else {
            pRT->DrawGeometry(pPath, pBrush, 1.0f);
        }
        
        pSink->Release();
        pPath->Release();
        pFactory->Release();
    }
    
    bool HitTest(D2D1_POINT_2F point) override {
        return PointToLineDistance(point, p1, p2) < 5.0f ||
               PointToLineDistance(point, p2, p3) < 5.0f ||
               PointToLineDistance(point, p3, p1) < 5.0f;
    }
    
    void Move(float dx, float dy) override {
        p1.x += dx; p1.y += dy;
        p2.x += dx; p2.y += dy;
        p3.x += dx; p3.y += dy;
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
    }
    
    void Rotate(D2D1_POINT_2F center, float angle) override {
        p1 = RotatePoint(p1, center, angle);
        p2 = RotatePoint(p2, center, angle);
        p3 = RotatePoint(p3, center, angle);
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
    }
    
    void Scale(D2D1_POINT_2F center, float factor) override {
        p1 = ScalePoint(p1, center, factor);
        p2 = ScalePoint(p2, center, factor);
        p3 = ScalePoint(p3, center, factor);
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
    }
    
    D2D1_POINT_2F GetCenter() override {
        return D2D1::Point2F((p1.x + p2.x + p3.x) / 3, (p1.y + p2.y + p3.y) / 3);
    }
    
    std::string Serialize() override {
        std::stringstream ss;
        ss << "TRIANGLE " << p1.x << " " << p1.y << " " << p2.x << " " << p2.y << " " << p3.x << " " << p3.y;
        return ss.str();
    }
    
    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        ss >> type >> p1.x >> p1.y >> p2.x >> p2.y >> p3.x >> p3.y;
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
    }
};

// Diamond class
class Diamond : public Shape {
public:
    D2D1_POINT_2F center;
    float width, height;
    D2D1_POINT_2F top, right, bottom, left;  // Actual vertices after transformations
    
    Diamond() : Shape(ShapeType::DIAMOND), width(0), height(0) {}
    Diamond(D2D1_POINT_2F c, float w, float h) : Shape(ShapeType::DIAMOND), center(c), width(w), height(h) {
        points.push_back(c);
        UpdateVertices();
    }
    
    void UpdateVertices() {
        top = D2D1::Point2F(center.x, center.y - height / 2);
        right = D2D1::Point2F(center.x + width / 2, center.y);
        bottom = D2D1::Point2F(center.x, center.y + height / 2);
        left = D2D1::Point2F(center.x - width / 2, center.y);
    }
    
    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        UpdateVertices();
        
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        ID2D1PathGeometry* pPath = nullptr;
        pFactory->CreatePathGeometry(&pPath);
        ID2D1GeometrySink* pSink = nullptr;
        pPath->Open(&pSink);
        pSink->BeginFigure(top, filled ? D2D1_FIGURE_BEGIN_FILLED : D2D1_FIGURE_BEGIN_HOLLOW);
        pSink->AddLine(right);
        pSink->AddLine(bottom);
        pSink->AddLine(left);
        pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
        pSink->Close();
        
        // Draw fill if enabled
        if (filled) {
            pBrush->SetColor(fillColor);
            pRT->FillGeometry(pPath, pBrush);
        }
        
        // Draw outline
        pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
        if (selected) {
            DrawDashed(pRT, pBrush, [&](ID2D1StrokeStyle* style) {
                pRT->DrawGeometry(pPath, pBrush, 2.0f, style);
            });
        } else {
            pRT->DrawGeometry(pPath, pBrush, 1.0f);
        }
        
        pSink->Release();
        pPath->Release();
        pFactory->Release();
    }
    
    bool HitTest(D2D1_POINT_2F point) override {
        UpdateVertices();
        
        return PointToLineDistance(point, top, right) < 5.0f ||
               PointToLineDistance(point, right, bottom) < 5.0f ||
               PointToLineDistance(point, bottom, left) < 5.0f ||
               PointToLineDistance(point, left, top) < 5.0f;
    }
    
    void Move(float dx, float dy) override {
        center.x += dx; center.y += dy;
        top.x += dx; top.y += dy;
        right.x += dx; right.y += dy;
        bottom.x += dx; bottom.y += dy;
        left.x += dx; left.y += dy;
        points.clear();
        points.push_back(center);
    }
    
    void Rotate(D2D1_POINT_2F rotCenter, float angle) override {
        center = RotatePoint(center, rotCenter, angle);
        top = RotatePoint(top, rotCenter, angle);
        right = RotatePoint(right, rotCenter, angle);
        bottom = RotatePoint(bottom, rotCenter, angle);
        left = RotatePoint(left, rotCenter, angle);
        points.clear();
        points.push_back(center);
    }
    
    void Scale(D2D1_POINT_2F scaleCenter, float factor) override {
        center = ScalePoint(center, scaleCenter, factor);
        top = ScalePoint(top, scaleCenter, factor);
        right = ScalePoint(right, scaleCenter, factor);
        bottom = ScalePoint(bottom, scaleCenter, factor);
        left = ScalePoint(left, scaleCenter, factor);
        width *= factor;
        height *= factor;
        points.clear();
        points.push_back(center);
    }
    
    D2D1_POINT_2F GetCenter() override { return center; }
    
    std::string Serialize() override {
        std::stringstream ss;
        ss << "DIAMOND " << center.x << " " << center.y << " " << width << " " << height;
        return ss.str();
    }
    
    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        ss >> type >> center.x >> center.y >> width >> height;
        UpdateVertices();
        points.clear();
        points.push_back(center);
    }
};

// Parallelogram class
class Parallelogram : public Shape {
public:
    D2D1_POINT_2F p1, p2, p3, p4;
    
    Parallelogram() : Shape(ShapeType::PARALLELOGRAM) {}
    Parallelogram(D2D1_POINT_2F a, D2D1_POINT_2F b, D2D1_POINT_2F c) : Shape(ShapeType::PARALLELOGRAM) {
        p1 = a;
        p2 = b;
        p3 = c;
        p4 = D2D1::Point2F(p1.x + (p3.x - p2.x), p1.y + (p3.y - p2.y));
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        ID2D1PathGeometry* pPath = nullptr;
        pFactory->CreatePathGeometry(&pPath);
        ID2D1GeometrySink* pSink = nullptr;
        pPath->Open(&pSink);
        pSink->BeginFigure(p1, filled ? D2D1_FIGURE_BEGIN_FILLED : D2D1_FIGURE_BEGIN_HOLLOW);
        pSink->AddLine(p2);
        pSink->AddLine(p3);
        pSink->AddLine(p4);
        pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
        pSink->Close();
        
        // Draw fill if enabled
        if (filled) {
            pBrush->SetColor(fillColor);
            pRT->FillGeometry(pPath, pBrush);
        }
        
        // Draw outline
        pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
        if (selected) {
            DrawDashed(pRT, pBrush, [&](ID2D1StrokeStyle* style) {
                pRT->DrawGeometry(pPath, pBrush, 2.0f, style);
            });
        } else {
            pRT->DrawGeometry(pPath, pBrush, 1.0f);
        }
        
        pSink->Release();
        pPath->Release();
        pFactory->Release();
    }
    
    bool HitTest(D2D1_POINT_2F point) override {
        return PointToLineDistance(point, p1, p2) < 5.0f ||
               PointToLineDistance(point, p2, p3) < 5.0f ||
               PointToLineDistance(point, p3, p4) < 5.0f ||
               PointToLineDistance(point, p4, p1) < 5.0f;
    }
    
    void Move(float dx, float dy) override {
        p1.x += dx; p1.y += dy;
        p2.x += dx; p2.y += dy;
        p3.x += dx; p3.y += dy;
        p4.x += dx; p4.y += dy;
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    void Rotate(D2D1_POINT_2F center, float angle) override {
        p1 = RotatePoint(p1, center, angle);
        p2 = RotatePoint(p2, center, angle);
        p3 = RotatePoint(p3, center, angle);
        p4 = RotatePoint(p4, center, angle);
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    void Scale(D2D1_POINT_2F center, float factor) override {
        p1 = ScalePoint(p1, center, factor);
        p2 = ScalePoint(p2, center, factor);
        p3 = ScalePoint(p3, center, factor);
        p4 = ScalePoint(p4, center, factor);
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
    
    D2D1_POINT_2F GetCenter() override {
        return D2D1::Point2F((p1.x + p2.x + p3.x + p4.x) / 4, (p1.y + p2.y + p3.y + p4.y) / 4);
    }
    
    std::string Serialize() override {
        std::stringstream ss;
        ss << "PARALLELOGRAM " << p1.x << " " << p1.y << " " << p2.x << " " << p2.y << " " 
           << p3.x << " " << p3.y << " " << p4.x << " " << p4.y;
        return ss.str();
    }
    
    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        ss >> type >> p1.x >> p1.y >> p2.x >> p2.y >> p3.x >> p3.y >> p4.x >> p4.y;
        points.clear();
        points.push_back(p1);
        points.push_back(p2);
        points.push_back(p3);
        points.push_back(p4);
    }
};

// Curve class
class Curve : public Shape {
public:
    std::vector<D2D1_POINT_2F> curvePoints;
    
    Curve() : Shape(ShapeType::CURVE) {}
    
    void AddPoint(D2D1_POINT_2F p) {
        curvePoints.push_back(p);
        points.push_back(p);
    }
    
    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        if (curvePoints.empty()) return;
        
        pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
        
        // Draw single point as a small circle
        if (curvePoints.size() == 1) {
            D2D1_ELLIPSE ellipse = D2D1::Ellipse(curvePoints[0], 3.0f, 3.0f);
            pRT->FillEllipse(ellipse, pBrush);
            return;
        }
        
        // Two points: just draw a line
        if (curvePoints.size() == 2) {
            pRT->DrawLine(curvePoints[0], curvePoints[1], pBrush, 
                         selected ? 2.5f : 2.0f);
            return;
        }
        
        // Three or more points: use Bezier curve (实验2算法)
        // Generate smooth Bezier curve through all control points
        auto generatedPoints = BezierCurve::GenerateCurve(curvePoints, 100);
        
        if (generatedPoints.size() < 2) return;
        
        // Draw the generated smooth curve
        for (size_t i = 0; i < generatedPoints.size() - 1; i++) {
            pRT->DrawLine(generatedPoints[i], generatedPoints[i + 1], pBrush, 
                         selected ? 2.5f : 2.0f);
        }
    }
    
    bool HitTest(D2D1_POINT_2F point) override {
        if (curvePoints.empty()) return false;
        
        // Check if point is near any control point
        for (const auto& cp : curvePoints) {
            float dx = point.x - cp.x;
            float dy = point.y - cp.y;
            if (sqrt(dx * dx + dy * dy) < 8.0f) return true;
        }
        
        // Check if point is near the actual curve using sampled points
        auto sampledPoints = GetSampledPoints(10);
        if (sampledPoints.size() >= 2) {
            for (size_t i = 0; i < sampledPoints.size() - 1; i++) {
                if (PointToLineDistance(point, sampledPoints[i], sampledPoints[i + 1]) < 5.0f)
                    return true;
            }
        }
        return false;
    }
    
    void Move(float dx, float dy) override {
        for (auto& p : curvePoints) {
            p.x += dx; p.y += dy;
        }
        points = curvePoints;
    }
    
    void Rotate(D2D1_POINT_2F center, float angle) override {
        for (auto& p : curvePoints) {
            p = RotatePoint(p, center, angle);
        }
        points = curvePoints;
    }
    
    void Scale(D2D1_POINT_2F center, float factor) override {
        for (auto& p : curvePoints) {
            p = ScalePoint(p, center, factor);
        }
        points = curvePoints;
    }
    
    D2D1_POINT_2F GetCenter() override {
        if (curvePoints.empty()) return D2D1::Point2F(0, 0);
        float sumX = 0, sumY = 0;
        for (const auto& p : curvePoints) {
            sumX += p.x;
            sumY += p.y;
        }
        return D2D1::Point2F(sumX / curvePoints.size(), sumY / curvePoints.size());
    }
    
    // Get sampled points along the Bezier curve for intersection calculations
    std::vector<D2D1_POINT_2F> GetSampledPoints(int samplesPerSegment = 10) const {
        std::vector<D2D1_POINT_2F> sampledPoints;
        if (curvePoints.empty()) return sampledPoints;
        
        if (curvePoints.size() == 1) {
            sampledPoints.push_back(curvePoints[0]);
            return sampledPoints;
        }
        
        if (curvePoints.size() == 2) {
            // Linear interpolation for 2 points
            for (int i = 0; i <= samplesPerSegment; i++) {
                float t = (float)i / samplesPerSegment;
                D2D1_POINT_2F pt;
                pt.x = curvePoints[0].x + t * (curvePoints[1].x - curvePoints[0].x);
                pt.y = curvePoints[0].y + t * (curvePoints[1].y - curvePoints[0].y);
                sampledPoints.push_back(pt);
            }
            return sampledPoints;
        }
        
        // Sample the Bezier curve segments
        auto sampleQuadraticBezier = [](D2D1_POINT_2F p0, D2D1_POINT_2F p1, D2D1_POINT_2F p2, 
                                        int samples, std::vector<D2D1_POINT_2F>& output) {
            for (int i = 0; i <= samples; i++) {
                float t = (float)i / samples;
                float u = 1.0f - t;
                D2D1_POINT_2F pt;
                pt.x = u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x;
                pt.y = u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y;
                output.push_back(pt);
            }
        };
        
        // Sample the curve matching the Draw() logic
        D2D1_POINT_2F currentPoint = curvePoints[0];
        sampledPoints.push_back(currentPoint);
        
        for (size_t i = 0; i < curvePoints.size() - 1; i++) {
            D2D1_POINT_2F p0 = currentPoint;
            D2D1_POINT_2F p1 = curvePoints[i + 1];  // Control point
            D2D1_POINT_2F p2;  // End point
            
            if (i == curvePoints.size() - 2) {
                // Last segment: end at last control point
                p2 = curvePoints[i + 1];
            } else {
                // End at midpoint
                p2 = D2D1::Point2F((curvePoints[i + 1].x + curvePoints[i + 2].x) / 2,
                                   (curvePoints[i + 1].y + curvePoints[i + 2].y) / 2);
            }
            
            // Sample this segment (skip first point to avoid duplicates)
            for (int j = 1; j <= samplesPerSegment; j++) {
                float t = (float)j / samplesPerSegment;
                float u = 1.0f - t;
                D2D1_POINT_2F pt;
                pt.x = u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x;
                pt.y = u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y;
                sampledPoints.push_back(pt);
            }
            
            currentPoint = p2;  // Update current point for next segment
        }
        
        return sampledPoints;
    }
    
    std::string Serialize() override {
        std::stringstream ss;
        ss << "CURVE " << curvePoints.size();
        for (const auto& p : curvePoints) {
            ss << " " << p.x << " " << p.y;
        }
        return ss.str();
    }
    
    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        size_t count;
        ss >> type >> count;
        curvePoints.clear();
        for (size_t i = 0; i < count; i++) {
            D2D1_POINT_2F p;
            ss >> p.x >> p.y;
            curvePoints.push_back(p);
        }
        points = curvePoints;
    }
};

// Polyline class - closed polygon without fill
class PolylineShape : public Shape {
public:
    std::vector<D2D1_POINT_2F> polyPoints;

    PolylineShape() : Shape(ShapeType::POLYLINE) {}

    void AddPoint(D2D1_POINT_2F p) {
        polyPoints.push_back(p);
        points.push_back(p);
    }

    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) override {
        if (!pRT || !pBrush) return;  // 安全检查
        if (polyPoints.empty()) return;

        if (polyPoints.size() == 1) {
            pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
            D2D1_ELLIPSE ellipse = D2D1::Ellipse(polyPoints[0], 2.0f, 2.0f);
            pRT->FillEllipse(ellipse, pBrush);
            return;
        }

        pBrush->SetColor(selected ? D2D1::ColorF(D2D1::ColorF::Red) : color);
        if (selected) {
            DrawDashed(pRT, pBrush, [&](ID2D1StrokeStyle* style) {
                for (size_t i = 0; i < polyPoints.size() - 1; i++) {
                    pRT->DrawLine(polyPoints[i], polyPoints[i + 1], pBrush, 2.0f, style);
                }
                if (polyPoints.size() >= 3) {
                    pRT->DrawLine(polyPoints.back(), polyPoints.front(), pBrush, 2.0f, style);
                }
            });
        } else {
            // 绘制多边形边
            for (size_t i = 0; i < polyPoints.size() - 1; i++) {
                pRT->DrawLine(polyPoints[i], polyPoints[i + 1], pBrush, 1.0f);
            }
            // 闭合多边形
            if (polyPoints.size() >= 3) {
                pRT->DrawLine(polyPoints.back(), polyPoints.front(), pBrush, 1.0f);
            }
        }
    }

    bool HitTest(D2D1_POINT_2F point) override {
        if (polyPoints.empty()) return false;

        for (size_t i = 0; i < polyPoints.size(); i++) {
            float dx = point.x - polyPoints[i].x;
            float dy = point.y - polyPoints[i].y;
            if (sqrt(dx * dx + dy * dy) < 8.0f) return true;
        }

        if (polyPoints.size() >= 2) {
            for (size_t i = 0; i < polyPoints.size() - 1; i++) {
                if (PointToLineDistance(point, polyPoints[i], polyPoints[i + 1]) < 5.0f)
                    return true;
            }
            if (polyPoints.size() >= 3) {
                if (PointToLineDistance(point, polyPoints.back(), polyPoints.front()) < 5.0f)
                    return true;
            }
        }
        return false;
    }

    void Move(float dx, float dy) override {
        for (size_t i = 0; i < polyPoints.size(); i++) {
            polyPoints[i].x += dx;
            polyPoints[i].y += dy;
        }
        points = polyPoints;
    }

    void Rotate(D2D1_POINT_2F center, float angle) override {
        for (size_t i = 0; i < polyPoints.size(); i++) {
            polyPoints[i] = RotatePoint(polyPoints[i], center, angle);
        }
        points = polyPoints;
    }

    void Scale(D2D1_POINT_2F center, float factor) override {
        for (size_t i = 0; i < polyPoints.size(); i++) {
            polyPoints[i] = ScalePoint(polyPoints[i], center, factor);
        }
        points = polyPoints;
    }

    D2D1_POINT_2F GetCenter() override {
        if (polyPoints.empty()) return D2D1::Point2F(0, 0);
        float sumX = 0, sumY = 0;
        for (size_t i = 0; i < polyPoints.size(); i++) {
            sumX += polyPoints[i].x;
            sumY += polyPoints[i].y;
        }
        return D2D1::Point2F(sumX / polyPoints.size(), sumY / polyPoints.size());
    }

    std::string Serialize() override {
        std::stringstream ss;
        ss << "POLYLINE " << polyPoints.size();
        for (size_t i = 0; i < polyPoints.size(); i++) {
            ss << " " << polyPoints[i].x << " " << polyPoints[i].y;
        }
        return ss.str();
    }

    void Deserialize(const std::string& data) override {
        std::stringstream ss(data);
        std::string type;
        size_t count;
        ss >> type >> count;
        polyPoints.clear();
        for (size_t i = 0; i < count; i++) {
            D2D1_POINT_2F p;
            ss >> p.x >> p.y;
            polyPoints.push_back(p);
        }
        points = polyPoints;
    }
};
