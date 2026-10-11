#define UNICODE
#define _UNICODE
#include <windows.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <d3dcompiler.h>
#include <DirectXMath.h>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm> // for std::find
#include <new>       // for std::nothrow

#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "d3dcompiler.lib")
#pragma comment(lib, "dxgi.lib")
#pragma comment(lib, "comdlg32.lib")

using namespace DirectX;

// 常量定义
const int WINDOW_WIDTH = 1024;
const int WINDOW_HEIGHT = 768;
const float CAMERA_DISTANCE = 10.0f;

// 顶点结构
struct Vertex
{
    XMFLOAT3 position;
    XMFLOAT3 normal;
    XMFLOAT4 color;
    XMFLOAT2 texCoord; // 纹理坐标
};

// 常量缓冲区结构
struct ConstantBuffer
{
    XMMATRIX world;
    XMMATRIX view;
    XMMATRIX projection;
    XMFLOAT4 lightDir;
    XMFLOAT4 lightColor;
    XMFLOAT4 cameraPos;   // 摄像机位置（用于镜面反射计算）
    XMFLOAT4 matAmbient;  // 材质环境光
    XMFLOAT4 matDiffuse;  // 材质漫反射
    XMFLOAT4 matSpecular; // 材质镜面反射 (w = shininess)
    XMFLOAT4 textureInfo; // x: textureMode (0=无, 1=混合, 2=替换), y,z,w: 保留
};

// 实体类型枚举
enum ShapeType
{
    SHAPE_SPHERE,
    SHAPE_CYLINDER,
    SHAPE_CONE,
    SHAPE_PLANE,
    SHAPE_CUBE,
    SHAPE_TETRAHEDRON
};

// 材质结构
struct Material
{
    XMFLOAT3 ambient;  // 环境光反射率
    XMFLOAT3 diffuse;  // 漫反射率
    XMFLOAT3 specular; // 镜面反射率
    float shininess;   // 光泽度

    Material() : ambient(0.3f, 0.3f, 0.3f), diffuse(1.0f, 1.0f, 1.0f),
        specular(1.0f, 1.0f, 1.0f), shininess(32.0f) {
    }
};

// 3D实体类
class Shape3D
{
public:
    ShapeType type;
    XMFLOAT3 position;
    XMFLOAT3 rotation;
    XMFLOAT3 scale;
    XMFLOAT4 color;
    ID3D11Buffer* vertexBuffer;
    ID3D11Buffer* indexBuffer;
    UINT indexCount;
    bool selected;

    // 材质属性
    Material material;
    std::wstring texturePath;
    ID3D11ShaderResourceView* textureView;
    int textureMode; // 0: 无纹理, 1: 颜色混合, 2: 纹理替换

    Shape3D() : vertexBuffer(nullptr), indexBuffer(nullptr),
        indexCount(0), selected(false), textureView(nullptr), textureMode(0)
    {
        position = XMFLOAT3(0, 0, 0);
        rotation = XMFLOAT3(0, 0, 0);
        scale = XMFLOAT3(1, 1, 1);
        color = XMFLOAT4(0.5f, 0.5f, 0.8f, 1.0f);
        material = Material();
        texturePath = L"";
    }

    ~Shape3D()
    {
        if (vertexBuffer)
            vertexBuffer->Release();
        if (indexBuffer)
            indexBuffer->Release();
        if (textureView)
            textureView->Release();
    }

    XMMATRIX GetWorldMatrix()
    {
        XMMATRIX mScale = XMMatrixScaling(scale.x, scale.y, scale.z);
        XMMATRIX mRotX = XMMatrixRotationX(rotation.x);
        XMMATRIX mRotY = XMMatrixRotationY(rotation.y);
        XMMATRIX mRotZ = XMMatrixRotationZ(rotation.z);
        XMMATRIX mTrans = XMMatrixTranslation(position.x, position.y, position.z);
        return mScale * mRotX * mRotY * mRotZ * mTrans;
    }
};

// 安全释放宏
#define SAFE_RELEASE(p)     \
    {                       \
        if (p)              \
        {                   \
            (p)->Release(); \
            (p) = nullptr;  \
        }                   \
    }

// 全局变量
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
ID3D11RasterizerState* g_pWireframeState = nullptr; // 预创建的线框状态
ID3D11DepthStencilState* g_pDepthStencilState = nullptr;
ID3D11BlendState* g_pBlendState = nullptr;     // 混合状态用于半透明渲染
ID3D11SamplerState* g_pSamplerState = nullptr; // 纹理采样器状态

std::vector<Shape3D*> g_shapes;
Shape3D* g_selectedShape = nullptr;
POINT g_lastMousePos = { 0, 0 };
bool g_isDragging = false;
bool g_cameraMode = false;
bool g_middleButtonDragging = false; // 中键拖动摄像头
DWORD g_lastClickTime = 0;

// 状态提示文本
std::wstring g_statusText = L"操作提示: 左键选择/移动 | 右键/中键旋转视角 | 滚轮Z轴移动";

// 拖拽偏移记录 - 用于精确移动
XMFLOAT3 g_dragOffset = { 0.0f, 0.0f, 0.0f };

float g_cameraYaw = -0.6f;  // 初始偏航角，从右前方看向原点
float g_cameraPitch = 0.4f; // 初始仰角，俯视
float g_cameraDistance = CAMERA_DISTANCE;

// 坐标轴显示
bool g_showAxes = true;
ID3D11Buffer* g_pAxesVertexBuffer = nullptr;
UINT g_axesVertexCount = 0;

// 坐标轴原点偏移（可拖动）
XMFLOAT3 g_axesOrigin = { 0.0f, 0.0f, 0.0f };
bool g_isDraggingOrigin = false;

// 光照参数
XMFLOAT3 g_lightDirection = XMFLOAT3(0.577f, -0.577f, 0.577f);
XMFLOAT3 g_lightColor = XMFLOAT3(1.0f, 1.0f, 1.0f);

// 菜单ID
#define IDM_SPHERE 1001
#define IDM_CYLINDER 1002
#define IDM_PLANE 1003
#define IDM_CUBE 1004
#define IDM_TETRAHEDRON 1005
#define IDM_CAMERA_MODE 1006
#define IDM_LIGHT_SETTINGS 1007
#define IDM_MATERIAL_SETTINGS 1008
#define IDM_TEXTURE_SETTINGS 1009
#define IDM_SHOW_AXES 1011
#define IDM_DELETE_SHAPE 1012
#define IDM_EXIT 1010

// 对话框ID
#define IDD_SHAPE_PROPERTIES 2001
#define IDC_EDIT_POS_X 2002
#define IDC_EDIT_POS_Y 2003
#define IDC_EDIT_POS_Z 2004
#define IDC_EDIT_ROT_X 2005
#define IDC_EDIT_ROT_Y 2006
#define IDC_EDIT_ROT_Z 2007
#define IDC_EDIT_SCALE_X 2008
#define IDC_EDIT_SCALE_Y 2009
#define IDC_EDIT_SCALE_Z 2010

#define IDD_LIGHT_SETTINGS 3001
#define IDC_EDIT_LIGHT_X 3002
#define IDC_EDIT_LIGHT_Y 3003
#define IDC_EDIT_LIGHT_Z 3004
#define IDC_EDIT_LIGHT_R 3005
#define IDC_EDIT_LIGHT_G 3006
#define IDC_EDIT_LIGHT_B 3007

#define IDD_MATERIAL_SETTINGS 4001
#define IDC_EDIT_AMBIENT_R 4002
#define IDC_EDIT_AMBIENT_G 4003
#define IDC_EDIT_AMBIENT_B 4004
#define IDC_EDIT_DIFFUSE_R 4005
#define IDC_EDIT_DIFFUSE_G 4006
#define IDC_EDIT_DIFFUSE_B 4007
#define IDC_EDIT_SPECULAR_R 4008
#define IDC_EDIT_SPECULAR_G 4009
#define IDC_EDIT_SPECULAR_B 4010
#define IDC_EDIT_SHININESS 4011

#define IDD_TEXTURE_SETTINGS 5001
#define IDC_EDIT_TEXTURE_PATH 5002
#define IDC_COMBO_TEXTURE_MODE 5003
#define IDC_BUTTON_BROWSE 5004

