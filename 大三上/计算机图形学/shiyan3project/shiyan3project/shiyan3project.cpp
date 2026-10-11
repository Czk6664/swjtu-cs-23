// shiyan3project.cpp : 实验3 - 图形学基本算法实现
// 基于实验2的绘图软件，添加：中点画线法、Bresenham画线法、中点画圆法、Bresenham画圆法
// 扫描线填充、线型修改、栅栏填充、种子填充、Bezier曲线(de Casteljau算法)

#include "framework.h"
#include "shiyan3project.h"
#include "ShapeImpl.h"
#include "Algorithms.h"
#include "SeedFillD2D.h"

#define MAX_LOADSTRING 100

// Global variables
HINSTANCE hInst;
WCHAR szTitle[MAX_LOADSTRING];
WCHAR szWindowClass[MAX_LOADSTRING];

// Direct2D resources
ID2D1Factory* g_pD2DFactory = nullptr;
ID2D1HwndRenderTarget* g_pRenderTarget = nullptr;
ID2D1SolidColorBrush* g_pBrush = nullptr;
IDWriteFactory* g_pDWriteFactory = nullptr;
IDWriteTextFormat* g_pTextFormat = nullptr;

// 种子填充结果位图列表（支持多次填充）
std::vector<ID2D1Bitmap*> g_seedFillBitmaps;

// Drawing state
ShapeType g_currentTool = ShapeType::NONE;
std::vector<std::shared_ptr<Shape>> g_shapes;
std::shared_ptr<Shape> g_currentShape = nullptr;
Shape* g_selectedShape = nullptr;
D2D1_POINT_2F g_startPoint;
D2D1_POINT_2F g_lastMousePos;
bool g_isDrawing = false;
bool g_isMoving = false;
bool g_isRotating = false;
bool g_isScaling = false;
int g_clickCount = 0;
std::vector<D2D1_POINT_2F> g_tempPoints;
std::wstring g_statusText;

// Scaling state
std::string g_backupShapeData;
float g_currentScaleFactor = 1.0f;

// Rotation state
std::string g_backupRotationData;
float g_currentRotationAngle = 0.0f;

// Geometry calculation mode
enum class CalcMode { NONE, INTERSECTION, PERPENDICULAR, CENTER, TANGENT };
CalcMode g_calcMode = CalcMode::NONE;
Shape* g_calcShape1 = nullptr;
Shape* g_calcShape2 = nullptr;
D2D1_POINT_2F g_calcPoint;

// Undo/Redo stacks
std::vector<std::vector<std::shared_ptr<Shape>>> g_undoStack;
std::vector<std::vector<std::shared_ptr<Shape>>> g_redoStack;
const size_t MAX_UNDO_STEPS = 50;

// ==================== 实验3 新增全局变量 ====================
// 线宽和线型设置
int g_lineWidth = 1;
LineStyleType g_lineStyle = LineStyleType::SOLID;
COLORREF g_fillColor = RGB(200, 220, 255);

// 算法选择（全局设置，用于新绘制的图形）
LineAlgorithm g_lineAlgorithm = LineAlgorithm::DIRECT2D;
CircleAlgorithm g_circleAlgorithm = CircleAlgorithm::DIRECT2D;

// Bezier曲线控制点
std::vector<D2D1_POINT_2F> g_bezierControlPoints;
bool g_drawingBezier = false;

// 填充模式
enum class FillMode { NONE, SEED, FENCE };
FillMode g_fillMode = FillMode::NONE;
std::vector<D2D1_POINT_2F> g_polygonPoints;

// 种子填充待处理标记
bool g_pendingSeedFill = false;
D2D1_POINT_2F g_seedFillPoint;

// 种子填充结果位图
ID2D1Bitmap* g_seedFillBitmap = nullptr;

// Function declarations
ATOM MyRegisterClass(HINSTANCE hInstance);
BOOL InitInstance(HINSTANCE, int);
LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK About(HWND, UINT, WPARAM, LPARAM);
HRESULT CreateDeviceResources(HWND hWnd);
void DiscardDeviceResources();
void OnPaint(HWND hWnd);
void OnLButtonDown(HWND hWnd, LPARAM lParam);
void OnLButtonUp(HWND hWnd, LPARAM lParam);
void OnMouseMove(HWND hWnd, LPARAM lParam);
void OnRButtonDown(HWND hWnd);
void SaveToFile(HWND hWnd);
void LoadFromFile(HWND hWnd);
void CalculateIntersections();
void DrawPerpendicular(D2D1_POINT_2F clickPoint, Line* line);
void ShowCenter(Circle* circle);
void DrawTangent(D2D1_POINT_2F point, Circle* circle);
void SaveStateToUndoStack();

int APIENTRY wWinMain(_In_ HINSTANCE hInstance,
                     _In_opt_ HINSTANCE hPrevInstance,
                     _In_ LPWSTR    lpCmdLine,
                     _In_ int       nCmdShow)
{
    UNREFERENCED_PARAMETER(hPrevInstance);
    UNREFERENCED_PARAMETER(lpCmdLine);

    // Initialize COM
    CoInitialize(nullptr);

    // Initialize Direct2D
    D2D1CreateFactory(D2D1_FACTORY_TYPE_SINGLE_THREADED, &g_pD2DFactory);
    DWriteCreateFactory(DWRITE_FACTORY_TYPE_SHARED, __uuidof(IDWriteFactory),
        reinterpret_cast<IUnknown**>(&g_pDWriteFactory));

    // Initialize global strings
    LoadStringW(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
    LoadStringW(hInstance, IDC_SHIYAN3PROJECT, szWindowClass, MAX_LOADSTRING);
    MyRegisterClass(hInstance);

    // Perform application initialization
    if (!InitInstance(hInstance, nCmdShow))
    {
        return FALSE;
    }

    HACCEL hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_SHIYAN3PROJECT));

    MSG msg;

    // Main message loop
    while (GetMessage(&msg, nullptr, 0, 0))
    {
        if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg))
        {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    // Clean up resources
    DiscardDeviceResources();
    if (g_pD2DFactory) g_pD2DFactory->Release();
    if (g_pDWriteFactory) g_pDWriteFactory->Release();
    CoUninitialize();

    return (int)msg.wParam;
}



//
//  Function: MyRegisterClass()
//
//  Purpose: Register window class.
//
ATOM MyRegisterClass(HINSTANCE hInstance)
{
    WNDCLASSEXW wcex;

    wcex.cbSize = sizeof(WNDCLASSEX);

    wcex.style          = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc    = WndProc;
    wcex.cbClsExtra     = 0;
    wcex.cbWndExtra     = 0;
    wcex.hInstance      = hInstance;
    wcex.hIcon          = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_SHIYAN3PROJECT));
    wcex.hCursor        = LoadCursor(nullptr, IDC_ARROW);
    wcex.hbrBackground  = (HBRUSH)(COLOR_WINDOW+1);
    wcex.lpszMenuName   = MAKEINTRESOURCEW(IDC_SHIYAN3PROJECT);
    wcex.lpszClassName  = szWindowClass;
    wcex.hIconSm        = LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

    return RegisterClassExW(&wcex);
}

//
//   Function: InitInstance(HINSTANCE, int)
//
//   Purpose: Save instance handle and create main window
//
//   Comments:
//
//        In this function, we save the instance handle in a global variable and
//        create and display the main program window.
//
BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
   hInst = hInstance; // Store instance handle in global variable

   HWND hWnd = CreateWindowW(szWindowClass, szTitle, WS_OVERLAPPEDWINDOW,
      CW_USEDEFAULT, 0, CW_USEDEFAULT, 0, nullptr, nullptr, hInstance, nullptr);

   if (!hWnd)
   {
      return FALSE;
   }

   ShowWindow(hWnd, nCmdShow);
   UpdateWindow(hWnd);

   return TRUE;
}

