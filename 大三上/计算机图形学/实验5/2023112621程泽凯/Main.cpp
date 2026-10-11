// Main.cpp - 3D Graphics Editor
#include <windows.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <d3dcompiler.h>
#include <DirectXMath.h>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <new>

#include "Types.h"
#include "Globals.h"
#include "Geometry.h"
#include "Dialogs.h"

#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "d3dcompiler.lib")
#pragma comment(lib, "dxgi.lib")
#pragma comment(lib, "comdlg32.lib")

using namespace DirectX;

// Global variable definitions
HWND g_hWnd = nullptr;
ID3D11Device* g_pd3dDevice = nullptr;
ID3D11DeviceContext* g_pImmediateContext = nullptr;
IDXGISwapChain* g_pSwapChain = nullptr;
ID3D11RenderTargetView* g_pRenderTargetView = nullptr;
ID3D11DepthStencilView* g_pDepthStencilView = nullptr;
ID3D11VertexShader* g_pVertexShader = nullptr;
ID3D11PixelShader* g_pPixelShader = nullptr;
ID3D11InputLayout* g_pVertexLayout = nullptr;
ID3D11Buffer* g_pConstantBuffer = nullptr;
ID3D11RasterizerState* g_pRasterizerState = nullptr;
ID3D11RasterizerState* g_pWireframeState = nullptr;
ID3D11DepthStencilState* g_pDepthStencilState = nullptr;
ID3D11BlendState* g_pBlendState = nullptr;
ID3D11SamplerState* g_pSamplerState = nullptr;

std::vector<Shape3D*> g_shapes;
Shape3D* g_selectedShape = nullptr;
POINT g_lastMousePos = { 0, 0 };
bool g_isDragging = false;
bool g_cameraMode = false;
bool g_middleButtonDragging = false;
DWORD g_lastClickTime = 0;
std::wstring g_statusText = L"\u5de6\u952e:\u9009\u62e9/\u79fb\u52a8 | \u53f3\u952e/\u4e2d\u952e:\u65cb\u8f6c | \u6eda\u8f6e:Z\u8f74";
XMFLOAT3 g_dragOffset = { 0.0f, 0.0f, 0.0f };

float g_cameraYaw = -0.6f;
float g_cameraPitch = 0.4f;
float g_cameraDistance = CAMERA_DISTANCE;

bool g_showAxes = true;

ID3D11Buffer* g_pAxisXVertexBuffer = nullptr;
ID3D11Buffer* g_pAxisXIndexBuffer = nullptr;
UINT g_axisXIndexCount = 0;
ID3D11Buffer* g_pAxisYVertexBuffer = nullptr;
ID3D11Buffer* g_pAxisYIndexBuffer = nullptr;
UINT g_axisYIndexCount = 0;
ID3D11Buffer* g_pAxisZVertexBuffer = nullptr;
ID3D11Buffer* g_pAxisZIndexBuffer = nullptr;
UINT g_axisZIndexCount = 0;

ID3D11Buffer* g_pArrowXVertexBuffer = nullptr;
ID3D11Buffer* g_pArrowXIndexBuffer = nullptr;
UINT g_arrowXIndexCount = 0;
ID3D11Buffer* g_pArrowYVertexBuffer = nullptr;
ID3D11Buffer* g_pArrowYIndexBuffer = nullptr;
UINT g_arrowYIndexCount = 0;
ID3D11Buffer* g_pArrowZVertexBuffer = nullptr;
ID3D11Buffer* g_pArrowZIndexBuffer = nullptr;
UINT g_arrowZIndexCount = 0;

XMFLOAT3 g_axesOrigin = { 0.0f, 0.0f, 0.0f };
bool g_isDraggingOrigin = false;

XMFLOAT3 g_lightDirection = XMFLOAT3(0.577f, -0.577f, 0.577f);
XMFLOAT3 g_lightColor = XMFLOAT3(1.0f, 1.0f, 1.0f);

// Forward declarations
LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);
bool InitD3D();
void CleanupD3D();
void Render();
void GetCameraViewMatrix(XMMATRIX& outView, XMVECTOR& outEye);

// Shader code
const char* g_vertexShaderCode = R"(
cbuffer ConstantBuffer : register(b0) {
    matrix World; matrix View; matrix Projection;
    float4 LightDir; float4 LightColor; float4 CameraPos;
    float4 MatAmbient; float4 MatDiffuse; float4 MatSpecular; float4 MatEmissive; float4 TextureInfo; float4 MaterialExtra;
}
struct VS_INPUT { float3 Pos : POSITION; float3 Normal : NORMAL; float4 Color : COLOR; float2 TexCoord : TEXCOORD; };
struct PS_INPUT { float4 Pos : SV_POSITION; float3 Normal : NORMAL; float4 Color : COLOR; float3 WorldPos : TEXCOORD0; float2 TexCoord : TEXCOORD1; };
PS_INPUT main(VS_INPUT input) {
    PS_INPUT output;
    float4 worldPos = mul(float4(input.Pos, 1.0f), World);
    output.WorldPos = worldPos.xyz;
    output.Pos = mul(mul(worldPos, View), Projection);
    output.Normal = mul(input.Normal, (float3x3)World);
    output.Color = input.Color;
    output.TexCoord = input.TexCoord;
    return output;
}
)";