// 前向声明
LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK ShapePropertiesDlgProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK LightSettingsDlgProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK MaterialSettingsDlgProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK TextureSettingsDlgProc(HWND, UINT, WPARAM, LPARAM);
bool InitD3D();
void CleanupD3D();
void Render();
void CreateSphere(float radius, int slices, int stacks, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateCylinder(float radius, float height, int slices, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreatePlane(float width, float height, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateCube(float size, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateTetrahedron(float size, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
Shape3D* CreateShape(ShapeType type);
Shape3D* PickShape(int x, int y);
bool UpdateShapeVertexColor(Shape3D* shape);
bool LoadTextureFromFile(const wchar_t* filename, ID3D11ShaderResourceView** textureView);
DLGTEMPLATE* CreateShapePropertiesDialogTemplate();
DLGTEMPLATE* CreateLightSettingsDialogTemplate();

// 辅助函数：获取视图矩阵和摄像机位置
void GetCameraViewMatrix(XMMATRIX& outView, XMVECTOR& outEye);

// Shader代码
const char* g_vertexShaderCode = R"(
cbuffer ConstantBuffer : register(b0) {
    matrix World;
    matrix View;
    matrix Projection;
    float4 LightDir;
    float4 LightColor;
    float4 CameraPos;
    float4 MatAmbient;
    float4 MatDiffuse;
    float4 MatSpecular;
    float4 TextureInfo;  // x: textureMode
}

struct VS_INPUT {
    float3 Pos : POSITION;
    float3 Normal : NORMAL;
    float4 Color : COLOR;
    float2 TexCoord : TEXCOORD;
};

struct PS_INPUT {
    float4 Pos : SV_POSITION;
    float3 Normal : NORMAL;
    float4 Color : COLOR;
    float3 WorldPos : TEXCOORD0;
    float2 TexCoord : TEXCOORD1;
};

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
    matrix World;
    matrix View;
    matrix Projection;
    float4 LightDir;
    float4 LightColor;
    float4 CameraPos;
    float4 MatAmbient;
    float4 MatDiffuse;
    float4 MatSpecular;  // w = shininess
    float4 TextureInfo;  // x: textureMode (0=无, 1=混合, 2=替换)
}

struct PS_INPUT {
    float4 Pos : SV_POSITION;
    float3 Normal : NORMAL;
    float4 Color : COLOR;
    float3 WorldPos : TEXCOORD0;
    float2 TexCoord : TEXCOORD1;
};

float4 main(PS_INPUT input) : SV_Target {
    float3 normal = normalize(input.Normal);
    float3 lightDir = normalize(-LightDir.xyz);
    
    // 获取基础颜色（根据纹理模式）
    float3 baseColor = input.Color.rgb;
    float alpha = input.Color.a;
    int texMode = (int)TextureInfo.x;
    
    if (texMode > 0) {
        float4 texColor = texDiffuse.Sample(samLinear, input.TexCoord);
        if (texMode == 1) {
            // 颜色混合模式：纹理与材质颜色混合
            baseColor = texColor.rgb * MatDiffuse.rgb;
            alpha = texColor.a * input.Color.a;
        } else if (texMode == 2) {
            // 纹理替换模式：完全使用纹理颜色
            baseColor = texColor.rgb;
            alpha = texColor.a;
        }
    }
    
    // 环境光分量 - 使用材质环境光参数
    float3 ambient = MatAmbient.rgb * LightColor.rgb;
    
    // 漫反射分量 - 使用材质漫反射参数
    float NdotL = max(dot(normal, lightDir), 0.0f);
    float3 diffuse = MatDiffuse.rgb * NdotL * LightColor.rgb;
    
    // 镜面反射分量 - 使用材质镜面反射和光泽度参数
    float3 viewDir = normalize(CameraPos.xyz - input.WorldPos);
    float3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0f), MatSpecular.w);
    float3 specular = MatSpecular.rgb * spec * LightColor.rgb;
    
    // 组合光照结果
    float3 finalColor = (ambient + diffuse + specular) * baseColor;
    
    return float4(saturate(finalColor), alpha);
}
)";

// WinMain入口
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow)
{
    // 注册窗口类
    WNDCLASSEX wc = {};
    wc.cbSize = sizeof(WNDCLASSEX);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.lpszClassName = L"D3DWindowClass";
    wc.lpszMenuName = nullptr;
    RegisterClassEx(&wc);

    // 创建菜单
    HMENU hMenu = CreateMenu();
    HMENU hSubMenu = CreatePopupMenu();
    AppendMenu(hSubMenu, MF_STRING, IDM_SPHERE, L"球体");
    AppendMenu(hSubMenu, MF_STRING, IDM_CYLINDER, L"柱体");
    AppendMenu(hSubMenu, MF_STRING, IDM_PLANE, L"平面");
    AppendMenu(hSubMenu, MF_STRING, IDM_CUBE, L"六面体");
    AppendMenu(hSubMenu, MF_STRING, IDM_TETRAHEDRON, L"四面体");
    AppendMenu(hSubMenu, MF_SEPARATOR, 0, nullptr);
    AppendMenu(hSubMenu, MF_STRING, IDM_EXIT, L"退出");
    AppendMenu(hMenu, MF_POPUP, (UINT_PTR)hSubMenu, L"绘制");

    HMENU hViewMenu = CreatePopupMenu();
    AppendMenu(hViewMenu, MF_STRING, IDM_CAMERA_MODE, L"摄像机控制模式");
    AppendMenu(hViewMenu, MF_STRING | MF_CHECKED, IDM_SHOW_AXES, L"显示坐标轴");
    AppendMenu(hViewMenu, MF_STRING, IDM_LIGHT_SETTINGS, L"光照设置");
    AppendMenu(hMenu, MF_POPUP, (UINT_PTR)hViewMenu, L"视图");

    HMENU hEditMenu = CreatePopupMenu();
    AppendMenu(hEditMenu, MF_STRING, IDM_DELETE_SHAPE, L"删除图元\tDelete");
    AppendMenu(hEditMenu, MF_SEPARATOR, 0, nullptr);
    AppendMenu(hEditMenu, MF_STRING, IDM_MATERIAL_SETTINGS, L"材质设置");
    AppendMenu(hEditMenu, MF_STRING, IDM_TEXTURE_SETTINGS, L"纹理设置");
    AppendMenu(hMenu, MF_POPUP, (UINT_PTR)hEditMenu, L"编辑");

    // 创建窗口
    RECT rc = { 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT };
    AdjustWindowRect(&rc, WS_OVERLAPPEDWINDOW, TRUE);
    g_hWnd = CreateWindow(L"D3DWindowClass", L"3D图形绘制与编辑软件",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
        rc.right - rc.left, rc.bottom - rc.top,
        nullptr, hMenu, hInstance, nullptr);

    if (!g_hWnd)
        return 0;

    ShowWindow(g_hWnd, nCmdShow);
    UpdateWindow(g_hWnd);

    // 初始化D3D
    if (!InitD3D())
    {
        return 0;
    }

    // 消息循环
    MSG msg = {};
    while (msg.message != WM_QUIT)
    {
        if (PeekMessage(&msg, nullptr, 0, 0, PM_REMOVE))
        {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
        else
        {
            Render();
        }
    }

    CleanupD3D();
    return (int)msg.wParam;
}

// 窗口过程
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
    switch (message)
    {
    case WM_COMMAND:
    {
        int wmId = LOWORD(wParam);
        // 精简形状创建逻辑
        if (wmId >= IDM_SPHERE && wmId <= IDM_TETRAHEDRON)
        {
            ShapeType shapeTypes[] = { SHAPE_SPHERE, SHAPE_CYLINDER, SHAPE_PLANE, SHAPE_CUBE, SHAPE_TETRAHEDRON };
            Shape3D* newShape = CreateShape(shapeTypes[wmId - IDM_SPHERE]);
            if (newShape)
                g_shapes.push_back(newShape);
            break;
        }
        switch (wmId)
        {
        case IDM_CAMERA_MODE:
            g_cameraMode = !g_cameraMode;
            CheckMenuItem(GetMenu(hWnd), IDM_CAMERA_MODE,
                g_cameraMode ? MF_CHECKED : MF_UNCHECKED);
            if (g_cameraMode)
            {
                g_statusText = L"摄像机模式: 右键/中键旋转 | 滚轮缩放";
            }
            else
            {
                g_statusText = L"操作提示: 左键选择/移动 | 右键/中键旋转视角 | 滚轮Z轴移动";
            }
            break;
        case IDM_LIGHT_SETTINGS:
        {
            DLGTEMPLATE* pTemplate = CreateLightSettingsDialogTemplate();
            DialogBoxIndirect(GetModuleHandle(nullptr), pTemplate, hWnd, LightSettingsDlgProc);
            break;
        }
        case IDM_MATERIAL_SETTINGS:
            if (g_selectedShape)
            {
                DLGTEMPLATE* pTemplate = CreateShapePropertiesDialogTemplate();
                DialogBoxIndirect(GetModuleHandle(nullptr), pTemplate, hWnd, MaterialSettingsDlgProc);
            }
            else
            {
                g_statusText = L"提示: 请先选择一个实体";
                SetWindowText(g_hWnd, (L"3D图形绘制与编辑软件 - " + g_statusText).c_str());
            }
            break;
        case IDM_TEXTURE_SETTINGS:
            if (g_selectedShape)
            {
                DLGTEMPLATE* pTemplate = CreateShapePropertiesDialogTemplate();
                DialogBoxIndirect(GetModuleHandle(nullptr), pTemplate, hWnd, TextureSettingsDlgProc);
            }
            else
            {
                g_statusText = L"提示: 请先选择一个实体";
                SetWindowText(g_hWnd, (L"3D图形绘制与编辑软件 - " + g_statusText).c_str());
            }
            break;
        case IDM_SHOW_AXES:
            g_showAxes = !g_showAxes;
            CheckMenuItem(GetMenu(hWnd), IDM_SHOW_AXES,
                g_showAxes ? MF_CHECKED : MF_UNCHECKED);
            break;
        case IDM_DELETE_SHAPE:
            if (g_selectedShape)
            {
                // 从列表中移除并删除选中的形状
                auto it = std::find(g_shapes.begin(), g_shapes.end(), g_selectedShape);
                if (it != g_shapes.end())
                {
                    g_shapes.erase(it);
                }
                delete g_selectedShape;
                g_selectedShape = nullptr;
                g_statusText = L"提示: 图元已删除";
            }
            else
            {
                g_statusText = L"提示: 请先选择要删除的图元";
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

        // 检测双击
        DWORD currentTime = GetTickCount();
        bool isDoubleClick = (currentTime - g_lastClickTime) < GetDoubleClickTime();
        g_lastClickTime = currentTime;

        g_selectedShape = PickShape(x, y);

        // 更新所有形状的选中状态
        for (auto shape : g_shapes)
        {
            shape->selected = (shape == g_selectedShape);
        }

        if (g_selectedShape)
        {
            if (isDoubleClick)
            {
                // 双击弹出属性编辑对话框
                DLGTEMPLATE* pTemplate = CreateShapePropertiesDialogTemplate();
                DialogBoxIndirect(GetModuleHandle(nullptr), pTemplate, hWnd, ShapePropertiesDlgProc);
            }
            else
            {
                g_isDragging = true;
                g_lastMousePos.x = x;
                g_lastMousePos.y = y;
                SetCapture(hWnd);

                // 计算并记录点击位置与物体中心的世界空间偏移
                // 将屏幕坐标转换为世界坐标
                float ndcX = (2.0f * x / WINDOW_WIDTH) - 1.0f;
                float ndcY = 1.0f - (2.0f * y / WINDOW_HEIGHT);

                XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4,
                    (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT, 0.01f, 100.0f);
                XMMATRIX invProj = XMMatrixInverse(nullptr, projection);

                XMVECTOR Eye;
                XMMATRIX view;
                GetCameraViewMatrix(view, Eye);
                XMMATRIX invView = XMMatrixInverse(nullptr, view);

                XMVECTOR rayDir = XMVectorSet(ndcX, ndcY, 1.0f, 0.0f);
                rayDir = XMVector3TransformCoord(rayDir, invProj);
                rayDir = XMVector3TransformNormal(rayDir, invView);
                rayDir = XMVector3Normalize(rayDir);

                // 计算射线与XOY平面（z = 物体当前z坐标）的交点
                float shapeZ = g_selectedShape->position.z;
                float eyeZ = XMVectorGetZ(Eye);
                float rayDirZ = XMVectorGetZ(rayDir);

                if (fabsf(rayDirZ) > 0.0001f)
                {
                    float t = (shapeZ - eyeZ) / rayDirZ;
                    XMVECTOR intersectPoint = XMVectorAdd(Eye, XMVectorScale(rayDir, t));

                    // 记录物体位置与点击位置的偏移（只xy）
                    g_dragOffset.x = g_selectedShape->position.x - XMVectorGetX(intersectPoint);
                    g_dragOffset.y = g_selectedShape->position.y - XMVectorGetY(intersectPoint);
                    g_dragOffset.z = 0.0f;
                }
            }
        }
        // 未选中任何图元时，不进行任何操作（禁止默认拖动坐标系）
        break;
    }
    case WM_LBUTTONUP:
        g_isDragging = false;
        g_isDraggingOrigin = false;
        ReleaseCapture();
        break;
    case WM_MOUSEMOVE:
    {
        int x = LOWORD(lParam);
        int y = HIWORD(lParam);

        if ((wParam & MK_MBUTTON) || ((wParam & MK_RBUTTON) && g_cameraMode))
        {
            // 中键始终可以拖动，右键需要开启摄像机模式
            int dx = x - g_lastMousePos.x;
            int dy = y - g_lastMousePos.y;

            g_cameraYaw += dx * 0.005f;
            g_cameraPitch += dy * 0.005f;

            // 限制俯仰角
            if (g_cameraPitch > XM_PIDIV2 - 0.1f)
                g_cameraPitch = XM_PIDIV2 - 0.1f;
            if (g_cameraPitch < -XM_PIDIV2 + 0.1f)
                g_cameraPitch = -XM_PIDIV2 + 0.1f;

            g_lastMousePos.x = x;
            g_lastMousePos.y = y;
        }
        else if (g_isDragging && g_selectedShape && !g_cameraMode)
        {
            // 在XOY平面上移动图元，不改变z轴
            float ndcX = (2.0f * x / WINDOW_WIDTH) - 1.0f;
            float ndcY = 1.0f - (2.0f * y / WINDOW_HEIGHT);

            XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4,
                (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT, 0.01f, 100.0f);
            XMMATRIX invProj = XMMatrixInverse(nullptr, projection);

            XMVECTOR Eye;
            XMMATRIX view;
            GetCameraViewMatrix(view, Eye);
            XMMATRIX invView = XMMatrixInverse(nullptr, view);

            XMVECTOR rayDir = XMVectorSet(ndcX, ndcY, 1.0f, 0.0f);
            rayDir = XMVector3TransformCoord(rayDir, invProj);
            rayDir = XMVector3TransformNormal(rayDir, invView);
            rayDir = XMVector3Normalize(rayDir);

            // 计算射线与XOY平面（z = 物体当前z坐标）的交点
            // 平面方程: z = shapeZ
            // 射线: P = Eye + t * rayDir
            // 求解: Eye.z + t * rayDir.z = shapeZ
            float shapeZ = g_selectedShape->position.z;
            float eyeZ = XMVectorGetZ(Eye);
            float rayDirZ = XMVectorGetZ(rayDir);

            if (fabsf(rayDirZ) > 0.0001f) // 避免除以零
            {
                float t = (shapeZ - eyeZ) / rayDirZ;
                XMVECTOR intersectPoint = XMVectorAdd(Eye, XMVectorScale(rayDir, t));

                // 新位置 = 交点 + 偏移量，保持z不变
                float newX = XMVectorGetX(intersectPoint) + g_dragOffset.x;
                float newY = XMVectorGetY(intersectPoint) + g_dragOffset.y;

                g_selectedShape->position.x = newX;
                g_selectedShape->position.y = newY;
                // z保持不变
            }

            g_lastMousePos.x = x;
            g_lastMousePos.y = y;
        }
        else if (g_isDraggingOrigin && !g_cameraMode)
        {
            // 拖动坐标轴原点
            float ndcX = (2.0f * x / WINDOW_WIDTH) - 1.0f;
            float ndcY = 1.0f - (2.0f * y / WINDOW_HEIGHT);

            XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4,
                (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT, 0.01f, 100.0f);
            XMMATRIX invProj = XMMatrixInverse(nullptr, projection);

            XMVECTOR Eye;
            XMMATRIX view;
            GetCameraViewMatrix(view, Eye);
            XMMATRIX invView = XMMatrixInverse(nullptr, view);

            XMVECTOR rayDir = XMVectorSet(ndcX, ndcY, 1.0f, 0.0f);
            rayDir = XMVector3TransformCoord(rayDir, invProj);
            rayDir = XMVector3TransformNormal(rayDir, invView);
            rayDir = XMVector3Normalize(rayDir);

            // 计算射线与XOY平面（z = 原点当前z坐标）的交点
            float originZ = g_axesOrigin.z;
            float eyeZ = XMVectorGetZ(Eye);
            float rayDirZ = XMVectorGetZ(rayDir);

            if (fabsf(rayDirZ) > 0.0001f)
            {
                float t = (originZ - eyeZ) / rayDirZ;
                XMVECTOR intersectPoint = XMVectorAdd(Eye, XMVectorScale(rayDir, t));

                // 计算新原点位置（只移动坐标轴显示，不改变图元位置）
                g_axesOrigin.x = XMVectorGetX(intersectPoint) + g_dragOffset.x;
                g_axesOrigin.y = XMVectorGetY(intersectPoint) + g_dragOffset.y;
            }

            g_lastMousePos.x = x;
            g_lastMousePos.y = y;
        }
        break;
    }
    case WM_MOUSEWHEEL:
    {
        int delta = GET_WHEEL_DELTA_WPARAM(wParam);

        if (g_selectedShape)
        {
            // 选中图元时，滚轮沿z轴移动图元
            float moveSpeed = 0.01f;
            g_selectedShape->position.z += delta * moveSpeed;
        }
        else
        {
            // 未选中图元时，滚轮控制摄像机缩放
            g_cameraDistance -= delta * 0.005f;
            if (g_cameraDistance < 2.0f)
                g_cameraDistance = 2.0f;
            if (g_cameraDistance > 50.0f)
                g_cameraDistance = 50.0f;
        }
        break;
    }
    case WM_RBUTTONDOWN:
    {
        g_lastMousePos.x = LOWORD(lParam);
        g_lastMousePos.y = HIWORD(lParam);
        SetCapture(hWnd);
        break;
    }
    case WM_RBUTTONUP:
        ReleaseCapture();
        break;
    case WM_MBUTTONDOWN:
    {
        g_middleButtonDragging = true;
        g_lastMousePos.x = LOWORD(lParam);
        g_lastMousePos.y = HIWORD(lParam);
        SetCapture(hWnd);
        break;
    }
    case WM_MBUTTONUP:
        g_middleButtonDragging = false;
        ReleaseCapture();
        break;
    case WM_KEYDOWN:
        if (wParam == VK_DELETE)
        {
            // Delete键删除选中的图元
            if (g_selectedShape)
            {
                auto it = std::find(g_shapes.begin(), g_shapes.end(), g_selectedShape);
                if (it != g_shapes.end())
                {
                    g_shapes.erase(it);
                }
                delete g_selectedShape;
                g_selectedShape = nullptr;
                g_statusText = L"提示: 图元已删除";
            }
            else
            {
                g_statusText = L"提示: 请先选择要删除的图元";
            }
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

// 初始化Direct3D
bool InitD3D()
{
    HRESULT hr;

    // 创建交换链描述
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

    // 创建设备和交换链
    D3D_FEATURE_LEVEL featureLevel;
    hr = D3D11CreateDeviceAndSwapChain(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr,
        0, nullptr, 0, D3D11_SDK_VERSION,
        &sd, &g_pSwapChain, &g_pd3dDevice,
        &featureLevel, &g_pImmediateContext);
    if (FAILED(hr))
        return false;

    // 创建渲染目标视图
    ID3D11Texture2D* pBackBuffer = nullptr;
    hr = g_pSwapChain->GetBuffer(0, __uuidof(ID3D11Texture2D), (void**)&pBackBuffer);
    if (FAILED(hr))
        return false;

    hr = g_pd3dDevice->CreateRenderTargetView(pBackBuffer, nullptr, &g_pRenderTargetView);
    pBackBuffer->Release();
    if (FAILED(hr))
        return false;

    // 创建深度模板缓冲区
    D3D11_TEXTURE2D_DESC depthDesc = {};
    depthDesc.Width = WINDOW_WIDTH;
    depthDesc.Height = WINDOW_HEIGHT;
    depthDesc.MipLevels = 1;
    depthDesc.ArraySize = 1;
    depthDesc.Format = DXGI_FORMAT_D24_UNORM_S8_UINT;
    depthDesc.SampleDesc.Count = 1;
    depthDesc.SampleDesc.Quality = 0;
    depthDesc.Usage = D3D11_USAGE_DEFAULT;
    depthDesc.BindFlags = D3D11_BIND_DEPTH_STENCIL;

    ID3D11Texture2D* pDepthStencil = nullptr;
    hr = g_pd3dDevice->CreateTexture2D(&depthDesc, nullptr, &pDepthStencil);
    if (FAILED(hr))
        return false;

    hr = g_pd3dDevice->CreateDepthStencilView(pDepthStencil, nullptr, &g_pDepthStencilView);
    pDepthStencil->Release();
    if (FAILED(hr))
        return false;

    g_pImmediateContext->OMSetRenderTargets(1, &g_pRenderTargetView, g_pDepthStencilView);

    // 设置视口
    D3D11_VIEWPORT vp;
    vp.Width = (float)WINDOW_WIDTH;
    vp.Height = (float)WINDOW_HEIGHT;
    vp.MinDepth = 0.0f;
    vp.MaxDepth = 1.0f;
    vp.TopLeftX = 0;
    vp.TopLeftY = 0;
    g_pImmediateContext->RSSetViewports(1, &vp);

    // 编译顶点着色器
    ID3DBlob* pVSBlob = nullptr;
    ID3DBlob* pErrorBlob = nullptr;
    hr = D3DCompile(g_vertexShaderCode, strlen(g_vertexShaderCode), nullptr, nullptr, nullptr,
        "main", "vs_5_0", 0, 0, &pVSBlob, &pErrorBlob);
    if (FAILED(hr))
    {
        if (pErrorBlob)
            pErrorBlob->Release();
        return false;
    }

    hr = g_pd3dDevice->CreateVertexShader(pVSBlob->GetBufferPointer(), pVSBlob->GetBufferSize(),
        nullptr, &g_pVertexShader);
    if (FAILED(hr))
    {
        pVSBlob->Release();
        return false;
    }

    // 创建输入布局
    D3D11_INPUT_ELEMENT_DESC layout[] = {
        {"POSITION", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 0, D3D11_INPUT_PER_VERTEX_DATA, 0},
        {"NORMAL", 0, DXGI_FORMAT_R32G32B32_FLOAT, 0, 12, D3D11_INPUT_PER_VERTEX_DATA, 0},
        {"COLOR", 0, DXGI_FORMAT_R32G32B32A32_FLOAT, 0, 24, D3D11_INPUT_PER_VERTEX_DATA, 0},
        {"TEXCOORD", 0, DXGI_FORMAT_R32G32_FLOAT, 0, 40, D3D11_INPUT_PER_VERTEX_DATA, 0},
    };

    hr = g_pd3dDevice->CreateInputLayout(layout, ARRAYSIZE(layout),
        pVSBlob->GetBufferPointer(),
        pVSBlob->GetBufferSize(), &g_pVertexLayout);
    pVSBlob->Release();
    if (FAILED(hr))
        return false;

    // 编译像素着色器
    ID3DBlob* pPSBlob = nullptr;
    hr = D3DCompile(g_pixelShaderCode, strlen(g_pixelShaderCode), nullptr, nullptr, nullptr,
        "main", "ps_5_0", 0, 0, &pPSBlob, &pErrorBlob);
    if (FAILED(hr))
    {
        if (pErrorBlob)
            pErrorBlob->Release();
        return false;
    }

    hr = g_pd3dDevice->CreatePixelShader(pPSBlob->GetBufferPointer(), pPSBlob->GetBufferSize(),
        nullptr, &g_pPixelShader);
    pPSBlob->Release();
    if (FAILED(hr))
        return false;

    // 创建常量缓冲区
    D3D11_BUFFER_DESC bd = {};
    bd.Usage = D3D11_USAGE_DEFAULT;
    bd.ByteWidth = sizeof(ConstantBuffer);
    bd.BindFlags = D3D11_BIND_CONSTANT_BUFFER;
    hr = g_pd3dDevice->CreateBuffer(&bd, nullptr, &g_pConstantBuffer);
    if (FAILED(hr))
        return false;

    // 创建光栅化状态
    D3D11_RASTERIZER_DESC rasterDesc = {};
    rasterDesc.FillMode = D3D11_FILL_SOLID;
    rasterDesc.CullMode = D3D11_CULL_BACK;
    rasterDesc.FrontCounterClockwise = FALSE;
    rasterDesc.DepthClipEnable = TRUE;
    hr = g_pd3dDevice->CreateRasterizerState(&rasterDesc, &g_pRasterizerState);
    if (FAILED(hr))
        return false;

    // 创建深度模板状态
    D3D11_DEPTH_STENCIL_DESC dsDesc = {};
    dsDesc.DepthEnable = TRUE;
    dsDesc.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL;
    dsDesc.DepthFunc = D3D11_COMPARISON_LESS;
    hr = g_pd3dDevice->CreateDepthStencilState(&dsDesc, &g_pDepthStencilState);
    if (FAILED(hr))
        return false;

    // 预创建线框光栅化状态（避免每帧重复创建）
    D3D11_RASTERIZER_DESC wireframeDesc = {};
    wireframeDesc.FillMode = D3D11_FILL_WIREFRAME;
    wireframeDesc.CullMode = D3D11_CULL_NONE;
    wireframeDesc.FrontCounterClockwise = FALSE;
    wireframeDesc.DepthClipEnable = TRUE;
    wireframeDesc.DepthBias = -100; // 深度偏移，使线框在实体前面
    wireframeDesc.DepthBiasClamp = 0.0f;
    wireframeDesc.SlopeScaledDepthBias = -1.0f; // 斜率缩放深度偏移
    wireframeDesc.AntialiasedLineEnable = TRUE; // 启用线条抗锯齿
    wireframeDesc.MultisampleEnable = FALSE;
    hr = g_pd3dDevice->CreateRasterizerState(&wireframeDesc, &g_pWireframeState);
    if (FAILED(hr))
        return false;

    // 创建混合状态（用于半透明渲染）
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
    if (FAILED(hr))
        return false;

    // 创建纹理采样器状态
    D3D11_SAMPLER_DESC sampDesc = {};
    sampDesc.Filter = D3D11_FILTER_MIN_MAG_MIP_LINEAR;
    sampDesc.AddressU = D3D11_TEXTURE_ADDRESS_WRAP;
    sampDesc.AddressV = D3D11_TEXTURE_ADDRESS_WRAP;
    sampDesc.AddressW = D3D11_TEXTURE_ADDRESS_WRAP;
    sampDesc.ComparisonFunc = D3D11_COMPARISON_NEVER;
    sampDesc.MinLOD = 0;
    sampDesc.MaxLOD = D3D11_FLOAT32_MAX;
    hr = g_pd3dDevice->CreateSamplerState(&sampDesc, &g_pSamplerState);
    if (FAILED(hr))
        return false;

    // 创建坐标轴顶点缓冲区（包含箭头）- 标准右手坐标系，Z轴向上
    {
        float axisLength = 5.0f;
        float arrowSize = 0.15f;
        XMFLOAT2 uv0(0.0f, 0.0f); // 坐标轴不使用纹理，UV设为0

        // 6个轴线顶点 + 18个箭头顶点（每个箭头由6个顶点3条线）
        std::vector<Vertex> axesVertices;

        // X轴 - 红色（沿+X方向）
        axesVertices.push_back({ {0.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        // X轴箭头
        axesVertices.push_back({ {axisLength, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength - arrowSize, 0.0f, arrowSize}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength - arrowSize, 0.0f, -arrowSize}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength - arrowSize, arrowSize, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {axisLength - arrowSize, -arrowSize, 0.0f}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });

        // Y轴 - 绿色（沿+Y方向）
        axesVertices.push_back({ {0.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, axisLength, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        // Y轴箭头
        axesVertices.push_back({ {0.0f, axisLength, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, axisLength - arrowSize, arrowSize}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, axisLength, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, axisLength - arrowSize, -arrowSize}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, axisLength, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {arrowSize, axisLength - arrowSize, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, axisLength, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {-arrowSize, axisLength - arrowSize, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });

        // Z轴 - 蓝色（垂直向上）
        axesVertices.push_back({ {0.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, 0.0f, axisLength}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        // Z轴箭头
        axesVertices.push_back({ {0.0f, 0.0f, axisLength}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {arrowSize, 0.0f, axisLength - arrowSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, 0.0f, axisLength}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {-arrowSize, 0.0f, axisLength - arrowSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, 0.0f, axisLength}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, arrowSize, axisLength - arrowSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, 0.0f, axisLength}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, -arrowSize, axisLength - arrowSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });

        // X标签（用线段画出 X 字母）- 在X轴末端（沿+X方向）
        float labelOffset = axisLength + 0.3f;
        float labelSize = 0.2f;
        axesVertices.push_back({ {labelOffset - labelSize, 0.0f, labelSize}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {labelOffset + labelSize, 0.0f, -labelSize}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {labelOffset - labelSize, 0.0f, -labelSize}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {labelOffset + labelSize, 0.0f, labelSize}, {1.0f, 0.0f, 0.0f}, {1.0f, 0.0f, 0.0f, 1.0f}, uv0 });

        // Y标签（用线段画出 Y 字母）- 在Y轴末端（沿+Y方向）
        axesVertices.push_back({ {-labelSize, labelOffset, labelSize}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, labelOffset, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {labelSize, labelOffset, labelSize}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, labelOffset, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, labelOffset, 0.0f}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {0.0f, labelOffset, -labelSize}, {0.0f, 1.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 1.0f}, uv0 });

        // Z标签（用线段画出 Z 字母）- 在Z轴末端（向上）
        axesVertices.push_back({ {-labelSize, 0.0f, labelOffset + labelSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {labelSize, 0.0f, labelOffset + labelSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {labelSize, 0.0f, labelOffset + labelSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {-labelSize, 0.0f, labelOffset - labelSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {-labelSize, 0.0f, labelOffset - labelSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });
        axesVertices.push_back({ {labelSize, 0.0f, labelOffset - labelSize}, {0.0f, 0.0f, 1.0f}, {0.0f, 0.0f, 1.0f, 1.0f}, uv0 });

        g_axesVertexCount = (UINT)axesVertices.size();

        D3D11_BUFFER_DESC axesBd = {};
        axesBd.Usage = D3D11_USAGE_DEFAULT;
        axesBd.ByteWidth = sizeof(Vertex) * g_axesVertexCount;
        axesBd.BindFlags = D3D11_BIND_VERTEX_BUFFER;

        D3D11_SUBRESOURCE_DATA axesInitData = {};
        axesInitData.pSysMem = axesVertices.data();

        hr = g_pd3dDevice->CreateBuffer(&axesBd, &axesInitData, &g_pAxesVertexBuffer);
        if (FAILED(hr))
            return false;
    }

    return true;
}

// 清理Direct3D资源
void CleanupD3D()
{
    // 清理选中指针
    g_selectedShape = nullptr;

    // 释放所有形状
    for (auto shape : g_shapes)
    {
        delete shape;
    }
    g_shapes.clear();

    // 使用SAFE_RELEASE宏释放D3D资源（精简代码）
    SAFE_RELEASE(g_pSamplerState);
    SAFE_RELEASE(g_pBlendState);
    SAFE_RELEASE(g_pAxesVertexBuffer);
    SAFE_RELEASE(g_pDepthStencilState);
    SAFE_RELEASE(g_pWireframeState);
    SAFE_RELEASE(g_pRasterizerState);
    SAFE_RELEASE(g_pConstantBuffer);
    SAFE_RELEASE(g_pVertexLayout);
    SAFE_RELEASE(g_pVertexShader);
    SAFE_RELEASE(g_pPixelShader);
    SAFE_RELEASE(g_pDepthStencilView);
    SAFE_RELEASE(g_pRenderTargetView);
    SAFE_RELEASE(g_pSwapChain);
    SAFE_RELEASE(g_pImmediateContext);
    SAFE_RELEASE(g_pd3dDevice);
}

// 辅助函数：获取视图矩阵和摄像机位置（避免代码重复）
// 注意：Z轴向上为高度方向
void GetCameraViewMatrix(XMMATRIX& outView, XMVECTOR& outEye)
{
    // 在XY平面上绕转，Z轴向上
    outEye = XMVectorSet(
        g_cameraDistance * cosf(g_cameraPitch) * cosf(g_cameraYaw),
        g_cameraDistance * cosf(g_cameraPitch) * sinf(g_cameraYaw),
        g_cameraDistance * sinf(g_cameraPitch),
        0.0f);
    XMVECTOR At = XMVectorSet(0.0f, 0.0f, 0.0f, 0.0f);
    XMVECTOR Up = XMVectorSet(0.0f, 0.0f, 1.0f, 0.0f); // Z轴向上
    outView = XMMatrixLookAtLH(outEye, At, Up);
}

// 渲染场景
void Render()
{
    // 安全检查
    if (!g_pImmediateContext || !g_pRenderTargetView || !g_pDepthStencilView)
        return;

    // 清除缓冲区 - 淡灰色背景
    float clearColor[4] = { 0.75f, 0.75f, 0.78f, 1.0f };
    g_pImmediateContext->ClearRenderTargetView(g_pRenderTargetView, clearColor);
    g_pImmediateContext->ClearDepthStencilView(g_pDepthStencilView, D3D11_CLEAR_DEPTH, 1.0f, 0);

    // 设置视图矩阵（使用辅助函数避免重复代码）
    XMVECTOR Eye;
    XMMATRIX view;
    GetCameraViewMatrix(view, Eye);

    // 设置投影矩阵
    XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4,
        (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT,
        0.01f, 100.0f);

    // 设置渲染状态
    g_pImmediateContext->IASetInputLayout(g_pVertexLayout);
    g_pImmediateContext->VSSetShader(g_pVertexShader, nullptr, 0);
    g_pImmediateContext->PSSetShader(g_pPixelShader, nullptr, 0);
    g_pImmediateContext->RSSetState(g_pRasterizerState);
    g_pImmediateContext->OMSetDepthStencilState(g_pDepthStencilState, 1);

    // 启用混合状态实现半透明渲染
    float blendFactor[4] = { 0.0f, 0.0f, 0.0f, 0.0f };
    g_pImmediateContext->OMSetBlendState(g_pBlendState, blendFactor, 0xffffffff);

    // 获取摄像机位置用于镜面反射计算
    XMFLOAT3 cameraPos;
    XMStoreFloat3(&cameraPos, Eye);

    // 渲染所有形状
    for (auto shape : g_shapes)
    {
        if (!shape->vertexBuffer || !shape->indexBuffer)
            continue;

        // 准备常量缓冲区
        ConstantBuffer cb;
        cb.world = XMMatrixTranspose(shape->GetWorldMatrix());
        cb.view = XMMatrixTranspose(view);
        cb.projection = XMMatrixTranspose(projection);
        cb.lightDir = XMFLOAT4(g_lightDirection.x, g_lightDirection.y, g_lightDirection.z, 0.0f);
        cb.lightColor = XMFLOAT4(g_lightColor.x, g_lightColor.y, g_lightColor.z, 1.0f);
        // 传递摄像机位置
        cb.cameraPos = XMFLOAT4(cameraPos.x, cameraPos.y, cameraPos.z, 1.0f);
        // 传递材质参数
        cb.matAmbient = XMFLOAT4(shape->material.ambient.x, shape->material.ambient.y, shape->material.ambient.z, 1.0f);
        cb.matDiffuse = XMFLOAT4(shape->material.diffuse.x, shape->material.diffuse.y, shape->material.diffuse.z, 1.0f);
        cb.matSpecular = XMFLOAT4(shape->material.specular.x, shape->material.specular.y, shape->material.specular.z, shape->material.shininess);
        // 传递纹理模式
        cb.textureInfo = XMFLOAT4((float)shape->textureMode, 0.0f, 0.0f, 0.0f);
        g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cb, 0, 0);

        // 设置顶点缓冲区
        UINT stride = sizeof(Vertex);
        UINT offset = 0;
        g_pImmediateContext->IASetVertexBuffers(0, 1, &shape->vertexBuffer, &stride, &offset);
        g_pImmediateContext->IASetIndexBuffer(shape->indexBuffer, DXGI_FORMAT_R32_UINT, 0);
        g_pImmediateContext->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
        g_pImmediateContext->VSSetConstantBuffers(0, 1, &g_pConstantBuffer);
        g_pImmediateContext->PSSetConstantBuffers(0, 1, &g_pConstantBuffer);

        // 绑定纹理和采样器
        if (shape->textureView && shape->textureMode > 0)
        {
            g_pImmediateContext->PSSetShaderResources(0, 1, &shape->textureView);
            g_pImmediateContext->PSSetSamplers(0, 1, &g_pSamplerState);
        }
        else
        {
            // 无纹理时绑定空资源
            ID3D11ShaderResourceView* nullSRV = nullptr;
            g_pImmediateContext->PSSetShaderResources(0, 1, &nullSRV);
        }

        // 绘制
        g_pImmediateContext->DrawIndexed(shape->indexCount, 0, 0);

        // 绘制所有图元的棱边线框（使用淡化效果减少存在感）
        // 仅对球体和圆柱体跳过棱边绘制，其他形状使用极淡的棱边
        if (shape->type != SHAPE_SPHERE && shape->type != SHAPE_CYLINDER)
        {
            g_pImmediateContext->RSSetState(g_pWireframeState);

            // 修改常量缓冲区使用极淡的颜色来减少棱边存在感
            ConstantBuffer cbWire;
            cbWire.world = XMMatrixTranspose(shape->GetWorldMatrix());
            cbWire.view = XMMatrixTranspose(view);
            cbWire.projection = XMMatrixTranspose(projection);
            cbWire.lightDir = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);   // 无光照
            cbWire.lightColor = XMFLOAT4(0.6f, 0.6f, 0.6f, 0.3f); // 极淡的灰色
            cbWire.cameraPos = XMFLOAT4(cameraPos.x, cameraPos.y, cameraPos.z, 1.0f);
            cbWire.matAmbient = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
            cbWire.matDiffuse = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
            cbWire.matSpecular = XMFLOAT4(0.0f, 0.0f, 0.0f, 1.0f); // 无镜面反射
            cbWire.textureInfo = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f); // 无纹理
            g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cbWire, 0, 0);

            g_pImmediateContext->DrawIndexed(shape->indexCount, 0, 0);
        }

        // 恢复状态
        g_pImmediateContext->RSSetState(g_pRasterizerState);
        g_pImmediateContext->OMSetBlendState(g_pBlendState, blendFactor, 0xffffffff);

        // 如果被选中，绘制高亮线框（白色）
        if (shape->selected && g_pWireframeState)
        {
            g_pImmediateContext->OMSetBlendState(nullptr, blendFactor, 0xffffffff);
            g_pImmediateContext->RSSetState(g_pWireframeState);
            ConstantBuffer cbWireSelected;
            cbWireSelected.world = XMMatrixTranspose(shape->GetWorldMatrix());
            cbWireSelected.view = XMMatrixTranspose(view);
            cbWireSelected.projection = XMMatrixTranspose(projection);
            cbWireSelected.lightDir = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f);
            cbWireSelected.lightColor = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f); // 白色高亮
            cbWireSelected.cameraPos = XMFLOAT4(cameraPos.x, cameraPos.y, cameraPos.z, 1.0f);
            cbWireSelected.matAmbient = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
            cbWireSelected.matDiffuse = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
            cbWireSelected.matSpecular = XMFLOAT4(0.0f, 0.0f, 0.0f, 1.0f); // 无镜面反射
            cbWireSelected.textureInfo = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f); // 无纹理
            g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cbWireSelected, 0, 0);
            g_pImmediateContext->DrawIndexed(shape->indexCount, 0, 0);
            g_pImmediateContext->RSSetState(g_pRasterizerState);
            g_pImmediateContext->OMSetBlendState(g_pBlendState, blendFactor, 0xffffffff);
        }
    }

    // 绘制坐标轴
    if (g_showAxes && g_pAxesVertexBuffer)
    {
        // 应用坐标轴原点偏移
        XMMATRIX axesWorld = XMMatrixTranslation(g_axesOrigin.x, g_axesOrigin.y, g_axesOrigin.z);
        ConstantBuffer cbAxes;
        cbAxes.world = XMMatrixTranspose(axesWorld);
        cbAxes.view = XMMatrixTranspose(view);
        cbAxes.projection = XMMatrixTranspose(projection);
        cbAxes.lightDir = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f); // 坐标轴不受光照影响
        cbAxes.lightColor = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
        cbAxes.cameraPos = XMFLOAT4(cameraPos.x, cameraPos.y, cameraPos.z, 1.0f);
        cbAxes.matAmbient = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
        cbAxes.matDiffuse = XMFLOAT4(1.0f, 1.0f, 1.0f, 1.0f);
        cbAxes.matSpecular = XMFLOAT4(0.0f, 0.0f, 0.0f, 1.0f);
        cbAxes.textureInfo = XMFLOAT4(0.0f, 0.0f, 0.0f, 0.0f); // 无纹理
        g_pImmediateContext->UpdateSubresource(g_pConstantBuffer, 0, nullptr, &cbAxes, 0, 0);

        // 坐标轴不使用纹理
        ID3D11ShaderResourceView* nullSRV = nullptr;
        g_pImmediateContext->PSSetShaderResources(0, 1, &nullSRV);

        UINT stride = sizeof(Vertex);
        UINT offset = 0;
        g_pImmediateContext->IASetVertexBuffers(0, 1, &g_pAxesVertexBuffer, &stride, &offset);
        g_pImmediateContext->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_LINELIST);
        g_pImmediateContext->VSSetConstantBuffers(0, 1, &g_pConstantBuffer);
        g_pImmediateContext->PSSetConstantBuffers(0, 1, &g_pConstantBuffer);
        g_pImmediateContext->Draw(g_axesVertexCount, 0); // 绘制坐标轴、箭头和标签
    }

    // 呈现
    g_pSwapChain->Present(0, 0);

    // 更新窗口标题显示状态信息
    SetWindowText(g_hWnd, (L"3D图形绘制与编辑软件 - " + g_statusText).c_str());
}

// 创建球体
void CreateSphere(float radius, int slices, int stacks, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    for (int stack = 0; stack <= stacks; ++stack)
    {
        float phi = XM_PI * stack / stacks;
        for (int slice = 0; slice <= slices; ++slice)
        {
            float theta = 2.0f * XM_PI * slice / slices;

            Vertex v;
            v.position.x = radius * sinf(phi) * cosf(theta);
            v.position.y = radius * cosf(phi);
            v.position.z = radius * sinf(phi) * sinf(theta);

            XMVECTOR pos = XMLoadFloat3(&v.position);
            XMVECTOR norm = XMVector3Normalize(pos);
            XMStoreFloat3(&v.normal, norm);

            v.color = XMFLOAT4(0.5f, 0.5f, 0.8f, 1.0f);
            // 纹理坐标：U沿经度，V沿纬度
            v.texCoord = XMFLOAT2((float)slice / slices, (float)stack / stacks);
            vertices.push_back(v);
        }
    }

    for (int stack = 0; stack < stacks; ++stack)
    {
        for (int slice = 0; slice < slices; ++slice)
        {
            int first = stack * (slices + 1) + slice;
            int second = first + slices + 1;

            // 顺时针绕组（从外部看）使外表面为正面
            indices.push_back(first);
            indices.push_back(first + 1);
            indices.push_back(second);

            indices.push_back(second);
            indices.push_back(first + 1);
            indices.push_back(second + 1);
        }
    }
}

// 创建圆柱体
void CreateCylinder(float radius, float height, int slices, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    float halfHeight = height * 0.5f;

    // 顶部圆心
    Vertex topCenter;
    topCenter.position = XMFLOAT3(0, halfHeight, 0);
    topCenter.normal = XMFLOAT3(0, 1, 0);
    topCenter.color = XMFLOAT4(0.8f, 0.5f, 0.5f, 1.0f);
    topCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(topCenter);

    // 底部圆心
    Vertex bottomCenter;
    bottomCenter.position = XMFLOAT3(0, -halfHeight, 0);
    bottomCenter.normal = XMFLOAT3(0, -1, 0);
    bottomCenter.color = XMFLOAT4(0.8f, 0.5f, 0.5f, 1.0f);
    bottomCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(bottomCenter);

    // 侧面顶部圆
    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = halfHeight;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(cosf(theta), 0, sinf(theta));
        v.color = XMFLOAT4(0.8f, 0.5f, 0.5f, 1.0f);
        v.texCoord = XMFLOAT2((float)i / slices, 0.0f);
        vertices.push_back(v);
    }

    // 侧面底部圆
    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = -halfHeight;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(cosf(theta), 0, sinf(theta));
        v.color = XMFLOAT4(0.8f, 0.5f, 0.5f, 1.0f);
        v.texCoord = XMFLOAT2((float)i / slices, 1.0f);
        vertices.push_back(v);
    }

    // 顶部盖子索引 - 顺时针（从上方看）
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(0);
        indices.push_back(2 + i + 1);
        indices.push_back(2 + i);
    }

    // 底部盖子索引
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(1);
        indices.push_back(2 + slices + 1 + i + 1);
        indices.push_back(2 + slices + 1 + i);
    }

    // 侧面索引 - 顺时针（从外部看）
    int topStart = 2;
    int bottomStart = 2 + slices + 1;
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(topStart + i);
        indices.push_back(topStart + i + 1);
        indices.push_back(bottomStart + i);

        indices.push_back(topStart + i + 1);
        indices.push_back(bottomStart + i + 1);
        indices.push_back(bottomStart + i);
    }
}

// 创建平面
void CreatePlane(float width, float height, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    // 创建一个很大的平面（模拟无限延展）
    float halfW = width * 10.0f; // 扩大平面尺寸
    float halfH = height * 10.0f;

    XMFLOAT4 planeColor = XMFLOAT4(0.5f, 0.8f, 0.5f, 0.7f);

    // 正面（法线朝上）
    Vertex v;
    v.normal = XMFLOAT3(0, 1, 0);
    v.color = planeColor;

    v.position = XMFLOAT3(-halfW, 0, -halfH);
    v.texCoord = XMFLOAT2(0.0f, 0.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(-halfW, 0, halfH);
    v.texCoord = XMFLOAT2(0.0f, 10.0f); // 平铺纹理
    vertices.push_back(v);
    v.position = XMFLOAT3(halfW, 0, halfH);
    v.texCoord = XMFLOAT2(10.0f, 10.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(halfW, 0, -halfH);
    v.texCoord = XMFLOAT2(10.0f, 0.0f);
    vertices.push_back(v);

    // 反面（法线朝下）
    v.normal = XMFLOAT3(0, -1, 0);
    v.position = XMFLOAT3(-halfW, 0, -halfH);
    v.texCoord = XMFLOAT2(0.0f, 0.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(halfW, 0, -halfH);
    v.texCoord = XMFLOAT2(10.0f, 0.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(halfW, 0, halfH);
    v.texCoord = XMFLOAT2(10.0f, 10.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(-halfW, 0, halfH);
    v.texCoord = XMFLOAT2(0.0f, 10.0f);
    vertices.push_back(v);

    // 正面索引
    indices = { 0, 1, 2, 0, 2, 3,
        // 反面索引
        4, 5, 6, 4, 6, 7 };
}

// 创建立方体
void CreateCube(float size, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    float half = size * 0.5f;
    XMFLOAT4 color = XMFLOAT4(0.8f, 0.8f, 0.5f, 1.0f);
    XMFLOAT2 uv00(0.0f, 0.0f), uv01(0.0f, 1.0f), uv10(1.0f, 0.0f), uv11(1.0f, 1.0f);

    // 前面
    vertices.push_back({ XMFLOAT3(-half, -half, -half), XMFLOAT3(0, 0, -1), color, uv00 });
    vertices.push_back({ XMFLOAT3(-half, half, -half), XMFLOAT3(0, 0, -1), color, uv01 });
    vertices.push_back({ XMFLOAT3(half, half, -half), XMFLOAT3(0, 0, -1), color, uv11 });
    vertices.push_back({ XMFLOAT3(half, -half, -half), XMFLOAT3(0, 0, -1), color, uv10 });

    // 后面
    vertices.push_back({ XMFLOAT3(half, -half, half), XMFLOAT3(0, 0, 1), color, uv00 });
    vertices.push_back({ XMFLOAT3(half, half, half), XMFLOAT3(0, 0, 1), color, uv01 });
    vertices.push_back({ XMFLOAT3(-half, half, half), XMFLOAT3(0, 0, 1), color, uv11 });
    vertices.push_back({ XMFLOAT3(-half, -half, half), XMFLOAT3(0, 0, 1), color, uv10 });

    // 左面
    vertices.push_back({ XMFLOAT3(-half, -half, half), XMFLOAT3(-1, 0, 0), color, uv00 });
    vertices.push_back({ XMFLOAT3(-half, half, half), XMFLOAT3(-1, 0, 0), color, uv01 });
    vertices.push_back({ XMFLOAT3(-half, half, -half), XMFLOAT3(-1, 0, 0), color, uv11 });
    vertices.push_back({ XMFLOAT3(-half, -half, -half), XMFLOAT3(-1, 0, 0), color, uv10 });

    // 右面
    vertices.push_back({ XMFLOAT3(half, -half, -half), XMFLOAT3(1, 0, 0), color, uv00 });
    vertices.push_back({ XMFLOAT3(half, half, -half), XMFLOAT3(1, 0, 0), color, uv01 });
    vertices.push_back({ XMFLOAT3(half, half, half), XMFLOAT3(1, 0, 0), color, uv11 });
    vertices.push_back({ XMFLOAT3(half, -half, half), XMFLOAT3(1, 0, 0), color, uv10 });

    // 顶面
    vertices.push_back({ XMFLOAT3(-half, half, -half), XMFLOAT3(0, 1, 0), color, uv00 });
    vertices.push_back({ XMFLOAT3(-half, half, half), XMFLOAT3(0, 1, 0), color, uv01 });
    vertices.push_back({ XMFLOAT3(half, half, half), XMFLOAT3(0, 1, 0), color, uv11 });
    vertices.push_back({ XMFLOAT3(half, half, -half), XMFLOAT3(0, 1, 0), color, uv10 });

    // 底面
    vertices.push_back({ XMFLOAT3(-half, -half, half), XMFLOAT3(0, -1, 0), color, uv00 });
    vertices.push_back({ XMFLOAT3(-half, -half, -half), XMFLOAT3(0, -1, 0), color, uv01 });
    vertices.push_back({ XMFLOAT3(half, -half, -half), XMFLOAT3(0, -1, 0), color, uv11 });
    vertices.push_back({ XMFLOAT3(half, -half, half), XMFLOAT3(0, -1, 0), color, uv10 });

    // 索引
    for (int i = 0; i < 6; ++i)
    {
        int base = i * 4;
        indices.push_back(base + 0);
        indices.push_back(base + 1);
        indices.push_back(base + 2);
        indices.push_back(base + 0);
        indices.push_back(base + 2);
        indices.push_back(base + 3);
    }
}

// 创建四面体
void CreateTetrahedron(float size, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    XMFLOAT4 color = XMFLOAT4(0.8f, 0.5f, 0.8f, 1.0f);
    float h = size * sqrtf(2.0f / 3.0f);
    float r = size / sqrtf(3.0f);

    XMFLOAT3 v0(0, h, 0);
    XMFLOAT3 v1(-size * 0.5f, 0, r);
    XMFLOAT3 v2(size * 0.5f, 0, r);
    XMFLOAT3 v3(0, 0, -size / sqrtf(3.0f));

    // 面1
    XMVECTOR n1 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v1), XMLoadFloat3(&v0)),
        XMVectorSubtract(XMLoadFloat3(&v2), XMLoadFloat3(&v0))));
    XMFLOAT3 normal1;
    XMStoreFloat3(&normal1, n1);

    vertices.push_back({ v0, normal1, color, XMFLOAT2(0.5f, 0.0f) });
    vertices.push_back({ v1, normal1, color, XMFLOAT2(0.0f, 1.0f) });
    vertices.push_back({ v2, normal1, color, XMFLOAT2(1.0f, 1.0f) });

    // 面2
    XMVECTOR n2 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v2), XMLoadFloat3(&v0)),
        XMVectorSubtract(XMLoadFloat3(&v3), XMLoadFloat3(&v0))));
    XMFLOAT3 normal2;
    XMStoreFloat3(&normal2, n2);

    vertices.push_back({ v0, normal2, color, XMFLOAT2(0.5f, 0.0f) });
    vertices.push_back({ v2, normal2, color, XMFLOAT2(0.0f, 1.0f) });
    vertices.push_back({ v3, normal2, color, XMFLOAT2(1.0f, 1.0f) });

    // 面3
    XMVECTOR n3 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v3), XMLoadFloat3(&v0)),
        XMVectorSubtract(XMLoadFloat3(&v1), XMLoadFloat3(&v0))));
    XMFLOAT3 normal3;
    XMStoreFloat3(&normal3, n3);

    vertices.push_back({ v0, normal3, color, XMFLOAT2(0.5f, 0.0f) });
    vertices.push_back({ v3, normal3, color, XMFLOAT2(0.0f, 1.0f) });
    vertices.push_back({ v1, normal3, color, XMFLOAT2(1.0f, 1.0f) });

    // 底面
    XMVECTOR n4 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v2), XMLoadFloat3(&v1)),
        XMVectorSubtract(XMLoadFloat3(&v3), XMLoadFloat3(&v1))));
    XMFLOAT3 normal4;
    XMStoreFloat3(&normal4, n4);

    vertices.push_back({ v1, normal4, color, XMFLOAT2(0.0f, 0.0f) });
    vertices.push_back({ v3, normal4, color, XMFLOAT2(0.5f, 1.0f) });
    vertices.push_back({ v2, normal4, color, XMFLOAT2(1.0f, 0.0f) });

    // 索引
    for (UINT i = 0; i < 12; ++i)
    {
        indices.push_back(i);
    }
}