//
//  Function: WndProc(HWND, UINT, WPARAM, LPARAM)
//
//  Purpose: Process messages for the main window.
//
//  WM_COMMAND  - Process application menu
//  WM_PAINT    - Paint the main window
//  WM_DESTROY  - Post quit message and return
//
//
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_COMMAND:
    {
        int wmId = LOWORD(wParam);
        switch (wmId)
        {
        // Drawing tools
        case IDM_DRAW_LINE: g_currentTool = ShapeType::LINE; g_statusText = L"直线工具：点击两个点绘制直线"; break;
        case IDM_DRAW_CIRCLE: g_currentTool = ShapeType::CIRCLE; g_statusText = L"圆形工具：点击圆心，拖动鼠标确定半径"; break;
        case IDM_DRAW_RECTANGLE: g_currentTool = ShapeType::RECTANGLE; g_statusText = L"矩形工具：点击并拖动鼠标绘制矩形"; break;
        case IDM_DRAW_TRIANGLE: g_currentTool = ShapeType::TRIANGLE; g_statusText = L"三角形工具：依次点击三个顶点"; break;
        case IDM_DRAW_DIAMOND: g_currentTool = ShapeType::DIAMOND; g_statusText = L"菱形工具：点击并拖动鼠标绘制菱形"; break;
        case IDM_DRAW_PARALLELOGRAM: g_currentTool = ShapeType::PARALLELOGRAM; g_statusText = L"平行四边形工具：依次点击三个顶点"; break;
        case IDM_DRAW_CURVE: g_currentTool = ShapeType::CURVE; g_statusText = L"曲线工具：依次点击控制点，右键完成绘制"; break;
        case IDM_DRAW_POLYLINE: g_currentTool = ShapeType::POLYLINE; g_statusText = L"折线工具：依次点击各个顶点，右键完成绘制"; break;
        
        // Edit operations
        case IDM_SELECT: g_currentTool = ShapeType::NONE; g_statusText = L"选择模式：点击图形进行选择"; break;
        case IDM_DESELECT:
            if (g_selectedShape) {
                g_selectedShape->selected = false;
                g_selectedShape = nullptr;
                g_statusText = L"已取消选择";
                InvalidateRect(hWnd, nullptr, FALSE);
            }
            break;
        case IDM_DELETE:
            if (g_selectedShape) {
                SaveStateToUndoStack();
                g_shapes.erase(std::remove_if(g_shapes.begin(), g_shapes.end(),
                    [](const std::shared_ptr<Shape>& s) { return s.get() == g_selectedShape; }),
                    g_shapes.end());
                g_selectedShape = nullptr;
                g_statusText = L"已删除选中的图形";
                InvalidateRect(hWnd, nullptr, FALSE);
            }
            break;
        case IDM_MOVE: g_isMoving = true; g_statusText = L"移动模式：按住鼠标左键拖动图形"; break;
        case IDM_ROTATE:
            if (g_selectedShape) {
                g_backupRotationData = g_selectedShape->Serialize();
                g_currentRotationAngle = 0.0f;
                g_isRotating = true;
                g_statusText = L"旋转模式：滚动鼠标滚轮调整角度，左键确认，右键取消";
            } else {
                g_statusText = L"请先选择一个图形";
            }
            break;
        case IDM_SCALE:
            if (g_selectedShape) {
                g_backupShapeData = g_selectedShape->Serialize();
                g_currentScaleFactor = 1.0f;
                g_isScaling = true;
                g_statusText = L"缩放模式：滚动鼠标滚轮调整大小，左键确认，右键取消";
            } else {
                g_statusText = L"请先选择一个图形";
            }
            break;
        
        // Geometry calculations
        case IDM_INTERSECTION: g_calcMode = CalcMode::INTERSECTION; g_statusText = L"求交点：请依次选择两个图形"; break;
        case IDM_PERPENDICULAR: g_calcMode = CalcMode::PERPENDICULAR; g_statusText = L"绘制垂线：请选择一条直线"; break;
        case IDM_CENTER: g_calcMode = CalcMode::CENTER; g_statusText = L"显示圆心：请选择一个圆形"; break;
        case IDM_TANGENT: g_calcMode = CalcMode::TANGENT; g_statusText = L"绘制切线：先点击一个点，再选择圆形"; break;
        
        // File operations
        case IDM_NEW:
            if (!g_shapes.empty()) {
                SaveStateToUndoStack();
            }
            g_shapes.clear();
            g_selectedShape = nullptr;
            // Release all fill bitmaps
            for (auto bitmap : g_seedFillBitmaps) {
                if (bitmap) bitmap->Release();
            }
            g_seedFillBitmaps.clear();
            g_statusText = L"新建文件：画布已清空";
            InvalidateRect(hWnd, nullptr, FALSE);
            break;
        case IDM_SAVE: SaveToFile(hWnd); break;
        case IDM_OPEN: LoadFromFile(hWnd); break;
        case IDM_UNDO:
            if (!g_undoStack.empty()) {
                // Save current state to redo stack
                g_redoStack.push_back(g_shapes);
                if (g_redoStack.size() > MAX_UNDO_STEPS) {
                    g_redoStack.erase(g_redoStack.begin());
                }
                // Restore previous state directly
                g_shapes = g_undoStack.back();
                g_undoStack.pop_back();
                g_selectedShape = nullptr;
                g_statusText = L"已撤回操作";
                InvalidateRect(hWnd, nullptr, FALSE);
            } else {
                g_statusText = L"没有可撤回的操作";
            }
            break;
        case IDM_REDO:
            if (!g_redoStack.empty()) {
                // Save current state to undo stack
                g_undoStack.push_back(g_shapes);
                if (g_undoStack.size() > MAX_UNDO_STEPS) {
                    g_undoStack.erase(g_undoStack.begin());
                }
                // Restore next state directly
                g_shapes = g_redoStack.back();
                g_redoStack.pop_back();
                g_selectedShape = nullptr;
                g_statusText = L"已重做操作";
                InvalidateRect(hWnd, nullptr, FALSE);
            } else {
                g_statusText = L"没有可重做的操作";
            }
            break;
        
        // ==================== 实验3 新增菜单处理 ====================
        // (1) 直线绘制算法选择
        case IDM_LINE_MIDPOINT:
            g_lineAlgorithm = LineAlgorithm::MIDPOINT;
            g_statusText = L"已切换到中点画线法";
            break;
        case IDM_LINE_BRESENHAM:
            g_lineAlgorithm = LineAlgorithm::BRESENHAM;
            g_statusText = L"已切换到Bresenham画线法";
            break;
        
        // (2) 圆绘制算法选择
        case IDM_CIRCLE_MIDPOINT:
            g_circleAlgorithm = CircleAlgorithm::MIDPOINT;
            g_statusText = L"已切换到中点画圆法";
            break;
        case IDM_CIRCLE_BRESENHAM:
            g_circleAlgorithm = CircleAlgorithm::BRESENHAM;
            g_statusText = L"已切换到Bresenham画圆法";
            break;
        
        // (3) 线宽设置
        case IDM_LINEWIDTH_1:
            g_lineWidth = 1;
            // 如果有选中的直线或圆,修改其线宽
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineWidth = 1;
                    g_statusText = L"选中直线的线宽已设置为1像素";
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineWidth = 1;
                    g_statusText = L"选中圆形的线宽已设置为1像素";
                } else {
                    g_statusText = L"线宽设置为1像素（仅对新绘制的直线和圆有效）";
                }
                InvalidateRect(hWnd, nullptr, FALSE);
            } else {
                g_statusText = L"线宽设置为1像素";
            }
            break;
        case IDM_LINEWIDTH_3:
            g_lineWidth = 3;
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineWidth = 3;
                    g_statusText = L"选中直线的线宽已设置为3像素";
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineWidth = 3;
                    g_statusText = L"选中圆形的线宽已设置为3像素";
                } else {
                    g_statusText = L"线宽设置为3像素（仅对新绘制的直线和圆有效）";
                }
                InvalidateRect(hWnd, nullptr, FALSE);
            } else {
                g_statusText = L"线宽设置为3像素";
            }
            break;
        case IDM_LINEWIDTH_5:
            g_lineWidth = 5;
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineWidth = 5;
                    g_statusText = L"选中直线的线宽已设置为5像素";
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineWidth = 5;
                    g_statusText = L"选中圆形的线宽已设置为5像素";
                } else {
                    g_statusText = L"线宽设置为5像素（仅对新绘制的直线和圆有效）";
                }
                InvalidateRect(hWnd, nullptr, FALSE);
            } else {
                g_statusText = L"线宽设置为5像素";
            }
            break;
        case IDM_LINEWIDTH_SCANLINE:
            g_lineWidth = 10;
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineWidth = 10;
                    g_statusText = L"选中直线的线宽已设置为10像素";
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineWidth = 10;
                    g_statusText = L"选中圆形的线宽已设置为10像素";
                } else {
                    g_statusText = L"线宽设置为10像素（仅对新绘制的直线和圆有效）";
                }
                InvalidateRect(hWnd, nullptr, FALSE);
            } else {
                g_statusText = L"线宽设置为10像素（扫描线填充）";
            }
            break;
        
        // (4) 线型设置
        case IDM_LINESTYLE_SOLID:
            g_lineStyle = LineStyleType::SOLID;
            // 如果有选中的直线或圆形,修改其线型
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineStyle = LineStyleType::SOLID;
                    g_statusText = L"选中直线的线型已设置为实线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineStyle = LineStyleType::SOLID;
                    g_statusText = L"选中圆形的线型已设置为实线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                }
            } else {
                g_statusText = L"默认线型已设置为实线";
            }
            break;
        case IDM_LINESTYLE_DASH:
            g_lineStyle = LineStyleType::DASH;
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineStyle = LineStyleType::DASH;
                    g_statusText = L"选中直线的线型已设置为虚线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineStyle = LineStyleType::DASH;
                    g_statusText = L"选中圆形的线型已设置为虚线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                }
            } else {
                g_statusText = L"线型设置为虚线";
            }
            break;
        case IDM_LINESTYLE_DOT:
            g_lineStyle = LineStyleType::DOT;
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineStyle = LineStyleType::DOT;
                    g_statusText = L"选中直线的线型已设置为点线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineStyle = LineStyleType::DOT;
                    g_statusText = L"选中圆形的线型已设置为点线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                }
            } else {
                g_statusText = L"线型设置为点线";
            }
            break;
        case IDM_LINESTYLE_DASHDOT:
            g_lineStyle = LineStyleType::DASHDOT;
            if (g_selectedShape) {
                if (g_selectedShape->type == ShapeType::LINE) {
                    static_cast<Line*>(g_selectedShape)->lineStyle = LineStyleType::DASHDOT;
                    g_statusText = L"选中直线的线型已设置为点划线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                } else if (g_selectedShape->type == ShapeType::CIRCLE) {
                    static_cast<Circle*>(g_selectedShape)->lineStyle = LineStyleType::DASHDOT;
                    g_statusText = L"选中圆形的线型已设置为点划线";
                    InvalidateRect(hWnd, nullptr, FALSE);
                }
            } else {
                g_statusText = L"线型设置为点划线";
            }
            break;
        
        // (5) 填充功能
        case IDM_DRAW_POLYGON:
            g_currentTool = ShapeType::POLYLINE;
            g_fillMode = FillMode::FENCE;
            g_polygonPoints.clear();
            g_statusText = L"多边形绘制：依次点击顶点，右键完成并填充";
            break;
        case IDM_FILL_FENCE:
            g_fillMode = FillMode::FENCE;
            g_currentTool = ShapeType::NONE;
            g_statusText = L"栅栏填充模式：点击要填充的图形";
            break;
        case IDM_FILL_SEED:
            g_fillMode = FillMode::SEED;
            g_currentTool = ShapeType::NONE;
            g_statusText = L"种子填充模式：点击封闭区域内部进行填充";
            break;
        
        // (6) Bezier曲线
        case IDM_DRAW_BEZIER:
            g_drawingBezier = true;
            g_bezierControlPoints.clear();
            g_currentTool = ShapeType::NONE;
            g_statusText = L"Bezier曲线：依次点击控制点，右键完成绘制";
            break;
        
        // 辅助功能
        case IDM_CLEAR:
            SaveStateToUndoStack();
            g_shapes.clear();
            g_selectedShape = nullptr;
            g_bezierControlPoints.clear();
            g_polygonPoints.clear();
            g_drawingBezier = false;
            g_fillMode = FillMode::NONE;
            // Release all fill bitmaps
            for (auto bitmap : g_seedFillBitmaps) {
                if (bitmap) bitmap->Release();
            }
            g_seedFillBitmaps.clear();
            g_statusText = L"画布已清空";
            break;
        case IDM_SELECT_SHAPE:
            g_currentTool = ShapeType::NONE;
            g_drawingBezier = false;
            g_fillMode = FillMode::NONE;
            g_statusText = L"选择模式";
            break;
        
        case IDM_ABOUT:
            DialogBox(hInst, MAKEINTRESOURCE(IDD_ABOUTBOX), hWnd, About);
            break;
        case IDM_EXIT:
            DestroyWindow(hWnd);
            break;
        default:
            return DefWindowProc(hWnd, message, wParam, lParam);
        }
        InvalidateRect(hWnd, nullptr, FALSE);
    }
    break;
    
    case WM_PAINT:
        OnPaint(hWnd);
        break;
    
    case WM_LBUTTONDOWN:
        OnLButtonDown(hWnd, lParam);
        break;
    
    case WM_LBUTTONUP:
        OnLButtonUp(hWnd, lParam);
        break;
    
    case WM_MOUSEMOVE:
        OnMouseMove(hWnd, lParam);
        break;
    
    case WM_RBUTTONDOWN:
        OnRButtonDown(hWnd);
        break;
    
    case WM_MOUSEWHEEL:
        if (g_isScaling && g_selectedShape) {
            int delta = GET_WHEEL_DELTA_WPARAM(wParam);
            float scaleDelta = (delta > 0) ? 1.05f : 0.95f;
            g_currentScaleFactor *= scaleDelta;
            D2D1_POINT_2F center = g_selectedShape->GetCenter();
            g_selectedShape->Scale(center, scaleDelta);
            
            wchar_t buf[128];
            swprintf_s(buf, L"缩放中：%.2f倍（滚轮调整，左键确认，右键取消）", g_currentScaleFactor);
            g_statusText = buf;
            InvalidateRect(hWnd, nullptr, FALSE);
        } else if (g_isRotating && g_selectedShape) {
            int delta = GET_WHEEL_DELTA_WPARAM(wParam);
            float angleDelta = (delta > 0) ? 0.1f : -0.1f;  // Rotate in radians
            g_currentRotationAngle += angleDelta;
            D2D1_POINT_2F center = g_selectedShape->GetCenter();
            g_selectedShape->Rotate(center, angleDelta);
            
            wchar_t buf[128];
            float degrees = g_currentRotationAngle * 180.0f / 3.14159265f;
            swprintf_s(buf, L"旋转中：%.1f度（滚轮调整，左键确认，右键取消）", degrees);
            g_statusText = buf;
            InvalidateRect(hWnd, nullptr, FALSE);
        }
        break;
    
    case WM_SIZE:
        if (g_pRenderTarget) {
            RECT rc;
            GetClientRect(hWnd, &rc);
            g_pRenderTarget->Resize(D2D1::SizeU(rc.right - rc.left, rc.bottom - rc.top));
        }
        break;
    
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    
    default:
        return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

