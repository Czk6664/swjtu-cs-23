#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objbase.h>
#include <wincodec.h>
#include "Geometry.h"
#include "Globals.h"
#include <cmath>
#include <new>
#include <vector>

#pragma comment(lib, "windowscodecs.lib")
#pragma comment(lib, "ole32.lib")

// 辅助函数声明
void GetCameraViewMatrix(XMMATRIX& outView, XMVECTOR& outEye);

// 更新形状的顶点缓冲区颜色
bool UpdateShapeVertexColor(Shape3D* shape)
{
    if (!shape || !g_pd3dDevice)
        return false;

    std::vector<Vertex> vertices;
    std::vector<UINT> indices;

    switch (shape->type)
    {
    case SHAPE_SPHERE:
        CreateSphere(1.0f, 32, 16, vertices, indices);
        break;
    case SHAPE_CYLINDER:
        CreateCylinder(0.5f, 2.0f, 32, vertices, indices);
        break;
    case SHAPE_PLANE:
        CreatePlane(10.0f, 10.0f, vertices, indices);
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

    XMFLOAT4 baseColor = shape->color;
    for (auto& v : vertices)
    {
        v.color = baseColor;
    }

    if (shape->vertexBuffer)
    {
        shape->vertexBuffer->Release();
        shape->vertexBuffer = nullptr;
    }

    D3D11_BUFFER_DESC bd = {};
    bd.Usage = D3D11_USAGE_DEFAULT;
    bd.ByteWidth = sizeof(Vertex) * (UINT)vertices.size();
    bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;

    D3D11_SUBRESOURCE_DATA initData = {};
    initData.pSysMem = vertices.data();

    HRESULT hr = g_pd3dDevice->CreateBuffer(&bd, &initData, &shape->vertexBuffer);
    return SUCCEEDED(hr);
}

// 使用WIC加载图片（支持PNG, JPG, BMP, GIF, TIFF等）
bool LoadTextureFromFile(const wchar_t* filename, ID3D11ShaderResourceView** textureView)
{
    if (!g_pd3dDevice || !filename || !textureView)
        return false;

    *textureView = nullptr;

    // 初始化COM
    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    bool comInitialized = SUCCEEDED(hr) || hr == S_FALSE;

    // 创建WIC工厂
    IWICImagingFactory* pFactory = nullptr;
    hr = CoCreateInstance(
        CLSID_WICImagingFactory,
        nullptr,
        CLSCTX_INPROC_SERVER,
        __uuidof(IWICImagingFactory),
        (void**)&pFactory
    );
    if (FAILED(hr) || !pFactory)
    {
        if (comInitialized) CoUninitialize();
        return false;
    }

    // 创建解码器
    IWICBitmapDecoder* pDecoder = nullptr;
    hr = pFactory->CreateDecoderFromFilename(
        filename,
        nullptr,
        GENERIC_READ,
        WICDecodeMetadataCacheOnLoad,
        &pDecoder
    );
    if (FAILED(hr) || !pDecoder)
    {
        pFactory->Release();
        if (comInitialized) CoUninitialize();
        return false;
    }

    // 获取第一帧
    IWICBitmapFrameDecode* pFrame = nullptr;
    hr = pDecoder->GetFrame(0, &pFrame);
    if (FAILED(hr) || !pFrame)
    {
        pDecoder->Release();
        pFactory->Release();
        if (comInitialized) CoUninitialize();
        return false;
    }

    // 获取尺寸
    UINT width, height;
    pFrame->GetSize(&width, &height);

    // 创建格式转换器
    IWICFormatConverter* pConverter = nullptr;
    hr = pFactory->CreateFormatConverter(&pConverter);
    if (FAILED(hr) || !pConverter)
    {
        pFrame->Release();
        pDecoder->Release();
        pFactory->Release();
        if (comInitialized) CoUninitialize();
        return false;
    }

    // 转换为32位RGBA
    hr = pConverter->Initialize(
        pFrame,
        GUID_WICPixelFormat32bppRGBA,
        WICBitmapDitherTypeNone,
        nullptr,
        0.0,
        WICBitmapPaletteTypeCustom
    );
    if (FAILED(hr))
    {
        pConverter->Release();
        pFrame->Release();
        pDecoder->Release();
        pFactory->Release();
        if (comInitialized) CoUninitialize();
        return false;
    }

    // 读取像素数据
    UINT stride = width * 4;
    UINT imageSize = stride * height;
    std::vector<BYTE> imageData(imageSize);
    hr = pConverter->CopyPixels(nullptr, stride, imageSize, imageData.data());

    // 释放WIC资源
    pConverter->Release();
    pFrame->Release();
    pDecoder->Release();
    pFactory->Release();

    if (FAILED(hr))
    {
        if (comInitialized) CoUninitialize();
        return false;
    }

    // 创建D3D11纹理
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
    initData.pSysMem = imageData.data();
    initData.SysMemPitch = stride;

    ID3D11Texture2D* pTexture = nullptr;
    hr = g_pd3dDevice->CreateTexture2D(&texDesc, &initData, &pTexture);
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
    if (!g_pd3dDevice)
        return nullptr;

    Shape3D* shape = new (std::nothrow) Shape3D();
    if (!shape)
        return nullptr;

    shape->type = type;

    std::vector<Vertex> vertices;
    std::vector<UINT> indices;

    switch (type)
    {
    case SHAPE_SPHERE:
        CreateSphere(1.0f, 32, 16, vertices, indices);
        break;
    case SHAPE_CYLINDER:
        CreateCylinder(0.5f, 2.0f, 32, vertices, indices);
        break;
    case SHAPE_PLANE:
        CreatePlane(0.5f, 0.5f, vertices, indices);
        break;
    case SHAPE_CUBE:
        CreateCube(1.5f, vertices, indices);
        break;
    case SHAPE_TETRAHEDRON:
        CreateTetrahedron(1.5f, vertices, indices);
        break;
    }

    // 默认无颜色（灰色）
    shape->ApplyPresetStyle(STYLE_NONE);

    for (auto& v : vertices)
    {
        v.color = shape->color;
    }

    D3D11_BUFFER_DESC bd = {};
    bd.Usage = D3D11_USAGE_DEFAULT;
    bd.ByteWidth = sizeof(Vertex) * (UINT)vertices.size();
    bd.BindFlags = D3D11_BIND_VERTEX_BUFFER;

    D3D11_SUBRESOURCE_DATA initData = {};
    initData.pSysMem = vertices.data();

    HRESULT hr = g_pd3dDevice->CreateBuffer(&bd, &initData, &shape->vertexBuffer);
    if (FAILED(hr))
    {
        delete shape;
        return nullptr;
    }

    bd.ByteWidth = sizeof(UINT) * (UINT)indices.size();
    bd.BindFlags = D3D11_BIND_INDEX_BUFFER;
    initData.pSysMem = indices.data();

    hr = g_pd3dDevice->CreateBuffer(&bd, &initData, &shape->indexBuffer);
    if (FAILED(hr))
    {
        delete shape;
        return nullptr;
    }

    shape->indexCount = (UINT)indices.size();

    static int shapeCount = 0;
    float angle = shapeCount * XM_PI * 0.4f;
    shape->position = XMFLOAT3(3.0f * cosf(angle), 0, 3.0f * sinf(angle));
    shapeCount++;

    return shape;
}

// 拾取形状
Shape3D* PickShape(int x, int y)
{
    float ndcX = (2.0f * x / WINDOW_WIDTH) - 1.0f;
    float ndcY = 1.0f - (2.0f * y / WINDOW_HEIGHT);

    XMMATRIX projection = XMMatrixPerspectiveFovLH(XM_PIDIV4,
        (float)WINDOW_WIDTH / (float)WINDOW_HEIGHT, 0.01f, 100.0f);
    XMMATRIX invProj = XMMatrixInverse(nullptr, projection);

    XMVECTOR rayDir = XMVectorSet(ndcX, ndcY, 1.0f, 0.0f);
    rayDir = XMVector3TransformCoord(rayDir, invProj);

    XMVECTOR Eye;
    XMMATRIX view;
    GetCameraViewMatrix(view, Eye);
    XMMATRIX invView = XMMatrixInverse(nullptr, view);

    XMVECTOR rayOrigin = Eye;
    rayDir = XMVector3TransformNormal(rayDir, invView);
    rayDir = XMVector3Normalize(rayDir);

    Shape3D* closest = nullptr;
    float minDist = FLT_MAX;

    for (auto shape : g_shapes)
    {
        XMMATRIX worldMatrix = shape->GetWorldMatrix();
        XMMATRIX invWorld = XMMatrixInverse(nullptr, worldMatrix);

        XMVECTOR localRayOrigin = XMVector3TransformCoord(rayOrigin, invWorld);
        XMVECTOR localRayDir = XMVector3TransformNormal(rayDir, invWorld);
        localRayDir = XMVector3Normalize(localRayDir);

        float boundRadius = 1.0f;
        switch (shape->type)
        {
        case SHAPE_SPHERE: boundRadius = 1.0f; break;
        case SHAPE_CUBE: boundRadius = 0.87f; break;
        case SHAPE_CYLINDER: boundRadius = 1.12f; break;
        case SHAPE_CONE: boundRadius = 1.12f; break;
        case SHAPE_TETRAHEDRON: boundRadius = 0.87f; break;
        case SHAPE_PLANE: boundRadius = 10.0f; break;
        }

        XMVECTOR toCenter = XMVectorNegate(localRayOrigin);
        float projLen = XMVectorGetX(XMVector3Dot(toCenter, localRayDir));

        if (projLen > 0)
        {
            XMVECTOR closestPoint = XMVectorAdd(localRayOrigin, XMVectorScale(localRayDir, projLen));
            float dist = XMVectorGetX(XMVector3Length(closestPoint));

            if (dist < boundRadius)
            {
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
