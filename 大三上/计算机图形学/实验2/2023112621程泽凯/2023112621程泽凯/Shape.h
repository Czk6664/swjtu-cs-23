#pragma once
#include "framework.h"
#include <functional>
#include <vector>
#include <string>

const float PI = 3.14159265358979323846f;

inline D2D1_POINT_2F RotatePoint(D2D1_POINT_2F p, D2D1_POINT_2F center, float angle) {
    float s = sin(angle);
    float c = cos(angle);
    p.x -= center.x;
    p.y -= center.y;
    float xnew = p.x * c - p.y * s;
    float ynew = p.x * s + p.y * c;
    return D2D1::Point2F(xnew + center.x, ynew + center.y);
}

inline D2D1_POINT_2F ScalePoint(D2D1_POINT_2F p, D2D1_POINT_2F center, float factor) {
    return D2D1::Point2F(center.x + (p.x - center.x) * factor, center.y + (p.y - center.y) * factor);
}

inline float PointToLineDistance(D2D1_POINT_2F p, D2D1_POINT_2F a, D2D1_POINT_2F b) {
    float dx = b.x - a.x;
    float dy = b.y - a.y;
    float len = sqrt(dx * dx + dy * dy);
    if (len < 0.001f) return sqrt((p.x - a.x) * (p.x - a.x) + (p.y - a.y) * (p.y - a.y));
    
    float t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / (len * len);
    t = max(0.0f, min(1.0f, t));
    
    float px = a.x + t * dx;
    float py = a.y + t * dy;
    return sqrt((p.x - px) * (p.x - px) + (p.y - py) * (p.y - py));
}

enum class ShapeType {
    NONE, LINE, CIRCLE, RECTANGLE, TRIANGLE, DIAMOND, PARALLELOGRAM, CURVE, POLYLINE
};

class Shape {
public:
    ShapeType type;
    bool selected;
    D2D1_COLOR_F color;
    std::vector<D2D1_POINT_2F> points;
    
    Shape(ShapeType t) : type(t), selected(false), color(D2D1::ColorF(D2D1::ColorF::Black)) {}
    virtual ~Shape() {}
    
    virtual void Draw(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush) = 0;
    virtual bool HitTest(D2D1_POINT_2F point) = 0;
    virtual void Move(float dx, float dy) = 0;
    virtual void Rotate(D2D1_POINT_2F center, float angle) = 0;
    virtual void Scale(D2D1_POINT_2F center, float factor) = 0;
    virtual D2D1_POINT_2F GetCenter() = 0;
    virtual std::string Serialize() = 0;
    virtual void Deserialize(const std::string& data) = 0;
    
    void DrawDashed(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush, 
                    std::function<void(ID2D1StrokeStyle*)> drawFunc) {
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        ID2D1StrokeStyle* pStrokeStyle = nullptr;
        D2D1_STROKE_STYLE_PROPERTIES strokeProps = D2D1::StrokeStyleProperties(
            D2D1_CAP_STYLE_FLAT, D2D1_CAP_STYLE_FLAT, D2D1_CAP_STYLE_FLAT,
            D2D1_LINE_JOIN_MITER, 10.0f, D2D1_DASH_STYLE_DASH, 0.0f);
        pFactory->CreateStrokeStyle(&strokeProps, nullptr, 0, &pStrokeStyle);
        if (pStrokeStyle) {
            drawFunc(pStrokeStyle);
            pStrokeStyle->Release();
        }
        if (pFactory) pFactory->Release();
    }
};