// Message handler for About box.
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    UNREFERENCED_PARAMETER(lParam);
    switch (message)
    {
    case WM_INITDIALOG:
        return (INT_PTR)TRUE;

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, LOWORD(wParam));
            return (INT_PTR)TRUE;
        }
        break;
    }
    return (INT_PTR)FALSE;
}

// Create Direct2D device resources
HRESULT CreateDeviceResources(HWND hWnd)
{
    if (g_pRenderTarget) return S_OK;

    RECT rc;
    GetClientRect(hWnd, &rc);

    HRESULT hr = g_pD2DFactory->CreateHwndRenderTarget(
        D2D1::RenderTargetProperties(),
        D2D1::HwndRenderTargetProperties(hWnd, D2D1::SizeU(rc.right - rc.left, rc.bottom - rc.top)),
        &g_pRenderTarget);

    if (SUCCEEDED(hr)) {
        hr = g_pRenderTarget->CreateSolidColorBrush(D2D1::ColorF(D2D1::ColorF::Black), &g_pBrush);
    }

    if (SUCCEEDED(hr) && g_pDWriteFactory) {
        hr = g_pDWriteFactory->CreateTextFormat(
            L"Arial", nullptr, DWRITE_FONT_WEIGHT_NORMAL, DWRITE_FONT_STYLE_NORMAL,
            DWRITE_FONT_STRETCH_NORMAL, 14.0f, L"zh-cn", &g_pTextFormat);
    }

    return hr;
}

