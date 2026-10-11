#pragma once
#include "framework.h"
#include <vector>
#include <algorithm>
#include <cmath>
#include <list>
#include <set>

// ==================== 多边形自相交检测 ====================
class PolygonUtils {
public:
    // 检测两条线段是否相交
    static bool SegmentsIntersect(D2D1_POINT_2F p1, D2D1_POINT_2F p2, 
                                   D2D1_POINT_2F p3, D2D1_POINT_2F p4,
                                   D2D1_POINT_2F* intersection = nullptr) {
        float d1 = CrossProduct(p3, p4, p1);
        float d2 = CrossProduct(p3, p4, p2);
        float d3 = CrossProduct(p1, p2, p3);
        float d4 = CrossProduct(p1, p2, p4);
        
        if (((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) &&
            ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0))) {
            if (intersection) {
                float t = d1 / (d1 - d2);
                intersection->x = p1.x + t * (p2.x - p1.x);
                intersection->y = p1.y + t * (p2.y - p1.y);
            }
            return true;
        }
        
        // 检查共线情况
        if (d1 == 0 && OnSegment(p3, p1, p4)) { if (intersection) *intersection = p1; return true; }
        if (d2 == 0 && OnSegment(p3, p2, p4)) { if (intersection) *intersection = p2; return true; }
        if (d3 == 0 && OnSegment(p1, p3, p2)) { if (intersection) *intersection = p3; return true; }
        if (d4 == 0 && OnSegment(p1, p4, p2)) { if (intersection) *intersection = p4; return true; }
        
        return false;
    }
    
    // 检测多边形是否自相交
    static bool IsSelfIntersecting(const std::vector<D2D1_POINT_2F>& polygon,
                                    std::vector<D2D1_POINT_2F>* intersections = nullptr) {
        if (polygon.size() < 4) return false;
        
        bool hasIntersection = false;
        size_t n = polygon.size();
        
        for (size_t i = 0; i < n; i++) {
            D2D1_POINT_2F p1 = polygon[i];
            D2D1_POINT_2F p2 = polygon[(i + 1) % n];
            
            // 检查与非相邻边的交点
            for (size_t j = i + 2; j < n; j++) {
                // 跳过相邻边
                if (i == 0 && j == n - 1) continue;
                
                D2D1_POINT_2F p3 = polygon[j];
                D2D1_POINT_2F p4 = polygon[(j + 1) % n];
                
                D2D1_POINT_2F intersection;
                if (SegmentsIntersect(p1, p2, p3, p4, &intersection)) {
                    hasIntersection = true;
                    if (intersections) {
                        intersections->push_back(intersection);
                    }
                }
            }
        }
        
        return hasIntersection;
    }
    
    // 计算多边形面积（带符号，可判断方向）
    static float SignedArea(const std::vector<D2D1_POINT_2F>& polygon) {
        float area = 0;
        size_t n = polygon.size();
        for (size_t i = 0; i < n; i++) {
            size_t j = (i + 1) % n;
            area += polygon[i].x * polygon[j].y;
            area -= polygon[j].x * polygon[i].y;
        }
        return area / 2.0f;
    }
    
    // 判断多边形是否为顺时针方向
    static bool IsClockwise(const std::vector<D2D1_POINT_2F>& polygon) {
        return SignedArea(polygon) < 0;
    }
    
    // 判断点是否在多边形内部（射线法）
    static bool PointInPolygon(D2D1_POINT_2F point, const std::vector<D2D1_POINT_2F>& polygon) {
        int count = 0;
        size_t n = polygon.size();
        
        for (size_t i = 0; i < n; i++) {
            D2D1_POINT_2F p1 = polygon[i];
            D2D1_POINT_2F p2 = polygon[(i + 1) % n];
            
            if ((p1.y <= point.y && p2.y > point.y) || (p2.y <= point.y && p1.y > point.y)) {
                float x = p1.x + (point.y - p1.y) / (p2.y - p1.y) * (p2.x - p1.x);
                if (point.x < x) count++;
            }
        }
        
        return (count % 2) == 1;
    }
    
    // 分解自相交多边形为简单多边形
    static std::vector<std::vector<D2D1_POINT_2F>> DecomposeSelfIntersecting(
        const std::vector<D2D1_POINT_2F>& polygon) {
        
        std::vector<std::vector<D2D1_POINT_2F>> result;
        
        if (!IsSelfIntersecting(polygon)) {
            result.push_back(polygon);
            return result;
        }
        
        // 收集所有交点和原始顶点
        struct Vertex {
            D2D1_POINT_2F point;
            int edgeIndex;      // 所在边的索引
            float t;            // 在边上的参数位置
            bool isIntersection;
        };
        
        std::vector<Vertex> vertices;
        size_t n = polygon.size();
        
        // 添加原始顶点
        for (size_t i = 0; i < n; i++) {
            vertices.push_back({polygon[i], (int)i, 0.0f, false});
        }
        
        // 查找所有交点
        for (size_t i = 0; i < n; i++) {
            D2D1_POINT_2F p1 = polygon[i];
            D2D1_POINT_2F p2 = polygon[(i + 1) % n];
            
            for (size_t j = i + 2; j < n; j++) {
                if (i == 0 && j == n - 1) continue;
                
                D2D1_POINT_2F p3 = polygon[j];
                D2D1_POINT_2F p4 = polygon[(j + 1) % n];
                
                D2D1_POINT_2F intersection;
                if (SegmentsIntersect(p1, p2, p3, p4, &intersection)) {
                    float t1 = Distance(p1, intersection) / Distance(p1, p2);
                    float t2 = Distance(p3, intersection) / Distance(p3, p4);
                    vertices.push_back({intersection, (int)i, t1, true});
                    vertices.push_back({intersection, (int)j, t2, true});
                }
            }
        }
        
        // 简化处理：返回原始多边形
        // 完整的分解算法较复杂，这里返回原始多边形
        result.push_back(polygon);
        return result;
    }
    
