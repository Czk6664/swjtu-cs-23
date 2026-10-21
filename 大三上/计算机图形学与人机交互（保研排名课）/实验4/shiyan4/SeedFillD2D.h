#pragma once
#include "framework.h"
#include <queue>
#include <vector>
#include <memory>

// 前向声明
class Shape;

// 外部声明全局D2D工厂
extern ID2D1Factory* g_pD2DFactory;

// Direct2D Seed Fill Implementation
class SeedFillD2D {
public:
    // Perform seed fill on Direct2D render target, returns filled bitmap
    static ID2D1Bitmap* Fill(ID2D1HwndRenderTarget* pRT, int seedX, int seedY, D2D1_COLOR_F fillColor, 
                             const std::vector<std::shared_ptr<Shape>>& shapes) {
        if (!pRT || !g_pD2DFactory) return nullptr;
        
        // Get render target size
        D2D1_SIZE_U size = pRT->GetPixelSize();
        
        // Create WIC bitmap to access pixels
        IWICImagingFactory* pWICFactory = nullptr;
        HRESULT hr = CoCreateInstance(
            CLSID_WICImagingFactory,
            nullptr,
            CLSCTX_INPROC_SERVER,
            IID_PPV_ARGS(&pWICFactory)
        );
        if (FAILED(hr) || !pWICFactory) return nullptr;
        
        // Create WIC bitmap
        IWICBitmap* pWICBitmap = nullptr;
        hr = pWICFactory->CreateBitmap(
            size.width,
            size.height,
            GUID_WICPixelFormat32bppPBGRA,
            WICBitmapCacheOnDemand,
            &pWICBitmap
        );
        
        if (FAILED(hr) || !pWICBitmap) {
            pWICFactory->Release();
            return nullptr;
        }
        
        // Create D2D render target for WIC bitmap
        ID2D1RenderTarget* pWICRenderTarget = nullptr;
        D2D1_RENDER_TARGET_PROPERTIES rtProps = D2D1::RenderTargetProperties(
            D2D1_RENDER_TARGET_TYPE_DEFAULT,
            D2D1::PixelFormat(DXGI_FORMAT_B8G8R8A8_UNORM, D2D1_ALPHA_MODE_PREMULTIPLIED),
            0, 0, D2D1_RENDER_TARGET_USAGE_NONE, D2D1_FEATURE_LEVEL_DEFAULT
        );
        
        hr = g_pD2DFactory->CreateWicBitmapRenderTarget(pWICBitmap, rtProps, &pWICRenderTarget);
        if (FAILED(hr) || !pWICRenderTarget) {
            pWICBitmap->Release();
            pWICFactory->Release();
            return nullptr;
        }
        
        // Create a brush for drawing shapes
        ID2D1SolidColorBrush* pBrush = nullptr;
        hr = pWICRenderTarget->CreateSolidColorBrush(D2D1::ColorF(D2D1::ColorF::Black), &pBrush);
        if (FAILED(hr) || !pBrush) {
            pWICRenderTarget->Release();
            pWICBitmap->Release();
            pWICFactory->Release();
            return nullptr;
        }
        
        // Draw shapes onto WIC bitmap (white background + black shapes)
        pWICRenderTarget->BeginDraw();
        pWICRenderTarget->Clear(D2D1::ColorF(D2D1::ColorF::White));
        
        // Draw all shapes
        for (const auto& shape : shapes) {
            if (shape) {
                shape->Draw(pWICRenderTarget, pBrush);
            }
        }
        
        pWICRenderTarget->EndDraw();
        pBrush->Release();
        pWICRenderTarget->Release();
        
        // Lock WIC bitmap to access pixels
        IWICBitmapLock* pLock = nullptr;
        WICRect rcLock = { 0, 0, (INT)size.width, (INT)size.height };
        hr = pWICBitmap->Lock(&rcLock, WICBitmapLockWrite, &pLock);
        if (FAILED(hr) || !pLock) {
            pWICBitmap->Release();
            pWICFactory->Release();
            return nullptr;
        }
        
        // Get pixel data
        UINT cbBufferSize = 0;
        BYTE* pixels = nullptr;
        hr = pLock->GetDataPointer(&cbBufferSize, &pixels);
        if (FAILED(hr) || !pixels) {
            pLock->Release();
            pWICBitmap->Release();
            pWICFactory->Release();
            return nullptr;
        }
        
        UINT pitch = 0;
        pLock->GetStride(&pitch);
        
        // Get target color at seed point
        if (seedX < 0 || seedX >= (int)size.width || seedY < 0 || seedY >= (int)size.height) {
            pLock->Release();
            pWICBitmap->Release();
            pWICFactory->Release();
            return nullptr;
        }
        
        UINT32 targetColor = GetPixelColor(pixels, pitch, seedX, seedY);
        UINT32 newColor = ColorToUInt32(fillColor);
        
        // Don't fill if colors are the same or too similar
        if (ColorsMatch(targetColor, newColor)) {
            pLock->Release();
            pWICBitmap->Release();
            pWICFactory->Release();
            return nullptr;
        }
        
        // Perform flood fill using scanline algorithm
        FloodFillScanline(pixels, pitch, size.width, size.height, seedX, seedY, targetColor, newColor);
        
        // Unlock WIC bitmap
        pLock->Release();
        
        // Create new D2D bitmap from filled WIC bitmap
        ID2D1Bitmap* pFilledBitmap = nullptr;
        hr = pRT->CreateBitmapFromWicBitmap(pWICBitmap, &pFilledBitmap);
        
        // Cleanup
        pWICBitmap->Release();
        pWICFactory->Release();
        
        // Return the filled bitmap (caller is responsible for releasing it)
        return pFilledBitmap;
    }

private:
    // Get pixel color at (x, y)
    static UINT32 GetPixelColor(BYTE* pixels, UINT32 pitch, int x, int y) {
        BYTE* pixel = pixels + y * pitch + x * 4;
        return *(UINT32*)pixel;
    }
    