// Release Direct2D device resources
void DiscardDeviceResources()
{
    if (g_pBrush) { g_pBrush->Release(); g_pBrush = nullptr; }
    if (g_pRenderTarget) { g_pRenderTarget->Release(); g_pRenderTarget = nullptr; }
    if (g_pTextFormat) { g_pTextFormat->Release(); g_pTextFormat = nullptr; }
    // Release all fill bitmaps
    for (auto bitmap : g_seedFillBitmaps) {
        if (bitmap) bitmap->Release();
    }
    g_seedFillBitmaps.clear();
}

// Paint function - Pure Direct2D, no GDI
void OnPaint(HWND hWnd)
{
    PAINTSTRUCT ps;
    BeginPaint(hWnd, &ps);

    CreateDeviceResources(hWnd);

    if (g_pRenderTarget) {
        // 处理待执行的种子填充
        if (g_pendingSeedFill) {
            g_pendingSeedFill = false;
            
            // Convert fill color to D2D1_COLOR_F
            D2D1_COLOR_F d2dFillColor = D2D1::ColorF(
                GetRValue(g_fillColor) / 255.0f,
                GetGValue(g_fillColor) / 255.0f,
                GetBValue(g_fillColor) / 255.0f,
                1.0f
            );
            
            // Perform seed fill - Fill function will redraw shapes internally
            ID2D1Bitmap* newFillBitmap = SeedFillD2D::Fill(g_pRenderTarget, (int)g_seedFillPoint.x, (int)g_seedFillPoint.y, d2dFillColor, g_shapes);
            
            if (newFillBitmap) {
                // Add new fill bitmap to list (don't replace old ones)
                g_seedFillBitmaps.push_back(newFillBitmap);
                g_statusText = L"种子填充完成";
            } else {
                g_statusText = L"种子填充失败";
            }
        }
        
        // 正常的绘制流程
        g_pRenderTarget->BeginDraw();
        g_pRenderTarget->Clear(D2D1::ColorF(D2D1::ColorF::White));

        // Draw all seed fill bitmaps
        for (auto bitmap : g_seedFillBitmaps) {
            if (bitmap) {
                D2D1_SIZE_U bmpSize = bitmap->GetPixelSize();
                D2D1_RECT_F destRect = D2D1::RectF(0, 0, (float)bmpSize.width, (float)bmpSize.height);
                g_pRenderTarget->DrawBitmap(bitmap, destRect, 1.0f, D2D1_BITMAP_INTERPOLATION_MODE_NEAREST_NEIGHBOR);
            }
        }

        // Draw all shapes using Direct2D (no flicker)
        for (auto& shape : g_shapes) {
            shape->Draw(g_pRenderTarget, g_pBrush);
        }

        // Draw current shape being created
        if (g_currentShape) {
            g_currentShape->Draw(g_pRenderTarget, g_pBrush);
        }
        
        // ==================== 实验3 新增：绘制Bezier控制点和预览 ====================
        if (g_drawingBezier && !g_bezierControlPoints.empty()) {
            // 绘制控制点
            g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Red));
            for (const auto& pt : g_bezierControlPoints) {
                D2D1_ELLIPSE ellipse = D2D1::Ellipse(pt, 4.0f, 4.0f);
                g_pRenderTarget->FillEllipse(ellipse, g_pBrush);
            }
            
            // 绘制控制多边形
            if (g_bezierControlPoints.size() >= 2) {
                g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Gray));
                for (size_t i = 0; i < g_bezierControlPoints.size() - 1; i++) {
                    g_pRenderTarget->DrawLine(g_bezierControlPoints[i], 
                                             g_bezierControlPoints[i + 1], g_pBrush, 1.0f);
                }
                
                // 绘制Bezier曲线预览
                auto curvePoints = BezierCurve::GenerateCurve(g_bezierControlPoints, 200);
                g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Blue));
                for (size_t i = 0; i < curvePoints.size() - 1; i++) {
                    g_pRenderTarget->DrawLine(curvePoints[i], curvePoints[i + 1], g_pBrush, 2.0f);
                }
            }
        }
        
        // 绘制普通曲线的控制点预览
        if (g_currentTool == ShapeType::CURVE && g_currentShape) {
            if (auto curve = dynamic_cast<Curve*>(g_currentShape.get())) {
                if (!curve->curvePoints.empty()) {
                    // 绘制控制点
                    g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Blue));
                    for (const auto& pt : curve->curvePoints) {
                        D2D1_ELLIPSE ellipse = D2D1::Ellipse(pt, 4.0f, 4.0f);
                        g_pRenderTarget->FillEllipse(ellipse, g_pBrush);
                    }
                    
                    // 绘制控制折线（辅助线）
                    if (curve->curvePoints.size() >= 2) {
                        g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::LightGray));
                        for (size_t i = 0; i < curve->curvePoints.size() - 1; i++) {
                            g_pRenderTarget->DrawLine(curve->curvePoints[i], 
                                                     curve->curvePoints[i + 1], g_pBrush, 1.0f);
                        }
                    }
                }
            }
        }
        
        // 绘制多边形填充的临时点
        if (g_fillMode == FillMode::FENCE && !g_polygonPoints.empty()) {
            g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Green));
            for (const auto& pt : g_polygonPoints) {
                D2D1_ELLIPSE ellipse = D2D1::Ellipse(pt, 3.0f, 3.0f);
                g_pRenderTarget->FillEllipse(ellipse, g_pBrush);
            }
            if (g_polygonPoints.size() >= 2) {
                for (size_t i = 0; i < g_polygonPoints.size() - 1; i++) {
                    g_pRenderTarget->DrawLine(g_polygonPoints[i], g_polygonPoints[i + 1], g_pBrush, 1.0f);
                }
            }
        }

        // Display status text
        if (!g_statusText.empty() && g_pTextFormat) {
            g_pBrush->SetColor(D2D1::ColorF(D2D1::ColorF::Blue));
            D2D1_RECT_F textRect = D2D1::RectF(10, 10, 800, 50);
            g_pRenderTarget->DrawText(g_statusText.c_str(), (UINT32)g_statusText.length(),
                g_pTextFormat, textRect, g_pBrush);
        }

        HRESULT hr = g_pRenderTarget->EndDraw();
        if (hr == D2DERR_RECREATE_TARGET) {
            DiscardDeviceResources();
        }
    }

    EndPaint(hWnd, &ps);
}