// 更新形状的顶点缓冲区颜色（用于材质修改后生效）
bool UpdateShapeVertexColor(Shape3D* shape)
{
    if (!shape || !g_pd3dDevice)
        return false;

    std::vector<Vertex> vertices;
    std::vector<UINT> indices;

    // 根据类型重新生成顶点数据
    switch (shape->type)
    {
    case SHAPE_SPHERE:
        CreateSphere(1.0f, 32, 16, vertices, indices);
        break;
    case SHAPE_CYLINDER:
        CreateCylinder(0.5f, 2.0f, 32, vertices, indices);
        break;
    case SHAPE_PLANE:
        CreatePlane(2.0f, 2.0f, vertices, indices);
        break;
    case SHAPE_CUBE:
        CreateCube(1.5f, vertices, indices);
        break;
    case SHAPE_TETRAHEDRON:
        CreateTetrahedron(1.5f, vertices, indices);
        break;
    default:
        return false;
    }

    // 材质参数现在通过常量缓冲区传递给着色器
    // 顶点颜色保持为白色基础色，只保留透明度
    // 这样着色器可以正确应用完整的Phong光照模型
    XMFLOAT4 baseColor = XMFLOAT4(1.0f, 1.0f, 1.0f, shape->color.w);
    for (auto& v : vertices)
    {
        v.color = baseColor;
    }

    // 更新shape->color为白色基础色（材质颜色通过常量缓冲区传递）
    shape->color = baseColor;

    // 释放旧的顶点缓冲区
    if (shape->vertexBuffer)
    {
        shape->vertexBuffer->Release();
        shape->vertexBuffer = nullptr;
    }

    // 创建新的顶点缓冲区
    D3D11_BUFFER_DESC bd = {};
    bd.Usage = D3D11_USAGE_DEFAULT;
    bd.ByteWidth = sizeof(Vertex) * vertices.size();
    bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;

    D3D11_SUBRESOURCE_DATA initData = {};
    initData.pSysMem = vertices.data();

    HRESULT hr = g_pd3dDevice->CreateBuffer(&bd, &initData, &shape->vertexBuffer);
    return SUCCEEDED(hr);
}

