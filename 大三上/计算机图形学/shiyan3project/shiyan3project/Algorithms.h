#pragma once
#include "framework.h"
#include <queue>
#include <stack>
#include <set>

// Experiment 3 Algorithms

// Midpoint Line Algorithm
class MidpointLine {
public:
    static std::vector<POINT> DrawLine(int x1, int y1, int x2, int y2) {
        std::vector<POINT> pixels;
        int dx = abs(x2 - x1);
        int dy = abs(y2 - y1);
        int sx = (x1 < x2) ? 1 : -1;
        int sy = (y1 < y2) ? 1 : -1;
        
        if (dx > dy) {
            // 斜率 < 1
            int d = 2 * dy - dx;
            int y = y1;
            for (int x = x1; sx > 0 ? x <= x2 : x >= x2; x += sx) {
                pixels.push_back({x, y});
                if (d > 0) {
                    y += sy;
                    d += 2 * (dy - dx);
                } else {
                    d += 2 * dy;
                }
            }
        } else {
            // 斜率 >= 1
            int d = 2 * dx - dy;
            int x = x1;
            for (int y = y1; sy > 0 ? y <= y2 : y >= y2; y += sy) {
                pixels.push_back({x, y});
                if (d > 0) {
                    x += sx;
                    d += 2 * (dx - dy);
                } else {
                    d += 2 * dx;
                }
            }
        }
        return pixels;
    }
};

// (1) Bresenham画线法
class BresenhamLine {
public:
    static std::vector<POINT> DrawLine(int x1, int y1, int x2, int y2) {
        std::vector<POINT> pixels;
        int dx = abs(x2 - x1);
        int dy = abs(y2 - y1);
        int sx = (x1 < x2) ? 1 : -1;
        int sy = (y1 < y2) ? 1 : -1;
        int err = dx - dy;
        
        int x = x1, y = y1;
        while (true) {
            pixels.push_back({x, y});
            
            if (x == x2 && y == y2) break;
            
            int e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x += sx;
            }
            if (e2 < dx) {
                err += dx;
                y += sy;
            }
        }
        return pixels;
    }
};

// (2) 中点画圆法
class MidpointCircle {
public:
    static std::vector<POINT> DrawCircle(int xc, int yc, int radius) {
        std::vector<POINT> pixels;
        int x = 0;
        int y = radius;
        int d = 1 - radius;
        
        auto addSymmetricPoints = [&](int x, int y) {
            pixels.push_back({xc + x, yc + y});
            pixels.push_back({xc - x, yc + y});
            pixels.push_back({xc + x, yc - y});
            pixels.push_back({xc - x, yc - y});
            pixels.push_back({xc + y, yc + x});
            pixels.push_back({xc - y, yc + x});
            pixels.push_back({xc + y, yc - x});
            pixels.push_back({xc - y, yc - x});
        };
        
        addSymmetricPoints(x, y);
        
        while (x < y) {
            if (d < 0) {
                d += 2 * x + 3;
            } else {
                d += 2 * (x - y) + 5;
                y--;
            }
            x++;
            addSymmetricPoints(x, y);
        }
        
        return pixels;
    }
};

// (2) Bresenham画圆法
class BresenhamCircle {
public:
    static std::vector<POINT> DrawCircle(int xc, int yc, int radius) {
        std::vector<POINT> pixels;
        int x = 0;
        int y = radius;
        int d = 3 - 2 * radius;
        
        auto addSymmetricPoints = [&](int x, int y) {
            pixels.push_back({xc + x, yc + y});
            pixels.push_back({xc - x, yc + y});
            pixels.push_back({xc + x, yc - y});
            pixels.push_back({xc - x, yc - y});
            pixels.push_back({xc + y, yc + x});
            pixels.push_back({xc - y, yc + x});
            pixels.push_back({xc + y, yc - x});
            pixels.push_back({xc - y, yc - x});
        };
        
        addSymmetricPoints(x, y);
        
        while (x <= y) {
            if (d < 0) {
                d += 4 * x + 6;
            } else {
                d += 4 * (x - y) + 10;
                y--;
            }
            x++;
            if (x <= y) {
                addSymmetricPoints(x, y);
            }
        }
        
        return pixels;
    }
};

// (3) 扫描线填充法 - 用于绘制粗线
class ScanlineFill {
public:
    // 绘制指定宽度的线段
    static void DrawThickLine(HDC hdc, int x1, int y1, int x2, int y2, int width, COLORREF color) {
        if (width <= 1) {
            // 使用Bresenham画细线
            auto pixels = BresenhamLine::DrawLine(x1, y1, x2, y2);
            for (const auto& p : pixels) {
                SetPixel(hdc, p.x, p.y, color);
            }
            return;
        }
        
        // 计算线段的垂直方向
        float dx = (float)(x2 - x1);
        float dy = (float)(y2 - y1);
        float len = sqrt(dx * dx + dy * dy);
        if (len < 0.001f) return;
        
        float perpX = -dy / len * (width / 2.0f);
        float perpY = dx / len * (width / 2.0f);
        
        // 计算粗线的四个顶点
        POINT poly[4];
        poly[0] = {(LONG)(x1 + perpX), (LONG)(y1 + perpY)};
        poly[1] = {(LONG)(x1 - perpX), (LONG)(y1 - perpY)};
        poly[2] = {(LONG)(x2 - perpX), (LONG)(y2 - perpY)};
        poly[3] = {(LONG)(x2 + perpX), (LONG)(y2 + perpY)};
        
        // 使用扫描线填充多边形
        FillPolygonScanline(hdc, poly, 4, color);
    }
    