const char* g_pixelShaderCode = R"(
Texture2D texDiffuse : register(t0);
SamplerState samLinear : register(s0);
cbuffer ConstantBuffer : register(b0) {
    matrix World; matrix View; matrix Projection;
    float4 LightDir; float4 LightColor; float4 CameraPos;
    float4 MatAmbient; float4 MatDiffuse; float4 MatSpecular; float4 MatEmissive; float4 TextureInfo; float4 MaterialExtra;
}
struct PS_INPUT { float4 Pos : SV_POSITION; float3 Normal : NORMAL; float4 Color : COLOR; float3 WorldPos : TEXCOORD0; float2 TexCoord : TEXCOORD1; };
float4 main(PS_INPUT input) : SV_Target {
    float3 normal = normalize(input.Normal);
    float3 lightDir = normalize(-LightDir.xyz);
    float3 baseColor = input.Color.rgb;
    float alpha = input.Color.a;
    int texMode = (int)TextureInfo.x;
    if (texMode > 0) {
        float4 texColor = texDiffuse.Sample(samLinear, input.TexCoord);
        if (texMode == 1) { baseColor = texColor.rgb * MatDiffuse.rgb; alpha = texColor.a * input.Color.a; }
        else if (texMode == 2) { baseColor = texColor.rgb; alpha = texColor.a; }
    }
    float3 ambient = MatAmbient.rgb * LightColor.rgb;
    float NdotL = max(dot(normal, lightDir), 0.0f);
    float3 diffuse = MatDiffuse.rgb * NdotL * LightColor.rgb;
    float3 viewDir = normalize(CameraPos.xyz - input.WorldPos);
    float3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0f), MatSpecular.w);
    float3 specular = MatSpecular.rgb * spec * LightColor.rgb;
    float3 emissive = MatEmissive.rgb;
    float3 finalColor = (ambient + diffuse + specular) * baseColor + emissive;
    return float4(saturate(finalColor), alpha);
}
)";

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow)
{
    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.lpszClassName = L"D3DWindowClass";
    RegisterClassExW(&wc);

    HMENU hMenu = CreateMenu();
    HMENU hSubMenu = CreatePopupMenu();
    AppendMenuW(hSubMenu, MF_STRING, IDM_SPHERE, L"\u7403\u4f53");
    AppendMenuW(hSubMenu, MF_STRING, IDM_CYLINDER, L"\u67f1\u4f53");
    AppendMenuW(hSubMenu, MF_STRING, IDM_PLANE, L"\u5e73\u9762");
    AppendMenuW(hSubMenu, MF_STRING, IDM_CUBE, L"\u516d\u9762\u4f53");
    AppendMenuW(hSubMenu, MF_STRING, IDM_TETRAHEDRON, L"\u56db\u9762\u4f53");
    AppendMenuW(hSubMenu, MF_SEPARATOR, 0, nullptr);
    AppendMenuW(hSubMenu, MF_STRING, IDM_EXIT, L"\u9000\u51fa");
    AppendMenuW(hMenu, MF_POPUP, (UINT_PTR)hSubMenu, L"\u7ed8\u5236");

    HMENU hViewMenu = CreatePopupMenu();
    AppendMenuW(hViewMenu, MF_STRING, IDM_CAMERA_MODE, L"\u6444\u50cf\u673a\u6a21\u5f0f");
    AppendMenuW(hViewMenu, MF_STRING | MF_CHECKED, IDM_SHOW_AXES, L"\u663e\u793a\u5750\u6807\u8f74");
    AppendMenuW(hViewMenu, MF_STRING, IDM_LIGHT_SETTINGS, L"\u5149\u7167\u8bbe\u7f6e");
    AppendMenuW(hMenu, MF_POPUP, (UINT_PTR)hViewMenu, L"\u89c6\u56fe");

    HMENU hEditMenu = CreatePopupMenu();
    AppendMenuW(hEditMenu, MF_STRING, IDM_DELETE_SHAPE, L"\u5220\u9664\tDelete");
    AppendMenuW(hEditMenu, MF_SEPARATOR, 0, nullptr);
    AppendMenuW(hEditMenu, MF_STRING, IDM_MATERIAL_SETTINGS, L"\u6750\u8d28\u8bbe\u7f6e");
    AppendMenuW(hEditMenu, MF_STRING, IDM_TEXTURE_SETTINGS, L"\u7eb9\u7406\u8bbe\u7f6e");
    AppendMenuW(hMenu, MF_POPUP, (UINT_PTR)hEditMenu, L"\u7f16\u8f91");

    RECT rc = { 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT };
    AdjustWindowRect(&rc, WS_OVERLAPPEDWINDOW, TRUE);
    g_hWnd = CreateWindowW(L"D3DWindowClass", L"3D\u56fe\u5f62\u7f16\u8f91\u5668",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
        rc.right - rc.left, rc.bottom - rc.top,
        nullptr, hMenu, hInstance, nullptr);

    if (!g_hWnd) return 0;
    ShowWindow(g_hWnd, nCmdShow);
    UpdateWindow(g_hWnd);
    if (!InitD3D()) return 0;

    MSG msg = {};
    while (msg.message != WM_QUIT) {
        if (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg); DispatchMessage(&msg);
        } else {
            Render();
        }
    }
    CleanupD3D();
    return (int)msg.wParam;
}


LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_COMMAND:
    {
        int wmId = LOWORD(wParam);
        if (wmId >= IDM_SPHERE && wmId <= IDM_TETRAHEDRON) {
            ShapeType shapeTypes[] = { SHAPE_SPHERE, SHAPE_CYLINDER, SHAPE_PLANE, SHAPE_CUBE, SHAPE_TETRAHEDRON };
            Shape3D* newShape = CreateShape(shapeTypes[wmId - IDM_SPHERE]);
            if (newShape) g_shapes.push_back(newShape);
            break;
        }
        switch (wmId) {
        case IDM_CAMERA_MODE:
            g_cameraMode = !g_cameraMode;
            CheckMenuItem(GetMenu(hWnd), IDM_CAMERA_MODE, g_cameraMode ? MF_CHECKED : MF_UNCHECKED);
            g_statusText = g_cameraMode ? L"\u6444\u50cf\u673a\u6a21\u5f0f: \u53f3\u952e/\u4e2d\u952e:\u65cb\u8f6c | \u6eda\u8f6e:\u7f29\u653e" : L"\u5de6\u952e:\u9009\u62e9/\u79fb\u52a8 | \u53f3\u952e/\u4e2d\u952e:\u65cb\u8f6c | \u6eda\u8f6e:Z\u8f74";
            break;
        case IDM_LIGHT_SETTINGS:
        {
            DLGTEMPLATE* pTemplate = CreateLightSettingsDialogTemplate();
            DialogBoxIndirectW(GetModuleHandle(nullptr), pTemplate, hWnd, LightSettingsDlgProc);
            break;
        }
        case IDM_MATERIAL_SETTINGS:
            if (g_selectedShape) {
                DLGTEMPLATE* pTemplate = CreateShapePropertiesDialogTemplate();
                DialogBoxIndirectW(GetModuleHandle(nullptr), pTemplate, hWnd, MaterialSettingsDlgProc);
            } else {
                g_statusText = L"\u8bf7\u5148\u9009\u62e9\u4e00\u4e2a\u5b9e\u4f53";
            }
            break;
        case IDM_TEXTURE_SETTINGS:
            if (g_selectedShape) {
                DLGTEMPLATE* pTemplate = CreateShapePropertiesDialogTemplate();
                DialogBoxIndirectW(GetModuleHandle(nullptr), pTemplate, hWnd, TextureSettingsDlgProc);
            } else {
                g_statusText = L"\u8bf7\u5148\u9009\u62e9\u4e00\u4e2a\u5b9e\u4f53";
            }
            break;
        case IDM_SHOW_AXES:
            g_showAxes = !g_showAxes;
            CheckMenuItem(GetMenu(hWnd), IDM_SHOW_AXES, g_showAxes ? MF_CHECKED : MF_UNCHECKED);
            break;
        case IDM_DELETE_SHAPE:
            if (g_selectedShape) {
                auto it = std::find(g_shapes.begin(), g_shapes.end(), g_selectedShape);
                if (it != g_shapes.end()) g_shapes.erase(it);
                delete g_selectedShape;
                g_selectedShape = nullptr;
                g_statusText = L"\u5df2\u5220\u9664\u56fe\u5f62";
            } else {
                g_statusText = L"\u8bf7\u5148\u9009\u62e9\u8981\u5220\u9664\u7684\u56fe\u5f62";
            }
            break;
        case IDM_EXIT:
            DestroyWindow(hWnd);
            break;
        }
        break;
    }
    case WM_LBUTTONDOWN:
    {
        int x = LOWORD(lParam);
        int y = HIWORD(lParam);
        DWORD currentTime = GetTickCount();
        bool isDoubleClick = (currentTime - g_lastClickTime) < GetDoubleClickTime();
        g_lastClickTime = currentTime;
        g_selectedShape = PickShape(x, y);
        for (auto shape : g_shapes) shape->selected = (shape == g_selectedShape);
        if (g_selectedShape) {
            if (isDoubleClick) {
                g_statusText = L"\u6b63\u5728\u7f16\u8f91\u5b9e\u4f53\u5c5e\u6027...";
                DLGTEMPLATE* pTemplate = CreateShapePropertiesDialogTemplate();
                DialogBoxIndirectW(GetModuleHandle(nullptr), pTemplate, hWnd, ShapePropertiesDlgProc);
                g_statusText = L"\u5df2\u9009\u4e2d\u5b9e\u4f53 - \u53cc\u51fb\u7f16\u8f91 | \u62d6\u52a8\u79fb\u52a8 | Delete\u5220\u9664";
            } else {
                g_isDragging = true;
                g_lastMousePos.x = x;
                g_lastMousePos.y = y;
                SetCapture(hWnd);
                g_statusText = L"\u5df2\u9009\u4e2d\u5b9e\u4f53 - \u53cc\u51fb\u7f16\u8f91 | \u62d6\u52a8\u79fb\u52a8 | Delete\u5220\u9664";
                float ndcX = (2.0f * x / WINDOW_WIDTH) - 1.0f;
                float ndcY = 1.0f - (2.0f * y / WINDOW_HEIGHT);
                XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4, (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT, 0.01f, 100.0f);
                XMMATRIX invProj = XMMatrixInverse(nullptr, projection);
                XMVECTOR Eye; XMMATRIX view;
                GetCameraViewMatrix(view, Eye);
                XMMATRIX invView = XMMatrixInverse(nullptr, view);
                XMVECTOR rayDir = XMVectorSet(ndcX, ndcY, 1.0f, 0.0f);
                rayDir = XMVector3TransformCoord(rayDir, invProj);
                rayDir = XMVector3TransformNormal(rayDir, invView);
                rayDir = XMVector3Normalize(rayDir);
                float shapeZ = g_selectedShape->position.z;
                float eyeZ = XMVectorGetZ(Eye);
                float rayDirZ = XMVectorGetZ(rayDir);
                if (fabsf(rayDirZ) > 0.0001f) {
                    float t = (shapeZ - eyeZ) / rayDirZ;
                    XMVECTOR intersectPoint = XMVectorAdd(Eye, XMVectorScale(rayDir, t));
                    g_dragOffset.x = g_selectedShape->position.x - XMVectorGetX(intersectPoint);
                    g_dragOffset.y = g_selectedShape->position.y - XMVectorGetY(intersectPoint);
                    g_dragOffset.z = 0.0f;
                }
            }
        } else {
            g_statusText = L"\u5de6\u952e:\u9009\u62e9/\u79fb\u52a8 | \u53f3\u952e/\u4e2d\u952e:\u65cb\u8f6c | \u6eda\u8f6e:Z\u8f74";
        }
        break;
    }
    case WM_LBUTTONUP:
        g_isDragging = false;
        g_isDraggingOrigin = false;
        ReleaseCapture();
        if (g_selectedShape) {
            g_statusText = L"\u5df2\u9009\u4e2d\u5b9e\u4f53 - \u53cc\u51fb\u7f16\u8f91 | \u62d6\u52a8\u79fb\u52a8 | Delete\u5220\u9664";
        }
        break;
    case WM_MOUSEMOVE:
    {
        int x = LOWORD(lParam);
        int y = HIWORD(lParam);
        if ((wParam & MK_MBUTTON) || ((wParam & MK_RBUTTON) && g_cameraMode)) {
            g_statusText = L"\u6b63\u5728\u65cb\u8f6c\u89c6\u89d2...";
            int dx = x - g_lastMousePos.x;
            int dy = y - g_lastMousePos.y;
            g_cameraYaw += dx * 0.005f;
            g_cameraPitch += dy * 0.005f;
            if (g_cameraPitch > XM_PIDIV2 - 0.1f) g_cameraPitch = XM_PIDIV2 - 0.1f;
            if (g_cameraPitch < -XM_PIDIV2 + 0.1f) g_cameraPitch = -XM_PIDIV2 + 0.1f;
            g_lastMousePos.x = x;
            g_lastMousePos.y = y;
        } else if (g_isDragging && g_selectedShape && !g_cameraMode) {
            g_statusText = L"\u6b63\u5728\u79fb\u52a8\u5b9e\u4f53...";
            float ndcX = (2.0f * x / WINDOW_WIDTH) - 1.0f;
            float ndcY = 1.0f - (2.0f * y / WINDOW_HEIGHT);
            XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4, (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT, 0.01f, 100.0f);
            XMMATRIX invProj = XMMatrixInverse(nullptr, projection);
            XMVECTOR Eye; XMMATRIX view;
            GetCameraViewMatrix(view, Eye);
            XMMATRIX invView = XMMatrixInverse(nullptr, view);
            XMVECTOR rayDir = XMVectorSet(ndcX, ndcY, 1.0f, 0.0f);
            rayDir = XMVector3TransformCoord(rayDir, invProj);
            rayDir = XMVector3TransformNormal(rayDir, invView);
            rayDir = XMVector3Normalize(rayDir);
            float shapeZ = g_selectedShape->position.z;
            float eyeZ = XMVectorGetZ(Eye);
            float rayDirZ = XMVectorGetZ(rayDir);
            if (fabsf(rayDirZ) > 0.0001f) {
                float t = (shapeZ - eyeZ) / rayDirZ;
                XMVECTOR intersectPoint = XMVectorAdd(Eye, XMVectorScale(rayDir, t));
                g_selectedShape->position.x = XMVectorGetX(intersectPoint) + g_dragOffset.x;
                g_selectedShape->position.y = XMVectorGetY(intersectPoint) + g_dragOffset.y;
            }
            g_lastMousePos.x = x;
            g_lastMousePos.y = y;
        }
        break;
    }
    case WM_MOUSEWHEEL:
    {
        int delta = GET_WHEEL_DELTA_WPARAM(wParam);
        if (g_selectedShape) {
            g_selectedShape->position.z += delta * 0.01f;
            g_statusText = L"\u8c03\u6574\u5b9e\u4f53Z\u8f74\u4f4d\u7f6e...";
        } else {
            g_cameraDistance -= delta * 0.005f;
            if (g_cameraDistance < 2.0f) g_cameraDistance = 2.0f;
            if (g_cameraDistance > 50.0f) g_cameraDistance = 50.0f;
            g_statusText = L"\u8c03\u6574\u6444\u50cf\u673a\u8ddd\u79bb...";
        }
        break;
    }
    case WM_RBUTTONDOWN:
        g_lastMousePos.x = LOWORD(lParam);
        g_lastMousePos.y = HIWORD(lParam);
        SetCapture(hWnd);
        break;
    case WM_RBUTTONUP:
        ReleaseCapture();
        break;
    case WM_MBUTTONDOWN:
        g_middleButtonDragging = true;
        g_lastMousePos.x = LOWORD(lParam);
        g_lastMousePos.y = HIWORD(lParam);
        SetCapture(hWnd);
        break;
    case WM_MBUTTONUP:
        g_middleButtonDragging = false;
        ReleaseCapture();
        break;
    case WM_KEYDOWN:
        if (wParam == VK_DELETE) {
            if (g_selectedShape) {
                auto it = std::find(g_shapes.begin(), g_shapes.end(), g_selectedShape);
                if (it != g_shapes.end()) g_shapes.erase(it);
                delete g_selectedShape;
                g_selectedShape = nullptr;
                g_statusText = L"\u5df2\u5220\u9664\u56fe\u5f62";
            }
        }
        break;
    case WM_DESTROY:
        PostQuitMessage(0);
        break;
    default:
        return DefWindowProcW(hWnd, message, wParam, lParam);
    }
    return 0;
}