// 从BMP文件加载纹理（简化版本，只支持24/32位BMP）
bool LoadTextureFromFile(const wchar_t* filename, ID3D11ShaderResourceView** textureView)
{
    if (!g_pd3dDevice || !filename || !textureView)
        return false;

    *textureView = nullptr;

    // 打开文件
    HANDLE hFile = CreateFileW(filename, GENERIC_READ, FILE_SHARE_READ, nullptr,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hFile == INVALID_HANDLE_VALUE)
        return false;

    // 读取BMP文件头
    BITMAPFILEHEADER bmpFileHeader;
    DWORD bytesRead;
    if (!ReadFile(hFile, &bmpFileHeader, sizeof(bmpFileHeader), &bytesRead, nullptr) ||
        bmpFileHeader.bfType != 0x4D42) // "BM"
    {
        CloseHandle(hFile);
        return false;
    }

    // 读取BMP信息头
    BITMAPINFOHEADER bmpInfoHeader;
    if (!ReadFile(hFile, &bmpInfoHeader, sizeof(bmpInfoHeader), &bytesRead, nullptr))
    {
        CloseHandle(hFile);
        return false;
    }

    // 检查是否为支持的格式（24位或32位）
    if (bmpInfoHeader.biBitCount != 24 && bmpInfoHeader.biBitCount != 32)
    {
        CloseHandle(hFile);
        return false;
    }

    int width = bmpInfoHeader.biWidth;
    int height = abs(bmpInfoHeader.biHeight);
    bool topDown = bmpInfoHeader.biHeight < 0;
    int bytesPerPixel = bmpInfoHeader.biBitCount / 8;
    int rowPitch = ((width * bytesPerPixel + 3) / 4) * 4; // BMP行对齐到4字节

    // 读取像素数据
    SetFilePointer(hFile, bmpFileHeader.bfOffBits, nullptr, FILE_BEGIN);
    std::vector<BYTE> bmpData(rowPitch * height);
    if (!ReadFile(hFile, bmpData.data(), rowPitch * height, &bytesRead, nullptr))
    {
        CloseHandle(hFile);
        return false;
    }
    CloseHandle(hFile);

    // 转换为RGBA格式
    std::vector<BYTE> textureData(width * height * 4);
    for (int y = 0; y < height; y++)
    {
        int srcY = topDown ? y : (height - 1 - y);
        for (int x = 0; x < width; x++)
        {
            int srcIdx = srcY * rowPitch + x * bytesPerPixel;
            int dstIdx = (y * width + x) * 4;

            // BMP是BGR顺序，转换为RGBA
            textureData[dstIdx + 0] = bmpData[srcIdx + 2];                              // R
            textureData[dstIdx + 1] = bmpData[srcIdx + 1];                              // G
            textureData[dstIdx + 2] = bmpData[srcIdx + 0];                              // B
            textureData[dstIdx + 3] = (bytesPerPixel == 4) ? bmpData[srcIdx + 3] : 255; // A
        }
    }

    // 创建纹理
    D3D11_TEXTURE2D_DESC texDesc = {};
    texDesc.Width = width;
    texDesc.Height = height;
    texDesc.MipLevels = 1;
    texDesc.ArraySize = 1;
    texDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    texDesc.SampleDesc.Count = 1;
    texDesc.Usage = D3D11_USAGE_DEFAULT;
    texDesc.BindFlags = D3D11_BIND_SHADER_RESOURCE;

    D3D11_SUBRESOURCE_DATA initData = {};
    initData.pSysMem = textureData.data();
    initData.SysMemPitch = width * 4;

    ID3D11Texture2D* pTexture = nullptr;
    HRESULT hr = g_pd3dDevice->CreateTexture2D(&texDesc, &initData, &pTexture);
    if (FAILED(hr))
        return false;

    // 创建着色器资源视图
    D3D11_SHADER_RESOURCE_VIEW_DESC srvDesc = {};
    srvDesc.Format = texDesc.Format;
    srvDesc.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2D;
    srvDesc.Texture2D.MipLevels = 1;

    hr = g_pd3dDevice->CreateShaderResourceView(pTexture, &srvDesc, textureView);
    pTexture->Release();

    return SUCCEEDED(hr);
}