private:
    static float CrossProduct(D2D1_POINT_2F o, D2D1_POINT_2F a, D2D1_POINT_2F b) {
        return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
    }
    
    static bool OnSegment(D2D1_POINT_2F p, D2D1_POINT_2F q, D2D1_POINT_2F r) {
        return q.x <= max(p.x, r.x) && q.x >= min(p.x, r.x) &&
               q.y <= max(p.y, r.y) && q.y >= min(p.y, r.y);
    }
    
    static float Distance(D2D1_POINT_2F p1, D2D1_POINT_2F p2) {
        float dx = p2.x - p1.x;
        float dy = p2.y - p1.y;
        return sqrt(dx * dx + dy * dy);
    }
};

// ==================== Liang-Barsky 直线裁剪算法 ====================
class LiangBarskyClipper {
public:
    // Liang-Barsky 直线裁剪算法
    // 输入: 直线的两个端点 (x1,y1) 和 (x2,y2), 裁剪窗口 (xmin,ymin,xmax,ymax)
    // 输出: 如果直线与窗口相交,返回true并更新端点坐标;否则返回false
    static bool ClipLine(float& x1, float& y1, float& x2, float& y2,
                        float xmin, float ymin, float xmax, float ymax) {
        float dx = x2 - x1;
        float dy = y2 - y1;
        float t_enter = 0.0f;  // 进入参数
        float t_leave = 1.0f;  // 离开参数
        
        // 检查四个边界
        float p[4] = { -dx, dx, -dy, dy };
        float q[4] = { x1 - xmin, xmax - x1, y1 - ymin, ymax - y1 };
        
        for (int i = 0; i < 4; i++) {
            if (p[i] == 0) {
                // 直线平行于边界
                if (q[i] < 0) {
                    // 直线在边界外
                    return false;
                }
            } else {
                float t = q[i] / p[i];
                if (p[i] < 0) {
                    // 从外到内
                    t_enter = max(t_enter, t);
                } else {
                    // 从内到外
                    t_leave = min(t_leave, t);
                }
            }
        }
        
        // 检查是否有交集
        if (t_enter > t_leave) {
            return false;
        }
        
        // 计算裁剪后的端点
        float new_x1 = x1 + t_enter * dx;
        float new_y1 = y1 + t_enter * dy;
        float new_x2 = x1 + t_leave * dx;
        float new_y2 = y1 + t_leave * dy;
        
        x1 = new_x1;
        y1 = new_y1;
        x2 = new_x2;
        y2 = new_y2;
        
        return true;
    }
};

