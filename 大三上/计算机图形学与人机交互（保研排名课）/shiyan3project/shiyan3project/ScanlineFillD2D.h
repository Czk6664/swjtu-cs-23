#pragma once
#include "framework.h"
#include <vector>
#include <algorithm>

// Direct2D版本的扫描线填充算法
class ScanlineFillD2D {
public:
    // 使用D2D绘制粗线(扫描线填充法)
    static void DrawThickLine(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                              float x1, float y1, float x2, float y2, float width, D2D1_COLOR_F color) {
        if (width <= 1.0f) {
            // 细线直接用DrawLine
            pBrush->SetColor(color);
            pRT->DrawLine(D2D1::Point2F(x1, y1), D2D1::Point2F(x2, y2), pBrush, 1.0f);
            return;
        }
        
        // 计算线段的垂直方向
        float dx = x2 - x1;
        float dy = y2 - y1;
        float len = sqrt(dx * dx + dy * dy);
        if (len < 0.001f) return;
        
        float perpX = -dy / len * (width / 2.0f);
        float perpY = dx / len * (width / 2.0f);
        
        // 计算粗线的四个顶点
        D2D1_POINT_2F vertices[4];
        vertices[0] = D2D1::Point2F(x1 + perpX, y1 + perpY);
        vertices[1] = D2D1::Point2F(x1 - perpX, y1 - perpY);
        vertices[2] = D2D1::Point2F(x2 - perpX, y2 - perpY);
        vertices[3] = D2D1::Point2F(x2 + perpX, y2 + perpY);
        
        // 使用D2D填充多边形
        FillPolygon(pRT, pBrush, vertices, 4, color);
    }
    
    // 使用D2D绘制粗圆(扫描线填充法)
    static void DrawThickCircle(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                                float cx, float cy, float radius, float width, D2D1_COLOR_F color) {
        if (width <= 1.0f) {
            // 细线圆直接用DrawEllipse
            pBrush->SetColor(color);
            D2D1_ELLIPSE ellipse = D2D1::Ellipse(D2D1::Point2F(cx, cy), radius, radius);
            pRT->DrawEllipse(ellipse, pBrush, 1.0f);
            return;
        }
        
        // 粗线圆:绘制环形
        float outerRadius = radius + width / 2.0f;
        float innerRadius = radius - width / 2.0f;
        if (innerRadius < 0) innerRadius = 0;
        
        // 创建环形路径
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        if (!pFactory) return;
        
        ID2D1PathGeometry* pPathGeometry = nullptr;
        HRESULT hr = pFactory->CreatePathGeometry(&pPathGeometry);
        if (FAILED(hr) || !pPathGeometry) {
            pFactory->Release();
            return;
        }
        
        ID2D1GeometrySink* pSink = nullptr;
        hr = pPathGeometry->Open(&pSink);
        if (FAILED(hr) || !pSink) {
            pPathGeometry->Release();
            pFactory->Release();
            return;
        }
        
        // 绘制外圆
        pSink->BeginFigure(D2D1::Point2F(cx + outerRadius, cy), D2D1_FIGURE_BEGIN_FILLED);
        D2D1_ARC_SEGMENT arc;
        arc.size = D2D1::SizeF(outerRadius, outerRadius);
        arc.rotationAngle = 0.0f;
        arc.sweepDirection = D2D1_SWEEP_DIRECTION_CLOCKWISE;
        arc.arcSize = D2D1_ARC_SIZE_SMALL;
        
        // 上半圆
        arc.point = D2D1::Point2F(cx - outerRadius, cy);
        pSink->AddArc(arc);
        // 下半圆
        arc.point = D2D1::Point2F(cx + outerRadius, cy);
        pSink->AddArc(arc);
        pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
        
        // 如果有内圆,绘制内圆(反向,形成环形)
        if (innerRadius > 0) {
            pSink->BeginFigure(D2D1::Point2F(cx + innerRadius, cy), D2D1_FIGURE_BEGIN_FILLED);
            arc.size = D2D1::SizeF(innerRadius, innerRadius);
            arc.sweepDirection = D2D1_SWEEP_DIRECTION_COUNTER_CLOCKWISE;
            
            // 下半圆(反向)
            arc.point = D2D1::Point2F(cx - innerRadius, cy);
            pSink->AddArc(arc);
            // 上半圆(反向)
            arc.point = D2D1::Point2F(cx + innerRadius, cy);
            pSink->AddArc(arc);
            pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
        }
        
        pSink->Close();
        
        // 填充环形
        pBrush->SetColor(color);
        pRT->FillGeometry(pPathGeometry, pBrush);
        
        // 清理
        pSink->Release();
        pPathGeometry->Release();
        pFactory->Release();
    }
    
    // 使用D2D填充多边形(扫描线填充法的D2D实现)
    static void FillPolygon(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                           D2D1_POINT_2F* vertices, int count, D2D1_COLOR_F color) {
        if (count < 3) return;
        
        ID2D1Factory* pFactory = nullptr;
        pRT->GetFactory(&pFactory);
        if (!pFactory) return;
        
        ID2D1PathGeometry* pPathGeometry = nullptr;
        HRESULT hr = pFactory->CreatePathGeometry(&pPathGeometry);
        if (FAILED(hr) || !pPathGeometry) {
            pFactory->Release();
            return;
        }
        
        ID2D1GeometrySink* pSink = nullptr;
        hr = pPathGeometry->Open(&pSink);
        if (FAILED(hr) || !pSink) {
            pPathGeometry->Release();
            pFactory->Release();
            return;
        }
        
        // 构建多边形路径
        pSink->BeginFigure(vertices[0], D2D1_FIGURE_BEGIN_FILLED);
        for (int i = 1; i < count; i++) {
            pSink->AddLine(vertices[i]);
        }
        pSink->EndFigure(D2D1_FIGURE_END_CLOSED);
        pSink->Close();
        
        // 填充多边形
        pBrush->SetColor(color);
        pRT->FillGeometry(pPathGeometry, pBrush);
        
        // 清理
        pSink->Release();
        pPathGeometry->Release();
        pFactory->Release();
    }
    
    // 使用D2D绘制中点法/Bresenham法的像素点
    static void DrawPixels(ID2D1HwndRenderTarget* pRT, ID2D1SolidColorBrush* pBrush,
                          const std::vector<D2D1_POINT_2F>& pixels, D2D1_COLOR_F color) {
        pBrush->SetColor(color);
        
        // 使用小矩形模拟像素
        for (const auto& p : pixels) {
            D2D1_RECT_F rect = D2D1::RectF(p.x - 0.5f, p.y - 0.5f, p.x + 0.5f, p.y + 0.5f);
            pRT->FillRectangle(rect, pBrush);
        }
    }
};