// Left mouse button down
void OnLButtonDown(HWND hWnd, LPARAM lParam)
{
    D2D1_POINT_2F point = D2D1::Point2F(LOWORD(lParam), HIWORD(lParam));

    // ==================== 实验3 新增功能处理 ====================
    // Bezier曲线控制点添加
    if (g_drawingBezier) {
        g_bezierControlPoints.push_back(point);
        wchar_t buf[128];
        swprintf_s(buf, L"已添加第%d个控制点，右键完成绘制", (int)g_bezierControlPoints.size());
        g_statusText = buf;
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }
    
    // 多边形填充模式 - 添加顶点
    if (g_fillMode == FillMode::FENCE && g_currentTool == ShapeType::POLYLINE) {
        g_polygonPoints.push_back(point);
        wchar_t buf[128];
        swprintf_s(buf, L"已添加第%d个顶点，右键完成并填充", (int)g_polygonPoints.size());
        g_statusText = buf;
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }
    
    // 栅栏填充模式 - 点击图形进行填充
    if (g_fillMode == FillMode::FENCE && g_currentTool == ShapeType::NONE) {
        // 查找点击的图形
        for (auto& shape : g_shapes) {
            if (shape->HitTest(point) && shape->CanFill()) {
                SaveStateToUndoStack();
                D2D1_COLOR_F fillColor = D2D1::ColorF(D2D1::ColorF::Yellow, 0.5f);
                shape->Fill(fillColor);
                g_statusText = L"图形已填充";
                g_fillMode = FillMode::NONE;
                InvalidateRect(hWnd, nullptr, FALSE);
                return;
            }
        }
        g_statusText = L"未点击到可填充的图形";
        return;
    }
    
    // 种子填充模式 - 点击区域内部
    if (g_fillMode == FillMode::SEED && g_currentTool == ShapeType::NONE) {
        // 标记待处理的种子填充
        g_pendingSeedFill = true;
        g_seedFillPoint = point;
        g_fillMode = FillMode::NONE;
        g_statusText = L"正在执行种子填充...";
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }

    // Confirm scaling
    if (g_isScaling && g_selectedShape) {
        SaveStateToUndoStack();
        g_isScaling = false;
        g_backupShapeData.clear();
        g_currentScaleFactor = 1.0f;
        g_statusText = L"缩放已确认";
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }
    
    // Confirm rotation
    if (g_isRotating && g_selectedShape) {
        SaveStateToUndoStack();
        g_isRotating = false;
        g_backupRotationData.clear();
        g_currentRotationAngle = 0.0f;
        g_statusText = L"旋转已确认";
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }

    // Geometry calculation mode
    if (g_calcMode != CalcMode::NONE) {
        if (g_calcMode == CalcMode::TANGENT && g_calcShape1 == nullptr) {
            g_calcPoint = point;
            g_statusText = L"已记录点的位置，请选择一个圆形";
            g_calcShape1 = (Shape*)1;
            InvalidateRect(hWnd, nullptr, FALSE);
            return;
        }

        for (auto& shape : g_shapes) {
            if (shape->HitTest(point)) {
                if (g_calcMode == CalcMode::INTERSECTION) {
                    if (!g_calcShape1) {
                        g_calcShape1 = shape.get();
                        g_statusText = L"已选择第一个图形，请选择第二个图形";
                    } else {
                        g_calcShape2 = shape.get();
                        CalculateIntersections();
                        g_calcMode = CalcMode::NONE;
                        g_calcShape1 = g_calcShape2 = nullptr;
                    }
                } else if (g_calcMode == CalcMode::PERPENDICULAR && shape->type == ShapeType::LINE) {
                    DrawPerpendicular(point, dynamic_cast<Line*>(shape.get()));
                    g_calcMode = CalcMode::NONE;
                } else if (g_calcMode == CalcMode::CENTER && shape->type == ShapeType::CIRCLE) {
                    ShowCenter(dynamic_cast<Circle*>(shape.get()));
                    g_calcMode = CalcMode::NONE;
                } else if (g_calcMode == CalcMode::TANGENT && shape->type == ShapeType::CIRCLE && g_calcShape1) {
                    DrawTangent(g_calcPoint, dynamic_cast<Circle*>(shape.get()));
                    g_calcMode = CalcMode::NONE;
                    g_calcShape1 = nullptr;
                }
                InvalidateRect(hWnd, nullptr, FALSE);
                return;
            }
        }
        return;
    }

    // Selection mode
    if (g_currentTool == ShapeType::NONE) {
        if (g_selectedShape) g_selectedShape->selected = false;
        g_selectedShape = nullptr;

        for (auto& shape : g_shapes) {
            if (shape->HitTest(point)) {
                g_selectedShape = shape.get();
                g_selectedShape->selected = true;
                g_lastMousePos = point;
                g_statusText = L"已选中图形";
                break;
            }
        }
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }

    // Drawing mode
    g_isDrawing = true;
    g_startPoint = point;
    g_clickCount++;

    switch (g_currentTool) {
    case ShapeType::LINE:
        if (g_clickCount == 1) {
            auto line = std::make_shared<Line>(point, point);
            line->lineAlgorithm = g_lineAlgorithm;
            line->lineWidth = g_lineWidth;
            line->lineStyle = g_lineStyle;
            g_currentShape = line;
        }
        break;
    case ShapeType::CIRCLE:
        if (g_clickCount == 1) {
            auto circle = std::make_shared<Circle>(point, 0);
            circle->circleAlgorithm = g_circleAlgorithm;
            circle->lineWidth = g_lineWidth;
            circle->lineStyle = g_lineStyle;
            g_currentShape = circle;
        }
        break;
    case ShapeType::RECTANGLE:
        if (g_clickCount == 1) {
            g_currentShape = std::make_shared<RectangleShape>(point, point);
        }
        break;
    case ShapeType::TRIANGLE:
        g_tempPoints.push_back(point);
        if (g_clickCount == 3) {
            SaveStateToUndoStack();
            g_currentShape = std::make_shared<Triangle>(g_tempPoints[0], g_tempPoints[1], g_tempPoints[2]);
            g_shapes.push_back(g_currentShape);
            g_currentShape = nullptr;
            g_clickCount = 0;
            g_tempPoints.clear();
            g_statusText = L"三角形绘制完成";
        }
        break;
    case ShapeType::DIAMOND:
        if (g_clickCount == 1) {
            g_currentShape = std::make_shared<Diamond>(point, 0, 0);
        }
        break;
    case ShapeType::PARALLELOGRAM:
        g_tempPoints.push_back(point);
        if (g_clickCount == 3) {
            SaveStateToUndoStack();
            g_currentShape = std::make_shared<Parallelogram>(g_tempPoints[0], g_tempPoints[1], g_tempPoints[2]);
            g_shapes.push_back(g_currentShape);
            g_currentShape = nullptr;
            g_clickCount = 0;
            g_tempPoints.clear();
            g_statusText = L"平行四边形绘制完成";
        }
        break;
    case ShapeType::CURVE:
        if (!g_currentShape) {
            g_currentShape = std::make_shared<Curve>();
        }
        if (auto curve = dynamic_cast<Curve*>(g_currentShape.get())) {
            curve->AddPoint(point);
        }
        break;
    case ShapeType::POLYLINE:
        if (!g_currentShape) {
            g_currentShape = std::make_shared<PolylineShape>();
        }
        if (auto polyline = dynamic_cast<PolylineShape*>(g_currentShape.get())) {
            polyline->AddPoint(point);
        }
        break;
    }

    InvalidateRect(hWnd, nullptr, FALSE);
}