// ==================== Sutherland-Hodgman 多边形裁剪算法 ====================
class SutherlandHodgmanClipper {
public:
    // Sutherland-Hodgman 多边形裁剪算法
    // 输入: 多边形顶点列表, 裁剪窗口
    // 输出: 裁剪后的多边形顶点列表
    static std::vector<D2D1_POINT_2F> ClipPolygon(
        const std::vector<D2D1_POINT_2F>& polygon,
        float xmin, float ymin, float xmax, float ymax) {
        
        if (polygon.size() < 3) return std::vector<D2D1_POINT_2F>();
        
        std::vector<D2D1_POINT_2F> output = polygon;
        
        // 依次对四条边界进行裁剪
        output = ClipAgainstEdge(output, xmin, ymin, xmax, ymin, 0);  // 下边界
        output = ClipAgainstEdge(output, xmax, ymin, xmax, ymax, 1);  // 右边界
        output = ClipAgainstEdge(output, xmax, ymax, xmin, ymax, 2);  // 上边界
        output = ClipAgainstEdge(output, xmin, ymax, xmin, ymin, 3);  // 左边界
        
        return output;
    }
    
private:
    // 对单条边界进行裁剪
    // edge: 0=下, 1=右, 2=上, 3=左
    static std::vector<D2D1_POINT_2F> ClipAgainstEdge(
        const std::vector<D2D1_POINT_2F>& input,
        float x1, float y1, float x2, float y2, int edge) {
        
        std::vector<D2D1_POINT_2F> output;
        if (input.empty()) return output;
        
        for (size_t i = 0; i < input.size(); i++) {
            D2D1_POINT_2F current = input[i];
            D2D1_POINT_2F next = input[(i + 1) % input.size()];
            
            bool currentInside = IsInside(current, x1, y1, x2, y2, edge);
            bool nextInside = IsInside(next, x1, y1, x2, y2, edge);
            
            if (currentInside && nextInside) {
                // 两点都在内侧,输出next
                output.push_back(next);
            } else if (currentInside && !nextInside) {
                // current在内侧,next在外侧,输出交点
                D2D1_POINT_2F intersection = ComputeIntersection(current, next, x1, y1, x2, y2, edge);
                output.push_back(intersection);
            } else if (!currentInside && nextInside) {
                // current在外侧,next在内侧,输出交点和next
                D2D1_POINT_2F intersection = ComputeIntersection(current, next, x1, y1, x2, y2, edge);
                output.push_back(intersection);
                output.push_back(next);
            }
            // 两点都在外侧,不输出
        }
        
        return output;
    }
    
    // 判断点是否在边界内侧
    static bool IsInside(D2D1_POINT_2F p, float x1, float y1, float x2, float y2, int edge) {
        switch (edge) {
            case 0: return p.y >= y1;  // 下边界
            case 1: return p.x <= x1;  // 右边界
            case 2: return p.y <= y1;  // 上边界
            case 3: return p.x >= x1;  // 左边界
            default: return false;
        }
    }
    
    // 计算线段与边界的交点
    static D2D1_POINT_2F ComputeIntersection(
        D2D1_POINT_2F p1, D2D1_POINT_2F p2,
        float x1, float y1, float x2, float y2, int edge) {
        
        D2D1_POINT_2F intersection = p1; // 默认值
        
        switch (edge) {
            case 0: // 下边界 (水平线 y = y1)
            case 2: // 上边界 (水平线 y = y1)
                {
                    float dy = p2.y - p1.y;
                    if (fabs(dy) > 1e-10f) {
                        float t = (y1 - p1.y) / dy;
                        intersection.x = p1.x + t * (p2.x - p1.x);
                        intersection.y = y1;
                    }
                }
                break;
            case 1: // 右边界 (垂直线 x = x1)
            case 3: // 左边界 (垂直线 x = x1)
                {
                    float dx = p2.x - p1.x;
                    if (fabs(dx) > 1e-10f) {
                        float t = (x1 - p1.x) / dx;
                        intersection.x = x1;
                        intersection.y = p1.y + t * (p2.y - p1.y);
                    }
                }
                break;
        }
        
        return intersection;
    }
};