    // 扫描线填充多边形
    static void FillPolygonScanline(HDC hdc, POINT* vertices, int count, COLORREF color) {
        if (count < 3) return;
        
        // 找到y的范围
        int minY = vertices[0].y, maxY = vertices[0].y;
        for (int i = 1; i < count; i++) {
            if (vertices[i].y < minY) minY = vertices[i].y;
            if (vertices[i].y > maxY) maxY = vertices[i].y;
        }
        
        // 对每条扫描线
        for (int y = minY; y <= maxY; y++) {
            std::vector<int> intersections;
            
            // 找到与扫描线的交点
            for (int i = 0; i < count; i++) {
                int j = (i + 1) % count;
                int y1 = vertices[i].y;
                int y2 = vertices[j].y;
                
                if ((y1 <= y && y < y2) || (y2 <= y && y < y1)) {
                    int x1 = vertices[i].x;
                    int x2 = vertices[j].x;
                    int x = x1 + (y - y1) * (x2 - x1) / (y2 - y1);
                    intersections.push_back(x);
                }
            }
            
            // 排序交点
            std::sort(intersections.begin(), intersections.end());
            
            // 填充交点对之间的像素
            for (size_t i = 0; i + 1 < intersections.size(); i += 2) {
                for (int x = intersections[i]; x <= intersections[i + 1]; x++) {
                    SetPixel(hdc, x, y, color);
                }
            }
        }
    }
};

// (4) 线型处理
class LineStyle {
public:
    enum Style {
        SOLID,      // 实线
        DASH,       // 虚线
        DOT,        // 点线
        DASHDOT     // 点划线
    };
    
    static void DrawStyledLine(HDC hdc, int x1, int y1, int x2, int y2, Style style, COLORREF color) {
        auto pixels = BresenhamLine::DrawLine(x1, y1, x2, y2);
        
        int pattern[] = {0};
        int patternLen = 1;
        
        switch (style) {
            case SOLID:
                pattern[0] = 1;
                patternLen = 1;
                break;
            case DASH:
                {
                    static int dashPattern[] = {1, 1, 1, 1, 0, 0, 0, 0};
                    for (size_t i = 0; i < pixels.size(); i++) {
                        if (dashPattern[i % 8]) {
                            SetPixel(hdc, pixels[i].x, pixels[i].y, color);
                        }
                    }
                    return;
                }
            case DOT:
                {
                    static int dotPattern[] = {1, 0, 0};
                    for (size_t i = 0; i < pixels.size(); i++) {
                        if (dotPattern[i % 3]) {
                            SetPixel(hdc, pixels[i].x, pixels[i].y, color);
                        }
                    }
                    return;
                }
            case DASHDOT:
                {
                    static int dashDotPattern[] = {1, 1, 1, 0, 0, 1, 0, 0};
                    for (size_t i = 0; i < pixels.size(); i++) {
                        if (dashDotPattern[i % 8]) {
                            SetPixel(hdc, pixels[i].x, pixels[i].y, color);
                        }
                    }
                    return;
                }
        }
        
        // 默认实线
        for (const auto& p : pixels) {
            SetPixel(hdc, p.x, p.y, color);
        }
    }
};

// (5) 种子填充法（四连通）
class SeedFill {
public:
    static void Fill(HDC hdc, int x, int y, COLORREF fillColor, COLORREF boundaryColor) {
        COLORREF oldColor = GetPixel(hdc, x, y);
        if (oldColor == fillColor || oldColor == boundaryColor) return;
        
        std::queue<POINT> queue;
        queue.push({x, y});
        
        while (!queue.empty()) {
            POINT p = queue.front();
            queue.pop();
            
            COLORREF c = GetPixel(hdc, p.x, p.y);
            if (c == oldColor) {
                SetPixel(hdc, p.x, p.y, fillColor);
                
                queue.push({p.x + 1, p.y});
                queue.push({p.x - 1, p.y});
                queue.push({p.x, p.y + 1});
                queue.push({p.x, p.y - 1});
            }
        }
    }
};

// (5) 栅栏填充法（扫描线填充的改进版本）
class FenceFill {
public:
    static void Fill(HDC hdc, POINT* vertices, int count, COLORREF color) {
        ScanlineFill::FillPolygonScanline(hdc, vertices, count, color);
    }
};

// (6) Bezier曲线 - de Casteljau递推算法
class BezierCurve {
public:
    // de Casteljau递推算法计算Bezier曲线上的点
    static D2D1_POINT_2F DeCasteljau(const std::vector<D2D1_POINT_2F>& controlPoints, float t) {
        int n = (int)controlPoints.size();
        if (n == 0) return D2D1::Point2F(0, 0);
        if (n == 1) return controlPoints[0];
        
        std::vector<D2D1_POINT_2F> points = controlPoints;
        
        for (int r = 1; r < n; r++) {
            for (int i = 0; i < n - r; i++) {
                points[i].x = (1 - t) * points[i].x + t * points[i + 1].x;
                points[i].y = (1 - t) * points[i].y + t * points[i + 1].y;
            }
        }
        
        return points[0];
    }
    
    // 生成Bezier曲线的采样点
    static std::vector<D2D1_POINT_2F> GenerateCurve(const std::vector<D2D1_POINT_2F>& controlPoints, int samples = 100) {
        std::vector<D2D1_POINT_2F> curvePoints;
        
        for (int i = 0; i <= samples; i++) {
            float t = (float)i / samples;
            curvePoints.push_back(DeCasteljau(controlPoints, t));
        }
        
        return curvePoints;
    }
};