// 创建形状
Shape3D* CreateShape(ShapeType type)
{
    // 安全检查：确保D3D设备已初始化
    if (!g_pd3dDevice)
        return nullptr;

    Shape3D* shape = new (std::nothrow) Shape3D(); // 使用nothrow避免异常
    if (!shape)
        return nullptr;

    shape->type = type;

    std::vector<Vertex> vertices;
    std::vector<UINT> indices;

    switch (type)
    {
    case SHAPE_SPHERE:
        CreateSphere(1.0f, 32, 16, vertices, indices);
        shape->color = XMFLOAT4(0.5f, 0.5f, 0.8f, 0.7f); // 半透明
        break;
    case SHAPE_CYLINDER:
        CreateCylinder(0.5f, 2.0f, 32, vertices, indices);
        shape->color = XMFLOAT4(0.8f, 0.5f, 0.5f, 0.7f); // 半透明
        break;
    case SHAPE_PLANE:
        CreatePlane(2.0f, 2.0f, vertices, indices);
        shape->color = XMFLOAT4(0.5f, 0.8f, 0.5f, 0.7f); // 半透明
        break;
    case SHAPE_CUBE:
        CreateCube(1.5f, vertices, indices);
        shape->color = XMFLOAT4(0.8f, 0.8f, 0.5f, 0.7f); // 半透明
        break;
    case SHAPE_TETRAHEDRON:
        CreateTetrahedron(1.5f, vertices, indices);
        shape->color = XMFLOAT4(0.8f, 0.5f, 0.8f, 0.7f); // 半透明
        break;
    }

    // 应用颜色到顶点
    for (auto& v : vertices)
    {
        v.color = shape->color;
    }

    // 创建顶点缓冲区
    D3D11_BUFFER_DESC bd = {};
    bd.Usage = D3D11_USAGE_DEFAULT;
    bd.ByteWidth = sizeof(Vertex) * vertices.size();
    bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;

    D3D11_SUBRESOURCE_DATA initData = {};
    initData.pSysMem = vertices.data();

    HRESULT hr = g_pd3dDevice->CreateBuffer(&bd, &initData, &shape->vertexBuffer);
    if (FAILED(hr))
    {
        delete shape;
        return nullptr;
    }

    // 创建索引缓冲区
    bd.ByteWidth = sizeof(UINT) * indices.size();
    bd.BindFlags = D3D11_BIND_INDEX_BUFFER;
    initData.pSysMem = indices.data();

    hr = g_pd3dDevice->CreateBuffer(&bd, &initData, &shape->indexBuffer);
    if (FAILED(hr))
    {
        delete shape;
        return nullptr;
    }

    shape->indexCount = indices.size();

    // 设置随机位置
    static int shapeCount = 0;
    float angle = shapeCount * XM_PI * 0.4f;
    shape->position = XMFLOAT3(3.0f * cosf(angle), 0, 3.0f * sinf(angle));
    shapeCount++;

    return shape;
}