// ==================== Weiler-Atherton 多边形裁剪算法 ====================
// 输入：主多边形（被裁剪多边形）顶点列表，裁剪多边形顶点列表
// 输出：裁剪后的多边形列表（可能有多个）
// 
// 算法原理：
// Weiler-Atherton算法基于交点链表，可以处理凹多边形、自相交多边形和带孔洞的多边形。
// 核心思想：
// 1. 计算两个多边形边界的所有交点
// 2. 将交点插入到两个多边形的顶点链表中
// 3. 标记每个交点是"进入点"还是"离开点"
// 4. 从进入点开始，沿着主多边形边界行走，遇到交点时切换到裁剪多边形
// 5. 重复直到回到起点，形成一个裁剪后的多边形
//
// 交点分类：
// - 进入点：从裁剪多边形外部进入内部的交点
// - 离开点：从裁剪多边形内部离开到外部的交点

class WeilerAthertonClipper {
private:
    // 顶点节点结构
    struct Vertex {
        D2D1_POINT_2F pt;       // 顶点坐标
        float t;                 // 在边上的参数位置 [0,1]
        bool isIntersection;     // 是否为交点
        bool isEntering;         // true=进入点, false=离开点
        bool visited;            // 遍历时是否已访问
        int neighbor;            // 对应另一个链表中的索引（交点才有效）
        
        Vertex() : t(0), isIntersection(false), isEntering(false), visited(false), neighbor(-1) {
            pt = {0, 0};
        }
    };
    
    // 计算两条线段的交点
    // 返回：是否相交（不包括端点）
    // ta, tb：交点在两条线段上的参数位置
    static bool ComputeIntersection(
        D2D1_POINT_2F a1, D2D1_POINT_2F a2,  // 线段A
        D2D1_POINT_2F b1, D2D1_POINT_2F b2,  // 线段B
        float& ta, float& tb, D2D1_POINT_2F& pt) {
        
        float dax = a2.x - a1.x, day = a2.y - a1.y;
        float dbx = b2.x - b1.x, dby = b2.y - b1.y;
        float denom = dax * dby - day * dbx;
        
        // 平行或共线
        if (fabs(denom) < 1e-10f) return false;
        
        float dx = b1.x - a1.x, dy = b1.y - a1.y;
        ta = (dx * dby - dy * dbx) / denom;
        tb = (dx * day - dy * dax) / denom;
        
        // 交点必须在两条线段内部（不包括端点）
        const float eps = 1e-7f;
        if (ta > eps && ta < 1.0f - eps && tb > eps && tb < 1.0f - eps) {
            pt.x = a1.x + ta * dax;
            pt.y = a1.y + ta * day;
            return true;
        }
        return false;
    }
    