void GetCameraViewMatrix(XMMATRIX& outView, XMVECTOR& outEye)
{
    outEye = XMVectorSet(
        g_cameraDistance * cosf(g_cameraPitch) * cosf(g_cameraYaw),
        g_cameraDistance * cosf(g_cameraPitch) * sinf(g_cameraYaw),
        g_cameraDistance * sinf(g_cameraPitch), 0.0f);
    XMVECTOR At = XMVectorSet(0.0f, 0.0f, 0.0f, 0.0f);
    XMVECTOR Up = XMVectorSet(0.0f, 0.0f, 1.0f, 0.0f);
    outView = XMMatrixLookAtLH(outEye, At, Up);
}


bool CreateAxisBuffers(std::vector<Vertex>& vertices, std::vector<UINT>& indices,
    ID3D11Buffer** ppVertexBuffer, ID3D11Buffer** ppIndexBuffer, UINT* pIndexCount)
{
    D3D11_BUFFER_DESC bd = {};
    bd.Usage = D3D11_USAGE_DEFAULT;
    bd.ByteWidth = sizeof(Vertex) * (UINT)vertices.size();
    bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;
    D3D11_SUBRESOURCE_DATA initData = {};
    initData.pSysMem = vertices.data();
    HRESULT hr = g_pd3dDevice->CreateBuffer(&bd, &initData, ppVertexBuffer);
    if (FAILED(hr)) return false;
    bd.ByteWidth = sizeof(UINT) * (UINT)indices.size();
    bd.BindFlags = D3D11_BIND_INDEX_BUFFER;
    initData.pSysMem = indices.data();
    hr = g_pd3dDevice->CreateBuffer(&bd, &initData, ppIndexBuffer);
    if (FAILED(hr)) return false;
    *pIndexCount = (UINT)indices.size();
    return true;
}