// Left mouse button up
void OnLButtonUp(HWND hWnd, LPARAM lParam)
{
    if (!g_isDrawing) return;

    D2D1_POINT_2F point = D2D1::Point2F(LOWORD(lParam), HIWORD(lParam));

    switch (g_currentTool) {
    case ShapeType::LINE:
    case ShapeType::CIRCLE:
    case ShapeType::RECTANGLE:
    case ShapeType::DIAMOND:
        if (g_currentShape) {
            SaveStateToUndoStack();
            g_shapes.push_back(g_currentShape);
            g_currentShape = nullptr;
            g_clickCount = 0;
            g_statusText = L"图形绘制完成";
        }
        break;
    }

    g_isDrawing = false;
    InvalidateRect(hWnd, nullptr, FALSE);
}

// Mouse move
void OnMouseMove(HWND hWnd, LPARAM lParam)
{
    D2D1_POINT_2F point = D2D1::Point2F(LOWORD(lParam), HIWORD(lParam));

    // Move selected shape (rotation and scaling are now handled by mouse wheel)
    if (g_selectedShape && g_isMoving) {
        if (GetAsyncKeyState(VK_LBUTTON) & 0x8000) {
            float dx = point.x - g_lastMousePos.x;
            float dy = point.y - g_lastMousePos.y;
            g_selectedShape->Move(dx, dy);
            g_lastMousePos = point;
            InvalidateRect(hWnd, nullptr, FALSE);
        }
        return;
    }

    // Update shape being drawn
    if (g_isDrawing && g_currentShape) {
        if (auto line = dynamic_cast<Line*>(g_currentShape.get())) {
            line->end = point;
        } else if (auto circle = dynamic_cast<Circle*>(g_currentShape.get())) {
            float dx = point.x - circle->center.x;
            float dy = point.y - circle->center.y;
            circle->radius = sqrt(dx * dx + dy * dy);
        } else if (auto rect = dynamic_cast<RectangleShape*>(g_currentShape.get())) {
            // Update rectangle corners while dragging
            rect->p2 = D2D1::Point2F(point.x, rect->p1.y);
            rect->p3 = point;
            rect->p4 = D2D1::Point2F(rect->p1.x, point.y);
        } else if (auto diamond = dynamic_cast<Diamond*>(g_currentShape.get())) {
            diamond->width = fabs(point.x - diamond->center.x) * 2;
            diamond->height = fabs(point.y - diamond->center.y) * 2;
        }
        InvalidateRect(hWnd, nullptr, FALSE);
    }

    // Change mouse cursor
    if (g_currentTool == ShapeType::NONE) {
        bool onShape = false;
        for (auto& shape : g_shapes) {
            if (shape->HitTest(point)) {
                onShape = true;
                break;
            }
        }
        SetCursor(LoadCursor(nullptr, onShape ? IDC_HAND : IDC_ARROW));
    }
}

// Right mouse button down
void OnRButtonDown(HWND hWnd)
{
    // ==================== 实验3 新增功能：完成Bezier曲线绘制 ====================
    if (g_drawingBezier && g_bezierControlPoints.size() >= 2) {
        SaveStateToUndoStack();
        auto curve = std::make_shared<Curve>();
        for (const auto& pt : g_bezierControlPoints) {
            curve->AddPoint(pt);
        }
        g_shapes.push_back(curve);
        g_bezierControlPoints.clear();
        g_drawingBezier = false;
        g_statusText = L"Bezier曲线绘制完成";
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }
    
    // Complete polygon fill using Direct2D
    if (g_fillMode == FillMode::FENCE && g_currentTool == ShapeType::POLYLINE && g_polygonPoints.size() >= 3) {
        SaveStateToUndoStack();
        
        // Create a filled polygon using Direct2D PathGeometry
        auto polyline = std::make_shared<PolylineShape>();
        for (const auto& pt : g_polygonPoints) {
            polyline->AddPoint(pt);
        }
        // Enable fill and set fill color
        polyline->filled = true;
        polyline->fillColor = D2D1::ColorF(
            GetRValue(g_fillColor) / 255.0f,
            GetGValue(g_fillColor) / 255.0f,
            GetBValue(g_fillColor) / 255.0f,
            0.7f  // Semi-transparent
        );
        g_shapes.push_back(polyline);
        
        g_polygonPoints.clear();
        g_fillMode = FillMode::NONE;
        g_statusText = L"多边形填充完成";
        InvalidateRect(hWnd, nullptr, FALSE);
        return;
    }
    
    // Cancel scaling and restore original shape
    if (g_isScaling && g_selectedShape && !g_backupShapeData.empty()) {
        g_selectedShape->Deserialize(g_backupShapeData);
        g_backupShapeData.clear();
        g_currentScaleFactor = 1.0f;
        g_isScaling = false;
        g_statusText = L"缩放已取消，已恢复原始大小";
        InvalidateRect(hWnd, nullptr, FALSE);
    }
    // Cancel rotation and restore original shape
    else if (g_isRotating && g_selectedShape && !g_backupRotationData.empty()) {
        g_selectedShape->Deserialize(g_backupRotationData);
        g_backupRotationData.clear();
        g_currentRotationAngle = 0.0f;
        g_isRotating = false;
        g_statusText = L"旋转已取消，已恢复原始角度";
        InvalidateRect(hWnd, nullptr, FALSE);
    }
    // Complete curve/polyline drawing
    else if (g_currentShape && (g_currentTool == ShapeType::CURVE || g_currentTool == ShapeType::POLYLINE)) {
        SaveStateToUndoStack();
        g_shapes.push_back(g_currentShape);
        g_currentShape = nullptr;
        g_clickCount = 0;
        g_statusText = L"曲线/折线绘制完成";
        InvalidateRect(hWnd, nullptr, FALSE);
    }
    
    g_isMoving = g_isRotating = g_isScaling = false;
}

// Save to file
void SaveToFile(HWND hWnd)
{
    OPENFILENAME ofn = { 0 };
    WCHAR szFile[260] = { 0 };

    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hWnd;
    ofn.lpstrFile = szFile;
    ofn.nMaxFile = sizeof(szFile);
    ofn.lpstrFilter = L"Drawing Files (*.drw)\0*.drw\0All Files (*.*)\0*.*\0";
    ofn.nFilterIndex = 1;
    ofn.lpstrFileTitle = nullptr;
    ofn.nMaxFileTitle = 0;
    ofn.lpstrInitialDir = nullptr;
    ofn.Flags = OFN_PATHMUSTEXIST | OFN_OVERWRITEPROMPT;

    if (GetSaveFileName(&ofn)) {
        std::ofstream file(szFile);
        if (file.is_open()) {
            file << g_shapes.size() << std::endl;
            for (const auto& shape : g_shapes) {
                file << shape->Serialize() << std::endl;
            }
            file.close();
            g_statusText = L"文件保存成功";
            InvalidateRect(hWnd, nullptr, FALSE);
        }
    }
}