    // 判断点是否在多边形内部（射线法）
    static bool PointInsidePolygon(D2D1_POINT_2F pt, const std::vector<D2D1_POINT_2F>& polygon) {
        int count = 0;
        size_t n = polygon.size();
        for (size_t i = 0; i < n; i++) {
            D2D1_POINT_2F p1 = polygon[i];
            D2D1_POINT_2F p2 = polygon[(i + 1) % n];
            if ((p1.y <= pt.y && p2.y > pt.y) || (p2.y <= pt.y && p1.y > pt.y)) {
                float x = p1.x + (pt.y - p1.y) / (p2.y - p1.y) * (p2.x - p1.x);
                if (pt.x < x) count++;
            }
        }
        return (count % 2) == 1;
    }
    
public:
    // ========== 核心算法：Weiler-Atherton多边形裁剪 ==========
    // 输入：subject - 主多边形（被裁剪多边形）
    //       clipPoly - 裁剪多边形
    // 输出：裁剪后的多边形列表（可能有多个）
    static std::vector<std::vector<D2D1_POINT_2F>> ClipPolygons(
        const std::vector<D2D1_POINT_2F>& subject,
        const std::vector<D2D1_POINT_2F>& clipPoly) {
        
        std::vector<std::vector<D2D1_POINT_2F>> result;
        if (subject.size() < 3 || clipPoly.size() < 3) return result;
        
        // ===== 步骤1：计算所有交点 =====
        struct IntersectionInfo {
            D2D1_POINT_2F pt;
            int subjEdge;    // 主多边形边索引
            int clipEdge;    // 裁剪多边形边索引
            float tSubj;     // 在主多边形边上的参数
            float tClip;     // 在裁剪多边形边上的参数
            bool entering;   // 是否为进入点
        };
        std::vector<IntersectionInfo> intersections;
        
        size_t sn = subject.size();
        size_t cn = clipPoly.size();
        
        for (size_t i = 0; i < sn; i++) {
            D2D1_POINT_2F s1 = subject[i];
            D2D1_POINT_2F s2 = subject[(i + 1) % sn];
            
            for (size_t j = 0; j < cn; j++) {
                D2D1_POINT_2F c1 = clipPoly[j];
                D2D1_POINT_2F c2 = clipPoly[(j + 1) % cn];
                
                float ts, tc;
                D2D1_POINT_2F pt;
                if (ComputeIntersection(s1, s2, c1, c2, ts, tc, pt)) {
                    IntersectionInfo info;
                    info.pt = pt;
                    info.subjEdge = (int)i;
                    info.clipEdge = (int)j;
                    info.tSubj = ts;
                    info.tClip = tc;
                    
                    // 判断进入/离开：检查交点后一小段是否在裁剪多边形内
                    D2D1_POINT_2F afterPt = {
                        s1.x + (ts + 0.001f) * (s2.x - s1.x),
                        s1.y + (ts + 0.001f) * (s2.y - s1.y)
                    };
                    info.entering = PointInsidePolygon(afterPt, clipPoly);
                    
                    intersections.push_back(info);
                }
            }
        }
        
        // 特殊情况：无交点
        if (intersections.empty()) {
            // 检查主多边形是否完全在裁剪多边形内
            if (PointInsidePolygon(subject[0], clipPoly)) {
                result.push_back(subject);
            }
            // 检查裁剪多边形是否完全在主多边形内
            else if (PointInsidePolygon(clipPoly[0], subject)) {
                result.push_back(clipPoly);
            }
            return result;
        }
        
        // ===== 步骤2：构建主多边形顶点链表（插入交点） =====
        std::vector<Vertex> subjList;
        for (size_t i = 0; i < sn; i++) {
            Vertex v;
            v.pt = subject[i];
            v.isIntersection = false;
            subjList.push_back(v);
            
            // 收集该边上的所有交点，按参数排序
            std::vector<std::pair<float, IntersectionInfo*>> edgeInters;
            for (auto& inter : intersections) {
                if (inter.subjEdge == (int)i) {
                    edgeInters.push_back({inter.tSubj, &inter});
                }
            }
            std::sort(edgeInters.begin(), edgeInters.end(),
                [](auto& a, auto& b) { return a.first < b.first; });
            
            // 按顺序插入交点
            for (auto& ei : edgeInters) {
                Vertex iv;
                iv.pt = ei.second->pt;
                iv.t = ei.first;
                iv.isIntersection = true;
                iv.isEntering = ei.second->entering;
                subjList.push_back(iv);
            }
        }
        
        // ===== 步骤3：构建裁剪多边形顶点链表（插入交点） =====
        std::vector<Vertex> clipList;
        for (size_t j = 0; j < cn; j++) {
            Vertex v;
            v.pt = clipPoly[j];
            v.isIntersection = false;
            clipList.push_back(v);
            
            std::vector<std::pair<float, IntersectionInfo*>> edgeInters;
            for (auto& inter : intersections) {
                if (inter.clipEdge == (int)j) {
                    edgeInters.push_back({inter.tClip, &inter});
                }
            }
            std::sort(edgeInters.begin(), edgeInters.end(),
                [](auto& a, auto& b) { return a.first < b.first; });
            
            for (auto& ei : edgeInters) {
                Vertex iv;
                iv.pt = ei.second->pt;
                iv.t = ei.first;
                iv.isIntersection = true;
                iv.isEntering = ei.second->entering;
                clipList.push_back(iv);
            }
        }
        
        // ===== 步骤4：建立交点之间的双向链接 =====
        for (size_t i = 0; i < subjList.size(); i++) {
            if (subjList[i].isIntersection) {
                for (size_t j = 0; j < clipList.size(); j++) {
                    if (clipList[j].isIntersection) {
                        float dx = subjList[i].pt.x - clipList[j].pt.x;
                        float dy = subjList[i].pt.y - clipList[j].pt.y;
                        if (dx*dx + dy*dy < 1e-4f) {
                            subjList[i].neighbor = (int)j;
                            clipList[j].neighbor = (int)i;
                            break;
                        }
                    }
                }
            }
        }
        
        // ===== 步骤5：从进入点开始遍历，生成裁剪结果 =====
        // 对于凹多边形，可能产生多个独立的裁剪区域
        // 每个区域从一个未访问的进入点开始遍历
        // 
        // 关键：只标记作为"起点"使用的进入点为visited
        // 中间经过的进入点不标记，这样可以作为其他多边形的起点
        
        // 收集所有进入点的索引
        std::vector<size_t> enteringPoints;
        for (size_t i = 0; i < subjList.size(); i++) {
            if (subjList[i].isIntersection && subjList[i].isEntering) {
                enteringPoints.push_back(i);
            }
        }
        
        // 为每个进入点创建独立的visited标记
        std::vector<bool> usedAsStart(subjList.size(), false);
        
        for (size_t epIdx = 0; epIdx < enteringPoints.size(); epIdx++) {
            size_t startIdx = enteringPoints[epIdx];
            
            // 如果这个进入点已经作为起点使用过，跳过
            if (usedAsStart[startIdx]) continue;
            
            // 创建本次遍历的局部visited标记
            std::vector<bool> localVisitedS(subjList.size(), false);
            std::vector<bool> localVisitedC(clipList.size(), false);
            
            std::vector<D2D1_POINT_2F> polygon;
            int currentIdx = (int)startIdx;
            bool onSubject = true;
            int maxIterations = (int)(subjList.size() + clipList.size()) * 3;
            bool firstStep = true;
            
            for (int iter = 0; iter < maxIterations; iter++) {
                if (onSubject) {
                    // 检查是否回到起点（非首次）
                    if (!firstStep && currentIdx == (int)startIdx) break;
                    firstStep = false;
                    
                    Vertex& v = subjList[currentIdx];
                    polygon.push_back(v.pt);
                    localVisitedS[currentIdx] = true;
                    
                    // 如果是离开点，切换到裁剪多边形
                    if (v.isIntersection && !v.isEntering && v.neighbor >= 0) {
                        localVisitedC[v.neighbor] = true;
                        currentIdx = (v.neighbor + 1) % (int)clipList.size();
                        onSubject = false;
                    } else {
                        currentIdx = (currentIdx + 1) % (int)subjList.size();
                    }
                } else {
                    Vertex& v = clipList[currentIdx];
                    
                    // 如果是交点且对应subject上的进入点，切换回主多边形
                    if (v.isIntersection && v.neighbor >= 0 && subjList[v.neighbor].isEntering) {
                        // 检查是否回到起点
                        if (v.neighbor == (int)startIdx) break;
                        
                        localVisitedC[currentIdx] = true;
                        currentIdx = v.neighbor;
                        onSubject = true;
                    } else {
                        polygon.push_back(v.pt);
                        localVisitedC[currentIdx] = true;
                        currentIdx = (currentIdx + 1) % (int)clipList.size();
                    }
                }
            }
            
            // 如果成功形成多边形
            if (polygon.size() >= 3) {
                // 标记本次遍历中所有作为"起点或中转点"的进入点
                // 这样可以避免从同一个进入点重复开始
                for (size_t i = 0; i < subjList.size(); i++) {
                    if (localVisitedS[i] && subjList[i].isIntersection && subjList[i].isEntering) {
                        usedAsStart[i] = true;
                    }
                }
                
                // 去除重复点
                std::vector<D2D1_POINT_2F> cleanPoly;
                for (const auto& pt : polygon) {
                    if (cleanPoly.empty()) {
                        cleanPoly.push_back(pt);
                    } else {
                        float dx = pt.x - cleanPoly.back().x;
                        float dy = pt.y - cleanPoly.back().y;
                        if (dx*dx + dy*dy > 1e-4f) {
                            cleanPoly.push_back(pt);
                        }
                    }
                }
                // 检查首尾是否重复
                if (cleanPoly.size() > 1) {
                    float dx = cleanPoly.front().x - cleanPoly.back().x;
                    float dy = cleanPoly.front().y - cleanPoly.back().y;
                    if (dx*dx + dy*dy < 1e-4f) {
                        cleanPoly.pop_back();
                    }
                }
                if (cleanPoly.size() >= 3) {
                    // 验证多边形的点是否有效
                    bool valid = true;
                    for (const auto& pt : cleanPoly) {
                        if (isnan(pt.x) || isnan(pt.y) || 
                            isinf(pt.x) || isinf(pt.y)) {
                            valid = false;
                            break;
                        }
                    }
                    if (valid) {
                        result.push_back(cleanPoly);
                    }
                }
            }
        }
        
        return result;
    }
    