    // Set pixel color at (x, y)
    static void SetPixelColor(BYTE* pixels, UINT32 pitch, int x, int y, UINT32 color) {
        BYTE* pixel = pixels + y * pitch + x * 4;
        *(UINT32*)pixel = color;
    }
    
    // Convert D2D1_COLOR_F to UINT32 (BGRA format)
    static UINT32 ColorToUInt32(D2D1_COLOR_F color) {
        BYTE b = (BYTE)(color.b * 255);
        BYTE g = (BYTE)(color.g * 255);
        BYTE r = (BYTE)(color.r * 255);
        BYTE a = (BYTE)(color.a * 255);
        return (a << 24) | (r << 16) | (g << 8) | b;
    }
    
    // Check if two colors match with tolerance and ignoring alpha
    static bool ColorsMatch(UINT32 c1, UINT32 c2) {
        // Memory layout is BGRA (Little Endian), so UINT32 value is 0xAARRGGBB
        // c & 0xFF is Blue
        // (c >> 8) & 0xFF is Green
        // (c >> 16) & 0xFF is Red
        
        int b1 = (c1) & 0xFF;
        int g1 = (c1 >> 8) & 0xFF;
        int r1 = (c1 >> 16) & 0xFF;
        
        int b2 = (c2) & 0xFF;
        int g2 = (c2 >> 8) & 0xFF;
        int r2 = (c2 >> 16) & 0xFF;
        
        // TOLERANCE: 5 is sufficient for in-memory rendering with anti-aliasing
        // while preventing leakage through boundaries
        const int TOLERANCE = 5;
        return abs(r1 - r2) <= TOLERANCE && abs(g1 - g2) <= TOLERANCE && abs(b1 - b2) <= TOLERANCE;
    }

    // Scanline flood fill algorithm
    static void FloodFillScanline(BYTE* pixels, UINT32 pitch, UINT32 width, UINT32 height,
                                   int seedX, int seedY, UINT32 targetColor, UINT32 newColor) {
        struct Span {
            int x1, x2, y, dy;
        };
        
        std::queue<Span> queue;
        
        // Fill the seed scanline first
        int left = seedX;
        int right = seedX;
        
        // Scan left from seed
        while (left > 0 && ColorsMatch(GetPixelColor(pixels, pitch, left - 1, seedY), targetColor)) {
            left--;
        }
        
        // Scan right from seed
        while (right < (int)width - 1 && ColorsMatch(GetPixelColor(pixels, pitch, right + 1, seedY), targetColor)) {
            right++;
        }
        
        // Fill the seed scanline
        for (int x = left; x <= right; x++) {
            SetPixelColor(pixels, pitch, x, seedY, newColor);
        }
        
        // Add spans above and below
        queue.push({left, right, seedY, 1});   // Scan upward
        queue.push({left, right, seedY, -1});  // Scan downward
        
        while (!queue.empty()) {
            Span span = queue.front();
            queue.pop();
            
            int y = span.y + span.dy;
            
            if (y < 0 || y >= (int)height) continue;
            
            // Scan this line for spans
            int x = span.x1;
            while (x <= span.x2) {
                // Skip non-target pixels
                while (x <= span.x2 && !ColorsMatch(GetPixelColor(pixels, pitch, x, y), targetColor)) {
                    x++;
                }
                
                if (x > span.x2) break;
                
                // Found a span, scan left
                int spanLeft = x;
                while (spanLeft > 0 && ColorsMatch(GetPixelColor(pixels, pitch, spanLeft - 1, y), targetColor)) {
                    spanLeft--;
                }
                
                // Scan right
                int spanRight = x;
                while (spanRight < (int)width - 1 && ColorsMatch(GetPixelColor(pixels, pitch, spanRight + 1, y), targetColor)) {
                    spanRight++;
                }
                
                // Fill this span
                for (int i = spanLeft; i <= spanRight; i++) {
                    SetPixelColor(pixels, pitch, i, y, newColor);
                }
                
                // Add new span to queue
                queue.push({spanLeft, spanRight, y, span.dy});
                
                // Also check in opposite direction
                queue.push({spanLeft, spanRight, y, -span.dy});
                
                x = spanRight + 1;
            }
        }
    }
};