// Load from file
void LoadFromFile(HWND hWnd)
{
    OPENFILENAME ofn = { 0 };
    WCHAR szFile[260] = { 0 };

    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hWnd;
    ofn.lpstrFile = szFile;
    ofn.nMaxFile = sizeof(szFile);
    ofn.lpstrFilter = L"Drawing Files (*.drw)\0*.drw\0All Files (*.*)\0*.*\0";
    ofn.nFilterIndex = 1;
    ofn.lpstrFileTitle = nullptr;
    ofn.nMaxFileTitle = 0;
    ofn.lpstrInitialDir = nullptr;
    ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;

    if (GetOpenFileName(&ofn)) {
        std::ifstream file(szFile);
        if (file.is_open()) {
            g_shapes.clear();
            size_t count;
            file >> count;
            file.ignore();

            for (size_t i = 0; i < count; i++) {
                std::string line;
                std::getline(file, line);
                if (line.empty()) continue;

                std::stringstream ss(line);
                std::string type;
                ss >> type;

                std::shared_ptr<Shape> shape;
                if (type == "LINE") shape = std::make_shared<Line>();
                else if (type == "CIRCLE") shape = std::make_shared<Circle>();
                else if (type == "RECTANGLE") shape = std::make_shared<RectangleShape>();
                else if (type == "TRIANGLE") shape = std::make_shared<Triangle>();
                else if (type == "DIAMOND") shape = std::make_shared<Diamond>();
                else if (type == "PARALLELOGRAM") shape = std::make_shared<Parallelogram>();
                else if (type == "CURVE") shape = std::make_shared<Curve>();
                else if (type == "POLYLINE") shape = std::make_shared<PolylineShape>();

                if (shape) {
                    shape->Deserialize(line);
                    g_shapes.push_back(shape);
                }
            }
            file.close();
            g_statusText = L"文件加载成功";
            InvalidateRect(hWnd, nullptr, FALSE);
        }
    }
}

// Helper function: Calculate line-line intersection
bool LineLineIntersection(D2D1_POINT_2F p1, D2D1_POINT_2F p2, D2D1_POINT_2F p3, D2D1_POINT_2F p4, 
                          D2D1_POINT_2F& intersection) {
    float x1 = p1.x, y1 = p1.y;
    float x2 = p2.x, y2 = p2.y;
    float x3 = p3.x, y3 = p3.y;
    float x4 = p4.x, y4 = p4.y;
    
    float denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
    if (fabs(denom) < 0.001f) return false;
    
    float t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
    float u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom;
    
    // Check if intersection is within both line segments
    if (t < 0.0f || t > 1.0f || u < 0.0f || u > 1.0f) return false;
    
    intersection.x = x1 + t * (x2 - x1);
    intersection.y = y1 + t * (y2 - y1);
    return true;
}

// Helper function: Calculate line-circle intersection
int LineCircleIntersection(D2D1_POINT_2F p1, D2D1_POINT_2F p2, D2D1_POINT_2F center, float radius,
                           D2D1_POINT_2F& int1, D2D1_POINT_2F& int2) {
    float dx = p2.x - p1.x;
    float dy = p2.y - p1.y;
    float fx = p1.x - center.x;
    float fy = p1.y - center.y;
    
    float a = dx * dx + dy * dy;
    float b = 2 * (fx * dx + fy * dy);
    float c = fx * fx + fy * fy - radius * radius;
    
    float discriminant = b * b - 4 * a * c;
    if (discriminant < 0) return 0;
    
    discriminant = sqrt(discriminant);
    float t1 = (-b - discriminant) / (2 * a);
    float t2 = (-b + discriminant) / (2 * a);
    
    int count = 0;
    if (t1 >= 0 && t1 <= 1) {
        int1.x = p1.x + t1 * dx;
        int1.y = p1.y + t1 * dy;
        count++;
    }
    if (t2 >= 0 && t2 <= 1 && fabs(t2 - t1) > 0.001f) {
        if (count == 0) {
            int1.x = p1.x + t2 * dx;
            int1.y = p1.y + t2 * dy;
        } else {
            int2.x = p1.x + t2 * dx;
            int2.y = p1.y + t2 * dy;
        }
        count++;
    }
    return count;
}

// Helper function: Calculate circle-circle intersection
int CircleCircleIntersection(D2D1_POINT_2F c1, float r1, D2D1_POINT_2F c2, float r2,
                             D2D1_POINT_2F& int1, D2D1_POINT_2F& int2) {
    float dx = c2.x - c1.x;
    float dy = c2.y - c1.y;
    float dist = sqrt(dx * dx + dy * dy);
    
    if (dist > r1 + r2 || dist < fabs(r1 - r2) || dist < 0.001f) return 0;
    
    float a = (r1 * r1 - r2 * r2 + dist * dist) / (2 * dist);
    float h = sqrt(r1 * r1 - a * a);
    
    float px = c1.x + a * dx / dist;
    float py = c1.y + a * dy / dist;
    
    int1.x = px + h * dy / dist;
    int1.y = py - h * dx / dist;
    int2.x = px - h * dy / dist;
    int2.y = py + h * dx / dist;
    
    return (h > 0.001f) ? 2 : 1;
}

// Calculate intersections
void CalculateIntersections()
{
    if (!g_calcShape1 || !g_calcShape2) return;
    
    std::vector<D2D1_POINT_2F> intersections;
    
    // Get all edges from shapes
    auto getEdges = [](Shape* shape) -> std::vector<std::pair<D2D1_POINT_2F, D2D1_POINT_2F>> {
        std::vector<std::pair<D2D1_POINT_2F, D2D1_POINT_2F>> edges;
        if (shape->type == ShapeType::LINE) {
            Line* line = dynamic_cast<Line*>(shape);
            edges.push_back({line->start, line->end});
        } else if (shape->type == ShapeType::RECTANGLE) {
            RectangleShape* rect = dynamic_cast<RectangleShape*>(shape);
            edges.push_back({rect->p1, rect->p2});
            edges.push_back({rect->p2, rect->p3});
            edges.push_back({rect->p3, rect->p4});
            edges.push_back({rect->p4, rect->p1});
        } else if (shape->type == ShapeType::TRIANGLE) {
            Triangle* tri = dynamic_cast<Triangle*>(shape);
            edges.push_back({tri->p1, tri->p2});
            edges.push_back({tri->p2, tri->p3});
            edges.push_back({tri->p3, tri->p1});
        } else if (shape->type == ShapeType::DIAMOND) {
            Diamond* dia = dynamic_cast<Diamond*>(shape);
            dia->UpdateVertices();  // Ensure vertices are up to date
            edges.push_back({dia->top, dia->right});
            edges.push_back({dia->right, dia->bottom});
            edges.push_back({dia->bottom, dia->left});
            edges.push_back({dia->left, dia->top});
        } else if (shape->type == ShapeType::PARALLELOGRAM) {
            Parallelogram* para = dynamic_cast<Parallelogram*>(shape);
            edges.push_back({para->p1, para->p2});
            edges.push_back({para->p2, para->p3});
            edges.push_back({para->p3, para->p4});
            edges.push_back({para->p4, para->p1});
        } else if (shape->type == ShapeType::POLYLINE) {
            PolylineShape* poly = dynamic_cast<PolylineShape*>(shape);
            for (size_t i = 0; i < poly->polyPoints.size() - 1; i++) {
                edges.push_back({poly->polyPoints[i], poly->polyPoints[i + 1]});
            }
        } else if (shape->type == ShapeType::CURVE) {
            Curve* curve = dynamic_cast<Curve*>(shape);
            // Use sampled points from the actual Bezier curve instead of control points
            auto sampledPoints = curve->GetSampledPoints(10);
            for (size_t i = 0; i < sampledPoints.size() - 1; i++) {
                edges.push_back({sampledPoints[i], sampledPoints[i + 1]});
            }
        }
        return edges;
    };
    
    // Line-Line, Line-Polygon, Polygon-Polygon
    if (g_calcShape1->type != ShapeType::CIRCLE && g_calcShape2->type != ShapeType::CIRCLE) {
        auto edges1 = getEdges(g_calcShape1);
        auto edges2 = getEdges(g_calcShape2);
        
        for (auto& e1 : edges1) {
            for (auto& e2 : edges2) {
                D2D1_POINT_2F pt;
                if (LineLineIntersection(e1.first, e1.second, e2.first, e2.second, pt)) {
                    // Check for duplicates (within 1 pixel tolerance)
                    bool isDuplicate = false;
                    for (const auto& existing : intersections) {
                        float dx = pt.x - existing.x;
                        float dy = pt.y - existing.y;
                        if (sqrt(dx * dx + dy * dy) < 1.0f) {
                            isDuplicate = true;
                            break;
                        }
                    }
                    if (!isDuplicate) {
                        intersections.push_back(pt);
                    }
                }
            }
        }
    }
    // Line-Circle
    else if ((g_calcShape1->type == ShapeType::CIRCLE && g_calcShape2->type != ShapeType::CIRCLE) ||
             (g_calcShape2->type == ShapeType::CIRCLE && g_calcShape1->type != ShapeType::CIRCLE)) {
        Circle* circle = (g_calcShape1->type == ShapeType::CIRCLE) ? 
                         dynamic_cast<Circle*>(g_calcShape1) : dynamic_cast<Circle*>(g_calcShape2);
        Shape* other = (g_calcShape1->type == ShapeType::CIRCLE) ? g_calcShape2 : g_calcShape1;
        
        auto edges = getEdges(other);
        for (auto& edge : edges) {
            D2D1_POINT_2F int1, int2;
            int count = LineCircleIntersection(edge.first, edge.second, circle->center, circle->radius, int1, int2);
            if (count >= 1) intersections.push_back(int1);
            if (count >= 2) intersections.push_back(int2);
        }
    }
    // Circle-Circle
    else if (g_calcShape1->type == ShapeType::CIRCLE && g_calcShape2->type == ShapeType::CIRCLE) {
        Circle* c1 = dynamic_cast<Circle*>(g_calcShape1);
        Circle* c2 = dynamic_cast<Circle*>(g_calcShape2);
        D2D1_POINT_2F int1, int2;
        int count = CircleCircleIntersection(c1->center, c1->radius, c2->center, c2->radius, int1, int2);
        if (count >= 1) intersections.push_back(int1);
        if (count >= 2) intersections.push_back(int2);
    }
    
    // Display results
    if (intersections.empty()) {
        g_statusText = L"未找到交点";
    } else {
        std::wstring result = L"交点坐标：";
        for (size_t i = 0; i < intersections.size() && i < 5; i++) {
            wchar_t buf[64];
            swprintf_s(buf, L"(%.1f, %.1f) ", intersections[i].x, intersections[i].y);
            result += buf;
        }
        if (intersections.size() > 5) {
            result += L"...";
        }
        g_statusText = result;
        
        // Draw intersection points
        for (auto& pt : intersections) {
            float r = 3.0f;
            auto mark1 = std::make_shared<Line>(
                D2D1::Point2F(pt.x - r, pt.y - r),
                D2D1::Point2F(pt.x + r, pt.y + r));
            auto mark2 = std::make_shared<Line>(
                D2D1::Point2F(pt.x - r, pt.y + r),
                D2D1::Point2F(pt.x + r, pt.y - r));
            mark1->color = mark2->color = D2D1::ColorF(D2D1::ColorF::Red);
            g_shapes.push_back(mark1);
            g_shapes.push_back(mark2);
        }
    }
}