    // ========== 便捷接口：使用矩形裁剪窗口 ==========
    static std::vector<std::vector<D2D1_POINT_2F>> ClipPolygonWithHoles(
        const std::vector<D2D1_POINT_2F>& subject,
        float xmin, float ymin, float xmax, float ymax) {
        
        // 构建矩形裁剪窗口（逆时针方向）
        std::vector<D2D1_POINT_2F> clipRect = {
            D2D1::Point2F(xmin, ymin),
            D2D1::Point2F(xmax, ymin),
            D2D1::Point2F(xmax, ymax),
            D2D1::Point2F(xmin, ymax)
        };
        
        return ClipPolygons(subject, clipRect);
    }
    
    // 简单接口：返回面积最大的裁剪结果
    static std::vector<D2D1_POINT_2F> ClipPolygon(
        const std::vector<D2D1_POINT_2F>& polygon,
        float xmin, float ymin, float xmax, float ymax) {
        
        auto results = ClipPolygonWithHoles(polygon, xmin, ymin, xmax, ymax);
        
        if (results.empty()) return std::vector<D2D1_POINT_2F>();
        
        // 返回面积最大的多边形
        std::vector<D2D1_POINT_2F>* largest = &results[0];
        float maxArea = fabs(PolygonUtils::SignedArea(*largest));
        
        for (size_t i = 1; i < results.size(); i++) {
            float area = fabs(PolygonUtils::SignedArea(results[i]));
            if (area > maxArea) {
                maxArea = area;
                largest = &results[i];
            }
        }
        
        return *largest;
    }
    