bool InitD3D()
{
    HRESULT hr;
    DXGI_SWAP_CHAIN_DESC sd = {};
    sd.BufferCount = 1;
    sd.BufferDesc.Width = WINDOW_WIDTH;
    sd.BufferDesc.Height = WINDOW_HEIGHT;
    sd.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    sd.BufferDesc.RefreshRate.Numerator = 60;
    sd.BufferDesc.RefreshRate.Denominator = 1;
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    sd.OutputWindow = g_hWnd;
    sd.SampleDesc.Count = 1;
    sd.SampleDesc.Quality = 0;
    sd.Windowed = TRUE;

    D3D_FEATURE_LEVEL featureLevel;
    hr = D3D11CreateDeviceAndSwapChain(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr,
        0, nullptr, 0, D3D11_SDK_VERSION, &sd, &g_pSwapChain, &g_pd3dDevice, &featureLevel, &g_pImmediateContext);
    if (FAILED(hr)) return false;

    ID3D11Texture2D* pBackBuffer = nullptr;
    hr = g_pSwapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), (void**)&pBackBuffer);
    if (FAILED(hr)) return false;
    hr = g_pd3dDevice->CreateRenderTargetView(pBackBuffer, nullptr, &g_pRenderTargetView);
    pBackBuffer->Release();
    if (FAILED(hr)) return false;

    D3D11_TEXTURE2D_DESC depthDesc = {};
    depthDesc.Width = WINDOW_WIDTH;
    depthDesc.Height = WINDOW_HEIGHT;
    depthDesc.MipLevels = 1;
    depthDesc.ArraySize = 1;
    depthDesc.Format = DXGI_FORMAT_D24_UNORM_S8_UINT;
    depthDesc.SampleDesc.Count = 1;
    depthDesc.Usage = D3D11_USAGE_DEFAULT;
    depthDesc.BindFlags = D3D11_BIND_DEPTH_STENCIL;

    ID3D11Texture2D* pDepthStencil = nullptr;
    hr = g_pd3dDevice->CreateTexture2D(&depthDesc, nullptr, &pDepthStencil);
    if (FAILED(hr)) return false;
    hr = g_pd3dDevice->CreateDepthStencilView(pDepthStencil, nullptr, &g_pDepthStencilView);
    pDepthStencil->Release();
    if (FAILED(hr)) return false;

    g_pImmediateContext->OMSetRenderTargets(1, &g_pRenderTargetView, g_pDepthStencilView);

    D3D11_VIEWPORT vp = { 0, 0, (float)WINDOW_WIDTH, (float)WINDOW_HEIGHT, 0.0f, 1.0f };
    g_pImmediateContext->RSSetViewports(1, &vp);

    ID3DBlob* pVSBlob = nullptr;
    ID3DBlob* pErrorBlob = nullptr;
    hr = D3DCompile(g_vertexShaderCode, strlen(g_vertexShaderCode), nullptr, nullptr, nullptr, "main", "vs_5_0", 0, 0, &pVSBlob, &pErrorBlob);
    if (FAILED(hr)) { if (pErrorBlob) pErrorBlob->Release(); return false; }
    hr = g_pd3dDevice->CreateVertexShader(pVSBlob->GetBufferPointer(), pVSBlob->GetBufferSize(), nullptr, &g_pVertexShader);
    if (FAILED(hr)) { pVSBlob->Release(); return false; }

    D3D11_INPUT_ELEMENT_DESC layout[] = {
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0},
        {"NORMAL", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 12, D3D11_INPUT_PER_VERTEX_DATA, 0},
        {"COLOR", 0, DXGI_FORMAT_R32G32B32A32_FLOAT, 0, 24, D3D11_INPUT_PER_VERTEX_DATA, 0},
        {"TEXCOORD", 0, DXGI_FORMAT_R32G32_FLOAT, 0, 40, D3D11_INPUT_PER_VERTEX_DATA, 0},
    };
    hr = g_pd3dDevice->CreateInputLayout(layout, ARRAYSIZE(layout), pVSBlob->GetBufferPointer(), pVSBlob->GetBufferSize(), &g_pVertexLayout);
    pVSBlob->Release();
    if (FAILED(hr)) return false;

    ID3DBlob* pPSBlob = nullptr;
    hr = D3DCompile(g_pixelShaderCode, strlen(g_pixelShaderCode), nullptr, nullptr, nullptr, "main", "ps_5_0", 0, 0, &pPSBlob, &pErrorBlob);
    if (FAILED(hr)) { if (pErrorBlob) pErrorBlob->Release(); return false; }
    hr = g_pd3dDevice->CreatePixelShader(pPSBlob->GetBufferPointer(), pPSBlob->GetBufferSize(), nullptr, &g_pPixelShader);
    pPSBlob->Release();
    if (FAILED(hr)) return false;

    D3D11_BUFFER_DESC bd = {};
    bd.Usage = D3D11_USAGE_DEFAULT;
    bd.ByteWidth = sizeof(ConstantBuffer);
    bd.BindFlags = D3D11_BIND_CONSTANT_BUFFER;
    hr = g_pd3dDevice->CreateBuffer(&bd, nullptr, &g_pConstantBuffer);
    if (FAILED(hr)) return false;

    D3D11_RASTERIZER_DESC rasterDesc = {};
    rasterDesc.FillMode = D3D11_FILL_SOLID;
    rasterDesc.CullMode = D3D11_CULL_BACK;
    rasterDesc.FrontCounterClockwise = FALSE;
    rasterDesc.DepthClipEnable = TRUE;
    hr = g_pd3dDevice->CreateRasterizerState(&rasterDesc, &g_pRasterizerState);
    if (FAILED(hr)) return false;

    D3D11_DEPTH_STENCIL_DESC dsDesc = {};
    dsDesc.DepthEnable = TRUE;
    dsDesc.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL;
    dsDesc.DepthFunc = D3D11_COMPARISON_LESS;
    hr = g_pd3dDevice->CreateDepthStencilState(&dsDesc, &g_pDepthStencilState);
    if (FAILED(hr)) return false;

    D3D11_RASTERIZER_DESC wireframeDesc = {};
    wireframeDesc.FillMode = D3D11_FILL_WIREFRAME;
    wireframeDesc.CullMode = D3D11_CULL_NONE;
    wireframeDesc.DepthClipEnable = TRUE;
    wireframeDesc.DepthBias = -100;
    wireframeDesc.SlopeScaledDepthBias = -1.0f;
    wireframeDesc.AntialiasedLineEnable = TRUE;
    hr = g_pd3dDevice->CreateRasterizerState(&wireframeDesc, &g_pWireframeState);
    if (FAILED(hr)) return false;

    D3D11_BLEND_DESC blendDesc = {};
    blendDesc.RenderTarget[0].BlendEnable = TRUE;
    blendDesc.RenderTarget[0].SrcBlend = D3D11_BLEND_SRC_ALPHA;
    blendDesc.RenderTarget[0].DestBlend = D3D11_BLEND_INV_SRC_ALPHA;
    blendDesc.RenderTarget[0].BlendOp = D3D11_BLEND_OP_ADD;
    blendDesc.RenderTarget[0].SrcBlendAlpha = D3D11_BLEND_ONE;
    blendDesc.RenderTarget[0].DestBlendAlpha = D3D11_BLEND_ZERO;
    blendDesc.RenderTarget[0].BlendOpAlpha = D3D11_BLEND_OP_ADD;
    blendDesc.RenderTarget[0].RenderTargetWriteMask = D3D11_COLOR_WRITE_ENABLE_ALL;
    hr = g_pd3dDevice->CreateBlendState(&blendDesc, &g_pBlendState);
    if (FAILED(hr)) return false;

    D3D11_SAMPLER_DESC sampDesc = {};
    sampDesc.Filter = D3D11_FILTER_MIN_MAG_MIP_LINEAR;
    sampDesc.AddressU = sampDesc.AddressV = sampDesc.AddressW = D3D11_TEXTURE_ADDRESS_WRAP;
    sampDesc.ComparisonFunc = D3D11_COMPARISON_NEVER;
    sampDesc.MaxLOD = D3D11_FLOAT32_MAX;
    hr = g_pd3dDevice->CreateSamplerState(&sampDesc, &g_pSamplerState);
    if (FAILED(hr)) return false;

    // Create axes (cylinder + cone arrows)
    float axisRadius = 0.02f;
    float arrowRadius = 0.08f;
    float arrowHeight = 0.3f;
    int axisSlices = 16;

    std::vector<Vertex> vertices;
    std::vector<UINT> indices;

    XMFLOAT4 redColor(1.0f, 0.0f, 0.0f, 1.0f);
    CreateAxisCylinder(axisRadius, AXIS_LENGTH, axisSlices, redColor, vertices, indices);
    if (!CreateAxisBuffers(vertices, indices, &g_pAxisXVertexBuffer, &g_pAxisXIndexBuffer, &g_axisXIndexCount)) return false;
    CreateAxisCone(arrowRadius, arrowHeight, axisSlices, redColor, vertices, indices);
    if (!CreateAxisBuffers(vertices, indices, &g_pArrowXVertexBuffer, &g_pArrowXIndexBuffer, &g_arrowXIndexCount)) return false;

    XMFLOAT4 greenColor(0.0f, 1.0f, 0.0f, 1.0f);
    CreateAxisCylinder(axisRadius, AXIS_LENGTH, axisSlices, greenColor, vertices, indices);
    if (!CreateAxisBuffers(vertices, indices, &g_pAxisYVertexBuffer, &g_pAxisYIndexBuffer, &g_axisYIndexCount)) return false;
    CreateAxisCone(arrowRadius, arrowHeight, axisSlices, greenColor, vertices, indices);
    if (!CreateAxisBuffers(vertices, indices, &g_pArrowYVertexBuffer, &g_pArrowYIndexBuffer, &g_arrowYIndexCount)) return false;

    XMFLOAT4 blueColor(0.0f, 0.0f, 1.0f, 1.0f);
    CreateAxisCylinder(axisRadius, AXIS_LENGTH, axisSlices, blueColor, vertices, indices);
    if (!CreateAxisBuffers(vertices, indices, &g_pAxisZVertexBuffer, &g_pAxisZIndexBuffer, &g_axisZIndexCount)) return false;
    CreateAxisCone(arrowRadius, arrowHeight, axisSlices, blueColor, vertices, indices);
    if (!CreateAxisBuffers(vertices, indices, &g_pArrowZVertexBuffer, &g_pArrowZIndexBuffer, &g_arrowZIndexCount)) return false;

    return true;
}