// 拾取形状（简化的射线检测）
Shape3D* PickShape(int x, int y)
{
    // 将屏幕坐标转换为NDC
    float ndcX = (2.0f * x / WINDOW_WIDTH) - 1.0f;
    float ndcY = 1.0f - (2.0f * y / WINDOW_HEIGHT);

    // 计算投影矩阵的逆
    XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4,
        (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT,
        0.01f, 100.0f);
    XMMATRIX invProj = XMMatrixInverse(nullptr, projection);

    // 计算视图空间中的射线方向
    XMVECTOR rayDir = XMVectorSet(ndcX, ndcY, 1.0f, 0.0f);
    rayDir = XMVector3TransformCoord(rayDir, invProj);

    // 使用辅助函数获取视图矩阵（避免代码重复）
    XMVECTOR Eye;
    XMMATRIX view;
    GetCameraViewMatrix(view, Eye);
    XMMATRIX invView = XMMatrixInverse(nullptr, view);

    // 世界空间中的射线
    XMVECTOR rayOrigin = Eye;
    rayDir = XMVector3TransformNormal(rayDir, invView);
    rayDir = XMVector3Normalize(rayDir);

    // 射线与变换后的图元相交测试
    Shape3D* closest = nullptr;
    float minDist = FLT_MAX;

    for (auto shape : g_shapes)
    {
        // 获取图元的世界变换矩阵的逆
        XMMATRIX worldMatrix = shape->GetWorldMatrix();
        XMMATRIX invWorld = XMMatrixInverse(nullptr, worldMatrix);

        // 将射线变换到图元的本地坐标系
        XMVECTOR localRayOrigin = XMVector3TransformCoord(rayOrigin, invWorld);
        XMVECTOR localRayDir = XMVector3TransformNormal(rayDir, invWorld);
        localRayDir = XMVector3Normalize(localRayDir);

        // 根据图元类型设置包围球半径（本地空间）
        float boundRadius = 1.0f; // 默认包围球半径
        switch (shape->type)
        {
        case SHAPE_SPHERE:
            boundRadius = 1.0f;
            break;
        case SHAPE_CUBE:
            boundRadius = 0.87f; // 立方体对角线的一半 / sqrt(3)
            break;
        case SHAPE_CYLINDER:
            boundRadius = 1.12f; // 圆柱体的包围球
            break;
        case SHAPE_CONE:
            boundRadius = 1.12f;
            break;
        case SHAPE_TETRAHEDRON:
            boundRadius = 0.87f;
            break;
        case SHAPE_PLANE:
            boundRadius = 10.0f; // 平面较大
            break;
        }

        // 在本地空间进行射线-球体相交测试（包围球中心在原点）
        XMVECTOR toCenter = XMVectorNegate(localRayOrigin);
        float projLen = XMVectorGetX(XMVector3Dot(toCenter, localRayDir));

        if (projLen > 0)
        {
            XMVECTOR closestPoint = XMVectorAdd(localRayOrigin, XMVectorScale(localRayDir, projLen));
            float dist = XMVectorGetX(XMVector3Length(closestPoint));

            if (dist < boundRadius)
            {
                // 计算在世界空间中的距离（用于排序）
                XMVECTOR shapePos = XMLoadFloat3(&shape->position);
                float worldDist = XMVectorGetX(XMVector3Length(XMVectorSubtract(shapePos, rayOrigin)));

                if (worldDist < minDist)
                {
                    minDist = worldDist;
                    closest = shape;
                }
            }
        }
    }

    return closest;
}

