#include <windows.h>
#include <d2d1.h>
#include <vector>
#include <new>
#include <cmath>

#pragma comment(lib, "d2d1.lib")

// Global Direct2D Factory
ID2D1Factory* g_pFactory = NULL;

// Shape base class
class Shape {
public:
    virtual ~Shape() {}
    virtual void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) = 0;
};

// Line class
class MyLine : public Shape {
public:
    MyLine(float x1, float y1, float x2, float y2, float r, float g, float b, float width) {
        this->x1 = x1; this->y1 = y1; this->x2 = x2; this->y2 = y2;
        this->r = r; this->g = g; this->b = b; this->width = width;
    }

    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
        pBrush->SetColor(D2D1::ColorF(r, g, b));
        pRT->DrawLine(D2D1::Point2F(x1, y1), D2D1::Point2F(x2, y2), pBrush, width);
    }

private:
    float x1, y1, x2, y2;
    float r, g, b;
    float width;
};

// Rectangle class
class MyRect : public Shape {
public:
    MyRect(float x1, float y1, float x2, float y2, float r, float g, float b, float width) {
        this->x1 = x1; this->y1 = y1; this->x2 = x2; this->y2 = y2;
        this->r = r; this->g = g; this->b = b; this->width = width;
    }

    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
        pBrush->SetColor(D2D1::ColorF(r, g, b));
        pRT->DrawRectangle(D2D1::RectF(x1, y1, x2, y2), pBrush, width);
    }

private:
    float x1, y1, x2, y2;
    float r, g, b;
    float width;
};

// Ellipse class
class MyEllipse : public Shape {
public:
    MyEllipse(float cx, float cy, float rx, float ry, float r, float g, float b, float width) {
        this->cx = cx; this->cy = cy; this->rx = rx; this->ry = ry;
        this->r = r; this->g = g; this->b = b; this->width = width;
    }

    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
        pBrush->SetColor(D2D1::ColorF(r, g, b));
        pRT->DrawEllipse(D2D1::Ellipse(D2D1::Point2F(cx, cy), rx, ry), pBrush, width);
    }

private:
    float cx, cy, rx, ry;
    float r, g, b;
    float width;
};

// Simple Arc class - using center, radius and two endpoints
class MyArc : public Shape {
public:
    MyArc(float cx, float cy, float radius, float startX, float startY, float endX, float endY, 
          bool clockwise, float r, float g, float b, float width) {
        this->cx = cx; this->cy = cy; this->radius = radius;
        this->startX = startX; this->startY = startY;
        this->endX = endX; this->endY = endY;
        this->clockwise = clockwise;
        this->r = r; this->g = g; this->b = b; this->width = width;
    }

    void Draw(ID2D1RenderTarget* pRT, ID2D1SolidColorBrush* pBrush) {
        if (!pRT || !pBrush) return;
        
        pBrush->SetColor(D2D1::ColorF(r, g, b));

        const float PI = 3.14159265f;
        float startAngle = (float)atan2(startY - cy, startX - cx);
        float endAngle = (float)atan2(endY - cy, endX - cx);
        
        if (startAngle < 0) startAngle += 2.0f * PI;
        if (endAngle < 0) endAngle += 2.0f * PI;
        
        if (!clockwise && endAngle < startAngle) {
            endAngle += 2.0f * PI;
        } else if (clockwise && startAngle < endAngle) {
            startAngle += 2.0f * PI;
        }
        
        int segments = 100;
        float angleStep = 0.0f;
        
        if (clockwise) {
            angleStep = (startAngle - endAngle) / (float)segments;
        } else {
            angleStep = (endAngle - startAngle) / (float)segments;
        }
        
        for (int i = 0; i < segments; i++) {
            float angle1 = 0.0f;
            float angle2 = 0.0f;
            
            if (clockwise) {
                angle1 = startAngle - (float)i * angleStep;
                angle2 = startAngle - (float)(i + 1) * angleStep;
            } else {
                angle1 = startAngle + (float)i * angleStep;
                angle2 = startAngle + (float)(i + 1) * angleStep;
            }
            
            float x1 = cx + radius * (float)cos(angle1);
            float y1 = cy + radius * (float)sin(angle1);
            float x2 = cx + radius * (float)cos(angle2);
            float y2 = cy + radius * (float)sin(angle2);
            
            pRT->DrawLine(D2D1::Point2F(x1, y1), D2D1::Point2F(x2, y2), pBrush, width);
        }
    }

private:
    float cx, cy, radius;
    float startX, startY, endX, endY;
    bool clockwise;
    float r, g, b;
    float width;
};

// Global shape list
std::vector<Shape*> g_shapes;