// Draw perpendicular line
void DrawPerpendicular(D2D1_POINT_2F clickPoint, Line* line)
{
    float dx = line->end.x - line->start.x;
    float dy = line->end.y - line->start.y;

    float perpDx = -dy;
    float perpDy = dx;
    float len = sqrt(perpDx * perpDx + perpDy * perpDy);
    if (len > 0.001f) {
        perpDx = perpDx / len * 100;
        perpDy = perpDy / len * 100;
    }

    D2D1_POINT_2F p1 = D2D1::Point2F(clickPoint.x - perpDx, clickPoint.y - perpDy);
    D2D1_POINT_2F p2 = D2D1::Point2F(clickPoint.x + perpDx, clickPoint.y + perpDy);

    auto perpLine = std::make_shared<Line>(p1, p2);
    perpLine->color = D2D1::ColorF(D2D1::ColorF::Green);
    g_shapes.push_back(perpLine);
    g_statusText = L"垂线已绘制";
}

// Show circle center
void ShowCenter(Circle* circle)
{
    wchar_t buf[256];
    swprintf_s(buf, L"圆心坐标：(%.1f, %.1f)", circle->center.x, circle->center.y);
    g_statusText = buf;

    float r = 5.0f;
    auto mark1 = std::make_shared<Line>(
        D2D1::Point2F(circle->center.x - r, circle->center.y),
        D2D1::Point2F(circle->center.x + r, circle->center.y));
    auto mark2 = std::make_shared<Line>(
        D2D1::Point2F(circle->center.x, circle->center.y - r),
        D2D1::Point2F(circle->center.x, circle->center.y + r));
    mark1->color = mark2->color = D2D1::ColorF(D2D1::ColorF::Red);
    g_shapes.push_back(mark1);
    g_shapes.push_back(mark2);
}

// Draw tangent line
void DrawTangent(D2D1_POINT_2F point, Circle* circle)
{
    float dx = point.x - circle->center.x;
    float dy = point.y - circle->center.y;
    float dist = sqrt(dx * dx + dy * dy);

    if (dist < circle->radius) {
        g_statusText = L"点在圆内，无法绘制切线";
        return;
    }

    float a = circle->radius * circle->radius / dist;
    float h = sqrt(circle->radius * circle->radius - a * a);

    float px = circle->center.x + a * dx / dist;
    float py = circle->center.y + a * dy / dist;

    D2D1_POINT_2F t1 = D2D1::Point2F(px - h * dy / dist, py + h * dx / dist);
    D2D1_POINT_2F t2 = D2D1::Point2F(px + h * dy / dist, py - h * dx / dist);

    auto tangent1 = std::make_shared<Line>(point, t1);
    auto tangent2 = std::make_shared<Line>(point, t2);
    tangent1->color = tangent2->color = D2D1::ColorF(D2D1::ColorF::Purple);
    g_shapes.push_back(tangent1);
    g_shapes.push_back(tangent2);

    wchar_t buf[256];
    swprintf_s(buf, L"Tangent point 1: (%.1f, %.1f), Point 2: (%.1f, %.1f)", t1.x, t1.y, t2.x, t2.y);
    g_statusText = buf;
}

// Save current state to undo stack
void SaveStateToUndoStack()
{
    // Deep copy all shapes
    std::vector<std::shared_ptr<Shape>> stateCopy;
    for (const auto& shape : g_shapes) {
        std::shared_ptr<Shape> newShape;
        std::string data = shape->Serialize();
        
        if (shape->type == ShapeType::LINE) newShape = std::make_shared<Line>();
        else if (shape->type == ShapeType::CIRCLE) newShape = std::make_shared<Circle>();
        else if (shape->type == ShapeType::RECTANGLE) newShape = std::make_shared<RectangleShape>();
        else if (shape->type == ShapeType::TRIANGLE) newShape = std::make_shared<Triangle>();
        else if (shape->type == ShapeType::DIAMOND) newShape = std::make_shared<Diamond>();
        else if (shape->type == ShapeType::PARALLELOGRAM) newShape = std::make_shared<Parallelogram>();
        else if (shape->type == ShapeType::CURVE) newShape = std::make_shared<Curve>();
        else if (shape->type == ShapeType::POLYLINE) newShape = std::make_shared<PolylineShape>();
        
        if (newShape) {
            newShape->Deserialize(data);
            stateCopy.push_back(newShape);
        }
    }
    
    g_undoStack.push_back(stateCopy);
    
    // Limit undo stack size
    if (g_undoStack.size() > MAX_UNDO_STEPS) {
        g_undoStack.erase(g_undoStack.begin());
    }
    
    // Clear redo stack when new action is performed
    g_redoStack.clear();
}