    // 返回所有裁剪结果
    static std::vector<std::vector<D2D1_POINT_2F>> ClipPolygonMultiple(
        const std::vector<D2D1_POINT_2F>& polygon,
        float xmin, float ymin, float xmax, float ymax) {
        return ClipPolygonWithHoles(polygon, xmin, ymin, xmax, ymax);
    }
};

// ==================== 带孔洞的多边形结构 ====================
struct PolygonWithHoles {
    std::vector<D2D1_POINT_2F> outer;           // 外边界
    std::vector<std::vector<D2D1_POINT_2F>> holes;  // 孔洞列表
    
    // 检测点是否在多边形内（考虑孔洞）
    bool ContainsPoint(D2D1_POINT_2F point) const {
        if (!PolygonUtils::PointInPolygon(point, outer)) {
            return false;
        }
        for (const auto& hole : holes) {
            if (PolygonUtils::PointInPolygon(point, hole)) {
                return false;
            }
        }
        return true;
    }
    
    // 裁剪带孔洞的多边形
    static PolygonWithHoles Clip(const PolygonWithHoles& polygon,
                                  float xmin, float ymin, float xmax, float ymax) {
        PolygonWithHoles result;
        
        // 裁剪外边界
        auto outerResults = WeilerAthertonClipper::ClipPolygonWithHoles(
            polygon.outer, xmin, ymin, xmax, ymax);
        
        if (outerResults.empty()) return result;
        
        // 取最大的作为外边界
        result.outer = outerResults[0];
        float maxArea = fabs(PolygonUtils::SignedArea(result.outer));
        for (size_t i = 1; i < outerResults.size(); i++) {
            float area = fabs(PolygonUtils::SignedArea(outerResults[i]));
            if (area > maxArea) {
                maxArea = area;
                result.outer = outerResults[i];
            }
        }
        
        // 裁剪每个孔洞
        for (const auto& hole : polygon.holes) {
            auto holeResults = WeilerAthertonClipper::ClipPolygonWithHoles(
                hole, xmin, ymin, xmax, ymax);
            for (const auto& h : holeResults) {
                // 检查裁剪后的孔洞是否仍在外边界内
                if (h.size() >= 3) {
                    D2D1_POINT_2F center = {0, 0};
                    for (const auto& p : h) {
                        center.x += p.x;
                        center.y += p.y;
                    }
                    center.x /= h.size();
                    center.y /= h.size();
                    
                    if (PolygonUtils::PointInPolygon(center, result.outer)) {
                        result.holes.push_back(h);
                    }
                }
            }
        }
        
        return result;
    }
};