void CleanupD3D()
{
    g_selectedShape = nullptr;
    for (auto shape : g_shapes) delete shape;
    g_shapes.clear();

    SAFE_RELEASE(g_pAxisXVertexBuffer); SAFE_RELEASE(g_pAxisXIndexBuffer);
    SAFE_RELEASE(g_pAxisYVertexBuffer); SAFE_RELEASE(g_pAxisYIndexBuffer);
    SAFE_RELEASE(g_pAxisZVertexBuffer); SAFE_RELEASE(g_pAxisZIndexBuffer);
    SAFE_RELEASE(g_pArrowXVertexBuffer); SAFE_RELEASE(g_pArrowXIndexBuffer);
    SAFE_RELEASE(g_pArrowYVertexBuffer); SAFE_RELEASE(g_pArrowYIndexBuffer);
    SAFE_RELEASE(g_pArrowZVertexBuffer); SAFE_RELEASE(g_pArrowZIndexBuffer);
    SAFE_RELEASE(g_pSamplerState); SAFE_RELEASE(g_pBlendState);
    SAFE_RELEASE(g_pDepthStencilState); SAFE_RELEASE(g_pWireframeState);
    SAFE_RELEASE(g_pRasterizerState); SAFE_RELEASE(g_pConstantBuffer);
    SAFE_RELEASE(g_pVertexLayout); SAFE_RELEASE(g_pVertexShader);
    SAFE_RELEASE(g_pPixelShader); SAFE_RELEASE(g_pDepthStencilView);
    SAFE_RELEASE(g_pRenderTargetView); SAFE_RELEASE(g_pSwapChain);
    SAFE_RELEASE(g_pImmediateContext); SAFE_RELEASE(g_pd3dDevice);
}