// 简化的实体属性编辑（使用消息框）
void ShowShapePropertiesDialog(HWND hWnd)
{
    if (!g_selectedShape)
        return;

    wchar_t message[512];

    swprintf_s(message, L"当前属性：\n"
        L"位置: (%.2f, %.2f, %.2f)\n"
        L"旋转: (%.0f°, %.0f°, %.0f°)\n"
        L"缩放: (%.2f, %.2f, %.2f)\n\n"
        L"请输入新值（格式：x,y,z），或点击取消保持不变",
        g_selectedShape->position.x, g_selectedShape->position.y, g_selectedShape->position.z,
        XMConvertToDegrees(g_selectedShape->rotation.x),
        XMConvertToDegrees(g_selectedShape->rotation.y),
        XMConvertToDegrees(g_selectedShape->rotation.z),
        g_selectedShape->scale.x, g_selectedShape->scale.y, g_selectedShape->scale.z);

    MessageBox(hWnd, message, L"实体属性", MB_OK | MB_ICONINFORMATION);
}

// 实体属性对话框过程
INT_PTR CALLBACK ShapePropertiesDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[64];
    static HWND hEdits[9];

    switch (message)
    {
    case WM_INITDIALOG:
    {
        if (!g_selectedShape)
        {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }

        // 创建标签和编辑框
        int y = 10;
        const wchar_t* labels[] = { L"位置 X:", L"Y:", L"Z:", L"旋转 X°:", L"Y°:", L"Z°:", L"缩放 X:", L"Y:", L"Z:" };
        float values[] = {
            g_selectedShape->position.x, g_selectedShape->position.y, g_selectedShape->position.z,
            XMConvertToDegrees(g_selectedShape->rotation.x),
            XMConvertToDegrees(g_selectedShape->rotation.y),
            XMConvertToDegrees(g_selectedShape->rotation.z),
            g_selectedShape->scale.x, g_selectedShape->scale.y, g_selectedShape->scale.z };

        for (int i = 0; i < 9; i++)
        {
            CreateWindow(L"STATIC", labels[i], WS_CHILD | WS_VISIBLE,
                10, y, 70, 20, hDlg, nullptr, nullptr, nullptr);
            hEdits[i] = CreateWindow(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                90, y, 170, 20, hDlg, (HMENU)(IDC_EDIT_POS_X + i), nullptr, nullptr);
            swprintf_s(buffer, L"%.2f", values[i]);
            SetWindowText(hEdits[i], buffer);
            y += 22;
        }

        // 创建按钮
        CreateWindow(L"BUTTON", L"确定", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON,
            90, y + 5, 80, 25, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindow(L"BUTTON", L"取消", WS_CHILD | WS_VISIBLE,
            180, y + 5, 80, 25, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);

        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK)
        {
            if (!g_selectedShape)
            {
                EndDialog(hDlg, IDCANCEL);
                return TRUE;
            }

            // 读取位置
            GetWindowText(hEdits[0], buffer, 64);
            g_selectedShape->position.x = (float)_wtof(buffer);
            GetWindowText(hEdits[1], buffer, 64);
            g_selectedShape->position.y = (float)_wtof(buffer);
            GetWindowText(hEdits[2], buffer, 64);
            g_selectedShape->position.z = (float)_wtof(buffer);

            // 读取旋转（转换为弧度）
            GetWindowText(hEdits[3], buffer, 64);
            g_selectedShape->rotation.x = XMConvertToRadians((float)_wtof(buffer));
            GetWindowText(hEdits[4], buffer, 64);
            g_selectedShape->rotation.y = XMConvertToRadians((float)_wtof(buffer));
            GetWindowText(hEdits[5], buffer, 64);
            g_selectedShape->rotation.z = XMConvertToRadians((float)_wtof(buffer));

            // 读取缩放
            GetWindowText(hEdits[6], buffer, 64);
            g_selectedShape->scale.x = (float)_wtof(buffer);
            GetWindowText(hEdits[7], buffer, 64);
            g_selectedShape->scale.y = (float)_wtof(buffer);
            GetWindowText(hEdits[8], buffer, 64);
            g_selectedShape->scale.z = (float)_wtof(buffer);

            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}

// 光照设置对话框过程
INT_PTR CALLBACK LightSettingsDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[64];
    static HWND hEdits[6];

    switch (message)
    {
    case WM_INITDIALOG:
    {
        // 创建标签和编辑框
        int y = 10;
        const wchar_t* labels[] = { L"光源方向 X:", L"Y:", L"Z:", L"光源颜色 R:", L"G:", L"B:" };
        float values[] = {
            g_lightDirection.x, g_lightDirection.y, g_lightDirection.z,
            g_lightColor.x, g_lightColor.y, g_lightColor.z };

        for (int i = 0; i < 6; i++)
        {
            CreateWindow(L"STATIC", labels[i], WS_CHILD | WS_VISIBLE,
                10, y, 100, 20, hDlg, nullptr, nullptr, nullptr);
            hEdits[i] = CreateWindow(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                120, y, 140, 20, hDlg, (HMENU)(IDC_EDIT_LIGHT_X + i), nullptr, nullptr);
            swprintf_s(buffer, L"%.2f", values[i]);
            SetWindowText(hEdits[i], buffer);
            y += 22;
        }

        // 创建按钮
        CreateWindow(L"BUTTON", L"确定", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON,
            90, y + 5, 80, 25, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindow(L"BUTTON", L"取消", WS_CHILD | WS_VISIBLE,
            180, y + 5, 80, 25, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);

        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK)
        {
            // 读取光源方向
            GetWindowText(hEdits[0], buffer, 64);
            g_lightDirection.x = (float)_wtof(buffer);
            GetWindowText(hEdits[1], buffer, 64);
            g_lightDirection.y = (float)_wtof(buffer);
            GetWindowText(hEdits[2], buffer, 64);
            g_lightDirection.z = (float)_wtof(buffer);

            // 归一化光源方向
            XMVECTOR lightDir = XMLoadFloat3(&g_lightDirection);
            lightDir = XMVector3Normalize(lightDir);
            XMStoreFloat3(&g_lightDirection, lightDir);

            // 读取光源颜色
            GetWindowText(hEdits[3], buffer, 64);
            g_lightColor.x = (float)_wtof(buffer);
            GetWindowText(hEdits[4], buffer, 64);
            g_lightColor.y = (float)_wtof(buffer);
            GetWindowText(hEdits[5], buffer, 64);
            g_lightColor.z = (float)_wtof(buffer);

            // 限制颜色值范围
            g_lightColor.x = max(0.0f, min(2.0f, g_lightColor.x));
            g_lightColor.y = max(0.0f, min(2.0f, g_lightColor.y));
            g_lightColor.z = max(0.0f, min(2.0f, g_lightColor.z));

            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}

// 创建实体属性对话框模板
DLGTEMPLATE* CreateShapePropertiesDialogTemplate()
{
    static BYTE dlgTemplate[1024];
    memset(dlgTemplate, 0, sizeof(dlgTemplate));
    LPDLGTEMPLATE lpdt = (LPDLGTEMPLATE)dlgTemplate;
    LPWORD lpw;

    lpdt->style = WS_POPUP | WS_BORDER | WS_SYSMENU | DS_MODALFRAME | WS_CAPTION;
    lpdt->cdit = 0; // 控件在对话框过程中动态创建
    lpdt->x = 10;
    lpdt->y = 10;
    lpdt->cx = 280;
    lpdt->cy = 240;

    lpw = (LPWORD)(lpdt + 1);
    *lpw++ = 0; // 无菜单
    *lpw++ = 0; // 默认对话框类

    // 对话框标题
    wcscpy_s((wchar_t*)lpw, 50, L"实体属性");
    lpw += wcslen((wchar_t*)lpw) + 1;

    return lpdt;
}

// 创建光照设置对话框模板
DLGTEMPLATE* CreateLightSettingsDialogTemplate()
{
    static BYTE dlgTemplate[1024];
    memset(dlgTemplate, 0, sizeof(dlgTemplate));
    LPDLGTEMPLATE lpdt = (LPDLGTEMPLATE)dlgTemplate;
    LPWORD lpw;

    lpdt->style = WS_POPUP | WS_BORDER | WS_SYSMENU | DS_MODALFRAME | WS_CAPTION;
    lpdt->cdit = 0; // 控件在对话框过程中动态创建
    lpdt->x = 10;
    lpdt->y = 10;
    lpdt->cx = 280;
    lpdt->cy = 180;

    lpw = (LPWORD)(lpdt + 1);
    *lpw++ = 0; // 无菜单
    *lpw++ = 0; // 默认对话框类

    // 对话框标题
    wcscpy_s((wchar_t*)lpw, 50, L"光照设置");
    lpw += wcslen((wchar_t*)lpw) + 1;

    return lpdt;
}

// 材质设置对话框过程
INT_PTR CALLBACK MaterialSettingsDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[64];
    static HWND hEdits[11];

    switch (message)
    {
    case WM_INITDIALOG:
    {
        if (!g_selectedShape)
        {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }

        // 创建标签和编辑框
        int y = 10;
        const wchar_t* labels[] = { L"环境光 R:", L"G:", L"B:",
                                   L"漫反射 R:", L"G:", L"B:",
                                   L"镜面反射 R:", L"G:", L"B:",
                                   L"光泽度:", L"" };
        float values[] = {
            g_selectedShape->material.ambient.x,
            g_selectedShape->material.ambient.y,
            g_selectedShape->material.ambient.z,
            g_selectedShape->material.diffuse.x,
            g_selectedShape->material.diffuse.y,
            g_selectedShape->material.diffuse.z,
            g_selectedShape->material.specular.x,
            g_selectedShape->material.specular.y,
            g_selectedShape->material.specular.z,
            g_selectedShape->material.shininess,
            0.0f };

        for (int i = 0; i < 10; i++)
        {
            CreateWindow(L"STATIC", labels[i], WS_CHILD | WS_VISIBLE,
                10, y, 100, 20, hDlg, nullptr, nullptr, nullptr);
            hEdits[i] = CreateWindow(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                120, y, 140, 20, hDlg, (HMENU)(IDC_EDIT_AMBIENT_R + i), nullptr, nullptr);
            swprintf_s(buffer, L"%.2f", values[i]);
            SetWindowText(hEdits[i], buffer);
            y += 22;
        }

        // 创建按钮
        CreateWindow(L"BUTTON", L"确定", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON,
            90, y + 5, 80, 25, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindow(L"BUTTON", L"取消", WS_CHILD | WS_VISIBLE,
            180, y + 5, 80, 25, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);

        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK)
        {
            if (!g_selectedShape)
            {
                EndDialog(hDlg, IDCANCEL);
                return TRUE;
            }

            // 读取环境光
            GetWindowText(hEdits[0], buffer, 64);
            g_selectedShape->material.ambient.x = (float)_wtof(buffer);
            GetWindowText(hEdits[1], buffer, 64);
            g_selectedShape->material.ambient.y = (float)_wtof(buffer);
            GetWindowText(hEdits[2], buffer, 64);
            g_selectedShape->material.ambient.z = (float)_wtof(buffer);

            // 读取漫反射
            GetWindowText(hEdits[3], buffer, 64);
            g_selectedShape->material.diffuse.x = (float)_wtof(buffer);
            GetWindowText(hEdits[4], buffer, 64);
            g_selectedShape->material.diffuse.y = (float)_wtof(buffer);
            GetWindowText(hEdits[5], buffer, 64);
            g_selectedShape->material.diffuse.z = (float)_wtof(buffer);

            // 读取镜面反射
            GetWindowText(hEdits[6], buffer, 64);
            g_selectedShape->material.specular.x = (float)_wtof(buffer);
            GetWindowText(hEdits[7], buffer, 64);
            g_selectedShape->material.specular.y = (float)_wtof(buffer);
            GetWindowText(hEdits[8], buffer, 64);
            g_selectedShape->material.specular.z = (float)_wtof(buffer);

            // 读取光泽度
            GetWindowText(hEdits[9], buffer, 64);
            g_selectedShape->material.shininess = (float)_wtof(buffer);

            // 限制范围
            g_selectedShape->material.ambient.x = max(0.0f, min(1.0f, g_selectedShape->material.ambient.x));
            g_selectedShape->material.ambient.y = max(0.0f, min(1.0f, g_selectedShape->material.ambient.y));
            g_selectedShape->material.ambient.z = max(0.0f, min(1.0f, g_selectedShape->material.ambient.z));
            g_selectedShape->material.diffuse.x = max(0.0f, min(1.0f, g_selectedShape->material.diffuse.x));
            g_selectedShape->material.diffuse.y = max(0.0f, min(1.0f, g_selectedShape->material.diffuse.y));
            g_selectedShape->material.diffuse.z = max(0.0f, min(1.0f, g_selectedShape->material.diffuse.z));
            g_selectedShape->material.specular.x = max(0.0f, min(1.0f, g_selectedShape->material.specular.x));
            g_selectedShape->material.specular.y = max(0.0f, min(1.0f, g_selectedShape->material.specular.y));
            g_selectedShape->material.specular.z = max(0.0f, min(1.0f, g_selectedShape->material.specular.z));
            g_selectedShape->material.shininess = max(1.0f, min(128.0f, g_selectedShape->material.shininess));

            // 更新顶点缓冲区使材质生效
            UpdateShapeVertexColor(g_selectedShape);

            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}

// 纹理设置对话框过程
INT_PTR CALLBACK TextureSettingsDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[MAX_PATH];
    static HWND hEditPath = nullptr;
    static HWND hComboMode = nullptr;

    switch (message)
    {
    case WM_INITDIALOG:
    {
        if (!g_selectedShape)
        {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }

        // 创建纹理路径标签和编辑框
        CreateWindow(L"STATIC", L"纹理文件路径:", WS_CHILD | WS_VISIBLE,
            10, 10, 100, 20, hDlg, nullptr, nullptr, nullptr);
        hEditPath = CreateWindow(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
            10, 35, 250, 20, hDlg, (HMENU)IDC_EDIT_TEXTURE_PATH, nullptr, nullptr);
        SetWindowText(hEditPath, g_selectedShape->texturePath.c_str());

        // 浏览按钮
        CreateWindow(L"BUTTON", L"浏览...", WS_CHILD | WS_VISIBLE,
            10, 65, 80, 25, hDlg, (HMENU)IDC_BUTTON_BROWSE, nullptr, nullptr);

        // 映射方式标签和下拉框
        CreateWindow(L"STATIC", L"映射方式:", WS_CHILD | WS_VISIBLE,
            10, 105, 100, 20, hDlg, nullptr, nullptr, nullptr);
        hComboMode = CreateWindow(L"COMBOBOX", L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST,
            10, 130, 250, 80, hDlg, (HMENU)IDC_COMBO_TEXTURE_MODE, nullptr, nullptr);

        // 添加选项
        SendMessage(hComboMode, CB_ADDSTRING, 0, (LPARAM)L"无纹理");
        SendMessage(hComboMode, CB_ADDSTRING, 0, (LPARAM)L"颜色混合");
        SendMessage(hComboMode, CB_ADDSTRING, 0, (LPARAM)L"纹理替换");
        SendMessage(hComboMode, CB_SETCURSEL, g_selectedShape->textureMode, 0);

        // 创建按钮
        CreateWindow(L"BUTTON", L"确定", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON,
            90, 170, 80, 25, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindow(L"BUTTON", L"取消", WS_CHILD | WS_VISIBLE,
            180, 170, 80, 25, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);

        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDC_BUTTON_BROWSE)
        {
            // 简单的文件路径输入（实际应用中应使用文件对话框）
            OPENFILENAME ofn = {};
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hDlg;
            ofn.lpstrFilter = L"图片文件\0*.bmp;*.png;*.jpg;*.tga\0所有文件\0*.*\0";
            ofn.lpstrFile = buffer;
            ofn.nMaxFile = MAX_PATH;
            ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;

            if (GetOpenFileName(&ofn))
            {
                SetWindowText(hEditPath, buffer);
            }
            return TRUE;
        }
        else if (LOWORD(wParam) == IDOK)
        {
            if (!g_selectedShape)
            {
                EndDialog(hDlg, IDCANCEL);
                return TRUE;
            }

            // 读取纹理路径
            GetWindowText(hEditPath, buffer, MAX_PATH);
            std::wstring newPath = buffer;

            // 读取映射方式
            int modeIndex = (int)SendMessage(hComboMode, CB_GETCURSEL, 0, 0);

            // 如果路径发生变化或从无纹理变为有纹理，重新加载
            bool needReload = (newPath != g_selectedShape->texturePath) ||
                (modeIndex > 0 && g_selectedShape->textureView == nullptr);

            // 释放旧纹理
            if (needReload && g_selectedShape->textureView)
            {
                g_selectedShape->textureView->Release();
                g_selectedShape->textureView = nullptr;
            }

            // 加载新纹理
            if (needReload && modeIndex > 0 && !newPath.empty())
            {
                if (!LoadTextureFromFile(newPath.c_str(), &g_selectedShape->textureView))
                {
                    MessageBox(hDlg, L"无法加载纹理文件！\n目前仅支持24位或32位BMP格式。", L"错误", MB_OK | MB_ICONERROR);
                    g_selectedShape->textureMode = 0;
                    EndDialog(hDlg, IDCANCEL);
                    return TRUE;
                }
            }

            // 如果选择无纹理，释放纹理资源
            if (modeIndex == 0 && g_selectedShape->textureView)
            {
                g_selectedShape->textureView->Release();
                g_selectedShape->textureView = nullptr;
            }

            g_selectedShape->texturePath = newPath;
            g_selectedShape->textureMode = modeIndex;

            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL)
        {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}