// Window procedure
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    static ID2D1HwndRenderTarget* pRT = NULL;
    static ID2D1SolidColorBrush* pBrush = NULL;

    switch (msg) {
    case WM_CREATE: {
        // Initialize Direct2D
        HRESULT hr = D2D1CreateFactory(D2D1_FACTORY_TYPE_SINGLE_THREADED, &g_pFactory);
        if (FAILED(hr) || !g_pFactory) {
            MessageBox(hwnd, "Failed to create Direct2D factory", "Error", MB_OK | MB_ICONERROR);
            return -1;
        }

        // Create shapes - use try-catch to protect memory allocation
        try {
            g_shapes.push_back(new MyEllipse(150, 300, 40, 40, 0.0f, 0.0f, 0.0f, 2.0f)); //yuan A r40
            g_shapes.push_back(new MyArc(150, 300, 64, 212.98, 311.38, 109.28, 250.62, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(87, 223.6, 35, 109.28, 250.62, 122, 223.6, true, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyLine(122, 134, 122, 223.6, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(150, 134, 28, 122, 134, 178, 134, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(150, 134, 14, 136, 134, 164, 134, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyLine(136, 134, 136, 212, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyLine(164, 134, 164, 212, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(150, 212, 14, 136, 212, 164, 212, true, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyLine(178, 134, 178, 155.19, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(208, 155.19, 30, 178, 155.19, 197.5, 183.3, true, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(150, 300, 126, 197.5, 183.3, 274.09, 278.12, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(250.4, 282.3, 12, 238.6, 284.38, 262.2, 280.22, true, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(215.5, 221.9, 12, 207.8, 231, 223.2, 212.8, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(150, 300, 90, 207.8, 231, 238.6, 284.38, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(150, 300, 114, 223.2, 212.8, 262.2, 280.22, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(250.4,282.3,24,274.09,278.12,236.46,301.83, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(227.74,314.04,15,212.98,311.38,236.46,301.04, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(150,56,6,144.78,52.96,155.22,52.96,false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(188,78.1,50,144.78,52.96,142.54,98.93,true, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(112,78.1,50,155.22,52.96,157.46,98.93,false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(136.18,101.84,7,142.54,98.93,139.48,108.02, false, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyArc(163.82,101.84,7,157.46,98.93,160.52,108.02,true, 0.0f, 0.0f, 0.0f, 2.0f));
            g_shapes.push_back(new MyLine(172.5,117.5,251.6,225.7, 0.0f, 0.0f, 0.0f, 2.0f));
        }
        catch (const std::bad_alloc&) {
            MessageBox(hwnd, "Memory allocation failed", "Error", MB_OK | MB_ICONERROR);
            return -1;
        }
        return 0;
    }

    case WM_PAINT: {
        PAINTSTRUCT ps;
        BeginPaint(hwnd, &ps);

        // Create render target
        if (!pRT && g_pFactory) {
            RECT rc;
            GetClientRect(hwnd, &rc);
            
            if (rc.right > 0 && rc.bottom > 0) {
                HRESULT hr = g_pFactory->CreateHwndRenderTarget(
                    D2D1::RenderTargetProperties(),
                    D2D1::HwndRenderTargetProperties(hwnd, D2D1::SizeU(rc.right, rc.bottom)),
                    &pRT
                );

                // Create brush
                if (SUCCEEDED(hr) && pRT) {
                    hr = pRT->CreateSolidColorBrush(D2D1::ColorF(0, 0, 0), &pBrush);
                }
                
                if (FAILED(hr)) {
                    if (pBrush) { pBrush->Release(); pBrush = NULL; }
                    if (pRT) { pRT->Release(); pRT = NULL; }
                    EndPaint(hwnd, &ps);
                    return 0;
                }
            }
        }

        if (pRT && pBrush) {
            pRT->BeginDraw();
            pRT->Clear(D2D1::ColorF(1.0f, 1.0f, 1.0f));

            // Draw all shapes
            for (size_t i = 0; i < g_shapes.size(); ++i) {
                if (g_shapes[i]) {
                    g_shapes[i]->Draw(pRT, pBrush);
                }
            }

            HRESULT hr = pRT->EndDraw();
            if (hr == D2DERR_RECREATE_TARGET) {
                // Need to recreate render target
                if (pBrush) { pBrush->Release(); pBrush = NULL; }
                if (pRT) { pRT->Release(); pRT = NULL; }
            }
        }
        
        EndPaint(hwnd, &ps);
        return 0;
    }

    case WM_SIZE: {
        if (pRT) {
            RECT rc;
            GetClientRect(hwnd, &rc);
            if (rc.right > 0 && rc.bottom > 0) {
                HRESULT hr = pRT->Resize(D2D1::SizeU(rc.right, rc.bottom));
                if (FAILED(hr)) {
                    // If resize fails, release render target for recreation
                    if (pBrush) { pBrush->Release(); pBrush = NULL; }
                    if (pRT) { pRT->Release(); pRT = NULL; }
                }
                InvalidateRect(hwnd, NULL, FALSE);
            }
        }
        return 0;
    }

    case WM_DESTROY:
        // Clean up resources
        for (size_t i = 0; i < g_shapes.size(); ++i) {
            if (g_shapes[i]) {
                delete g_shapes[i];
                g_shapes[i] = NULL;
            }
        }
        g_shapes.clear();
        
        if (pBrush) { 
            pBrush->Release(); 
            pBrush = NULL; 
        }
        if (pRT) { 
            pRT->Release(); 
            pRT = NULL; 
        }
        if (g_pFactory) { 
            g_pFactory->Release(); 
            g_pFactory = NULL; 
        }
        PostQuitMessage(0);
        return 0;
    }

    return DefWindowProc(hwnd, msg, wParam, lParam);
}

// Entry point function
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    const char CLASS_NAME[] = "Direct2D Window";

    // Register window class
    WNDCLASS wc = { 0 };
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = CLASS_NAME;
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);

    RegisterClass(&wc);

    // Create window
    HWND hwnd = CreateWindowEx(
        0,
        CLASS_NAME,
        "Direct2D Multi-Shape Drawing",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 400, 500,
        NULL, NULL, hInstance, NULL
    );

    if (!hwnd) {
        return 0;
    }

    ShowWindow(hwnd, nCmdShow);

    // Message loop
    MSG msg = { 0 };
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}