void RenderAxis(ID3D11Buffer* pVertexBuffer, ID3D11Buffer* pIndexBuffer, UINT indexCount,
    ID3D11Buffer* pArrowVertexBuffer, ID3D11Buffer* pArrowIndexBuffer, UINT arrowIndexCount,
    const XMMATRIX& axisWorld, const XMMATRIX& arrowWorld,
    const XMMATRIX& view, const XMMATRIX& projection, const XMFLOAT3& cameraPos, const XMFLOAT4& axisColor)
{
    ConstantBuffer cb;
    cb.view = XMMatrixTranspose(view);
    cb.projection = XMMatrixTranspose(projection);
    cb.lightDir = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
    cb.lightColor = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
    cb.cameraPos = XMFLOAT4(cameraPos.x, cameraPos.y, cameraPos.z, 1.0f);
    cb.matAmbient = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
    cb.matDiffuse = XMFLOAT4(axisColor.x, axisColor.y, axisColor.z, 1.0f);
    cb.matSpecular = XMFLOAT4(0.0f, 0.0f, 0.0f, 1.0f);
    cb.matEmissive = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
    cb.textureInfo = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
    cb.materialExtra = XMFLOAT4(1.0f, 0.0f, 0.0f, 0.0f);

    UINT stride = sizeof(Vertex);
    UINT offset = 0;

    cb.world = XMMatrixTranspose(axisWorld);
    g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cb, 0, 0);
    g_pImmediateContext->IASetVertexBuffers(0, 1, &pVertexBuffer, &stride, &offset);
    g_pImmediateContext->IASetIndexBuffer(pIndexBuffer, DXGI_FORMAT_R32_UINT, 0);
    g_pImmediateContext->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    g_pImmediateContext->DrawIndexed(indexCount, 0, 0);

    cb.world = XMMatrixTranspose(arrowWorld);
    g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cb, 0, 0);
    g_pImmediateContext->IASetVertexBuffers(0, 1, &pArrowVertexBuffer, &stride, &offset);
    g_pImmediateContext->IASetIndexBuffer(pArrowIndexBuffer, DXGI_FORMAT_R32_UINT, 0);
    g_pImmediateContext->DrawIndexed(arrowIndexCount, 0, 0);
}

void Render()
{
    if (!g_pImmediateContext || !g_pRenderTargetView || !g_pDepthStencilView) return;

    float clearColor[4] = { 0.75f, 0.75f, 0.78f, 1.0f };
    g_pImmediateContext->ClearRenderTargetView(g_pRenderTargetView, clearColor);
    g_pImmediateContext->ClearDepthStencilView(g_pDepthStencilView, D3D11_CLEAR_DEPTH, 1.0f, 0);

    XMVECTOR Eye; XMMATRIX view;
    GetCameraViewMatrix(view, Eye);
    XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4, (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT, 0.01f, 100000.0f);

    g_pImmediateContext->IASetInputLayout(g_pVertexLayout);
    g_pImmediateContext->VSSetShader(g_pVertexShader, nullptr, 0);
    g_pImmediateContext->PSSetShader(g_pPixelShader, nullptr, 0);
    g_pImmediateContext->RSSetState(g_pRasterizerState);
    g_pImmediateContext->OMSetDepthStencilState(g_pDepthStencilState, 1);

    float blendFactor[4] = { 0.0f, 0.0f, 0.0f, 0.0f };
    g_pImmediateContext->OMSetBlendState(g_pBlendState, blendFactor, 0xffffffff);

    XMFLOAT3 cameraPos;
    XMStoreFloat3(&cameraPos, Eye);

    for (auto shape : g_shapes) {
        if (!shape->vertexBuffer || !shape->indexBuffer) continue;

        ConstantBuffer cb;
        cb.world = XMMatrixTranspose(shape->GetWorldMatrix());
        cb.view = XMMatrixTranspose(view);
        cb.projection = XMMatrixTranspose(projection);
        cb.lightDir = XMFLOAT4(g_lightDirection.x, g_lightDirection.y, g_lightDirection.z, 0.0f);
        cb.lightColor = XMFLOAT4(g_lightColor.x, g_lightColor.y, g_lightColor.z, 1.0f);
        cb.cameraPos = XMFLOAT4(cameraPos.x, cameraPos.y, cameraPos.z, 1.0f);
        cb.matAmbient = XMFLOAT4(shape->material.ambient.x, shape->material.ambient.y, shape->material.ambient.z, 1.0f);
        cb.matDiffuse = XMFLOAT4(shape->material.diffuse.x, shape->material.diffuse.y, shape->material.diffuse.z, 1.0f);
        cb.matSpecular = XMFLOAT4(shape->material.specular.x, shape->material.specular.y, shape->material.specular.z, shape->material.shininess);
        cb.matEmissive = XMFLOAT4(shape->material.emissive.x, shape->material.emissive.y, shape->material.emissive.z, 1.0f);
        cb.textureInfo = XMFLOAT4((float)shape->textureMode, 0.0f, 0.0f, 0.0f);
        cb.materialExtra = XMFLOAT4(shape->material.transparency, shape->material.reflectivity, 0.0f, 0.0f);
        g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cb, 0, 0);

        UINT stride = sizeof(Vertex);
        UINT offset = 0;
        g_pImmediateContext->IASetVertexBuffers(0, 1, &shape->vertexBuffer, &stride, &offset);
        g_pImmediateContext->IASetIndexBuffer(shape->indexBuffer, DXGI_FORMAT_R32_UINT, 0);
        g_pImmediateContext->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
        g_pImmediateContext->VSSetConstantBuffers(0, 1, &g_pConstantBuffer);
        g_pImmediateContext->PSSetConstantBuffers(0, 1, &g_pConstantBuffer);

        if (shape->textureView && shape->textureMode > 0) {
            g_pImmediateContext->PSSetShaderResources(0, 1, &shape->textureView);
            g_pImmediateContext->PSSetSamplers(0, 1, &g_pSamplerState);
        } else {
            ID3D11ShaderResourceView* nullSRV = nullptr;
            g_pImmediateContext->PSSetShaderResources(0, 1, &nullSRV);
        }

        g_pImmediateContext->DrawIndexed(shape->indexCount, 0, 0);

        // 只有四面体在未选中时显示线框，平面和立方体不显示
        if (shape->type == SHAPE_TETRAHEDRON) {
            g_pImmediateContext->RSSetState(g_pWireframeState);
            ConstantBuffer cbWire = cb;
            cbWire.lightDir = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
            cbWire.lightColor = XMFLOAT4(0.6f, 0.6f, 0.6f, 0.3f);
            cbWire.matSpecular = XMFLOAT4(0.0f, 0.0f, 0.0f, 1.0f);
            cbWire.textureInfo = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
            g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cbWire, 0, 0);
            g_pImmediateContext->DrawIndexed(shape->indexCount, 0, 0);
        }

        g_pImmediateContext->RSSetState(g_pRasterizerState);
        g_pImmediateContext->OMSetBlendState(g_pBlendState, blendFactor, 0xffffffff);

        if (shape->selected && g_pWireframeState) {
            g_pImmediateContext->OMSetBlendState(nullptr, blendFactor, 0xffffffff);
            g_pImmediateContext->RSSetState(g_pWireframeState);
            ConstantBuffer cbSel = cb;
            cbSel.lightDir = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
            cbSel.lightColor = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
            cbSel.matSpecular = XMFLOAT4(0.0f, 0.0f, 0.0f, 1.0f);
            cbSel.textureInfo = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
            g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cbSel, 0, 0);
            g_pImmediateContext->DrawIndexed(shape->indexCount, 0, 0);
            g_pImmediateContext->RSSetState(g_pRasterizerState);
            g_pImmediateContext->OMSetBlendState(g_pBlendState, blendFactor, 0xffffffff);
        }
    }

    if (g_showAxes) {
        ID3D11ShaderResourceView* nullSRV = nullptr;
        g_pImmediateContext->PSSetShaderResources(0, 1, &nullSRV);
        g_pImmediateContext->VSSetConstantBuffers(0, 1, &g_pConstantBuffer);
        g_pImmediateContext->PSSetConstantBuffers(0, 1, &g_pConstantBuffer);

        XMMATRIX originTrans = XMMatrixTranslation(g_axesOrigin.x, g_axesOrigin.y, g_axesOrigin.z);

        // X axis (red) - rotate -90 around Z to point along X
        XMMATRIX rotX = XMMatrixRotationZ(-XM_PIDIV2);
        XMMATRIX axisXWorld = rotX * originTrans;
        XMMATRIX arrowXWorld = XMMatrixTranslation(0, AXIS_LENGTH, 0) * rotX * originTrans;
        RenderAxis(g_pAxisXVertexBuffer, g_pAxisXIndexBuffer, g_axisXIndexCount,
            g_pArrowXVertexBuffer, g_pArrowXIndexBuffer, g_arrowXIndexCount,
            axisXWorld, arrowXWorld, view, projection, cameraPos, XMFLOAT4(1.0f, 0.0f, 0.0f, 1.0f));

        // Y axis (green) - rotate 90 around X
        XMMATRIX rotY = XMMatrixRotationX(XM_PIDIV2);
        XMMATRIX axisYWorld = rotY * originTrans;
        XMMATRIX arrowYWorld = XMMatrixTranslation(0, AXIS_LENGTH, 0) * rotY * originTrans;
        RenderAxis(g_pAxisYVertexBuffer, g_pAxisYIndexBuffer, g_axisYIndexCount,
            g_pArrowYVertexBuffer, g_pArrowYIndexBuffer, g_arrowYIndexCount,
            axisYWorld, arrowYWorld, view, projection, cameraPos, XMFLOAT4(0.0f, 1.0f, 0.0f, 1.0f));

        // Z axis (blue) - no rotation needed (Y is up in local, Z is up in world)
        XMMATRIX axisZWorld = originTrans;
        XMMATRIX arrowZWorld = XMMatrixTranslation(0, AXIS_LENGTH, 0) * originTrans;
        RenderAxis(g_pAxisZVertexBuffer, g_pAxisZIndexBuffer, g_axisZIndexCount,
            g_pArrowZVertexBuffer, g_pArrowZIndexBuffer, g_arrowZIndexCount,
            axisZWorld, arrowZWorld, view, projection, cameraPos, XMFLOAT4(0.0f, 0.0f, 1.0f, 1.0f));
    }

    g_pSwapChain->Present(0, 0);
    
    // 状态文字显示在窗口标题栏
    std::wstring title = L"3D\u56fe\u5f62\u7f16\u8f91\u5668 - " + g_statusText;
    SetWindowTextW(g_hWnd, title.c_str());
}
