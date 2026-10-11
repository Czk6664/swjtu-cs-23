#pragma once
#include <windows.h>
#include <d3d11.h>
#include <DirectXMath.h>
#include <string>

using namespace DirectX;

// Constants
const int WINDOW_WIDTH = 1024;
const int WINDOW_HEIGHT = 768;
const float CAMERA_DISTANCE = 10.0f;
const float AXIS_LENGTH = 10.0f;

// Vertex structure
struct Vertex
{
    XMFLOAT3 position;
    XMFLOAT3 normal;
    XMFLOAT4 color;
    XMFLOAT2 texCoord;
};

// Constant buffer structure
struct ConstantBuffer
{
    XMMATRIX world;
    XMMATRIX view;
    XMMATRIX projection;
    XMFLOAT4 lightDir;
    XMFLOAT4 lightColor;
    XMFLOAT4 cameraPos;
    XMFLOAT4 matAmbient;
    XMFLOAT4 matDiffuse;
    XMFLOAT4 matSpecular;
    XMFLOAT4 matEmissive;  // 新增：自发光
    XMFLOAT4 textureInfo;
    XMFLOAT4 materialExtra;  // 新增：transparency, reflectivity等
};

// Shape type enum
enum ShapeType
{
    SHAPE_SPHERE,
    SHAPE_CYLINDER,
    SHAPE_CONE,
    SHAPE_PLANE,
    SHAPE_CUBE,
    SHAPE_TETRAHEDRON
};

// Material structure
struct Material
{
    XMFLOAT3 ambient;
    XMFLOAT3 diffuse;
    XMFLOAT3 specular;
    XMFLOAT3 emissive;  // 自发光
    float shininess;
    float transparency;  // 透明度 (0=完全透明, 1=完全不透明)
    float reflectivity;  // 反射率

    Material() : ambient(0.3f, 0.3f, 0.3f), diffuse(1.0f, 1.0f, 1.0f),
        specular(1.0f, 1.0f, 1.0f), emissive(0.0f, 0.0f, 0.0f),
        shininess(32.0f), transparency(1.0f), reflectivity(0.0f) {}
};

// Preset style enum
enum PresetStyle
{
    STYLE_NONE = 0,
    STYLE_METAL,
    STYLE_PLASTIC,
    STYLE_GLASS,
    STYLE_RUBBER,
    STYLE_GOLD,
    STYLE_SILVER,
    STYLE_COPPER,
    STYLE_CHROME,
    STYLE_JADE,
    STYLE_EMERALD,
    STYLE_PEARL
};

// 3D Shape class
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
    PresetStyle presetStyle;

    Material material;
    std::wstring texturePath;
    ID3D11ShaderResourceView* textureView;
    int textureMode;

    Shape3D() : 
        type(SHAPE_SPHERE),
        position(0, 0, 0),
        rotation(0, 0, 0),
        scale(1, 1, 1),
        color(0.7f, 0.7f, 0.7f, 1.0f),
        vertexBuffer(nullptr),
        indexBuffer(nullptr),
        indexCount(0),
        selected(false),
        presetStyle(STYLE_NONE),
        textureView(nullptr),
        textureMode(0)
    {
        material = Material();
        material.diffuse = XMFLOAT3(0.7f, 0.7f, 0.7f);
        texturePath = L"";
    }

    ~Shape3D()
    {
        if (vertexBuffer) vertexBuffer->Release();
        if (indexBuffer) indexBuffer->Release();
        if (textureView) textureView->Release();
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

    void ApplyPresetStyle(PresetStyle style)
    {
        presetStyle = style;
        switch (style)
        {
        case STYLE_NONE:
            color = XMFLOAT4(0.7f, 0.7f, 0.7f, 1.0f);
            material.ambient = XMFLOAT3(0.2f, 0.2f, 0.2f);
            material.diffuse = XMFLOAT3(0.7f, 0.7f, 0.7f);
            material.specular = XMFLOAT3(0.3f, 0.3f, 0.3f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 16.0f;
            material.transparency = 1.0f;
            material.reflectivity = 0.0f;
            break;
        case STYLE_METAL:
            color = XMFLOAT4(0.8f, 0.7f, 0.5f, 1.0f);
            material.ambient = XMFLOAT3(0.25f, 0.22f, 0.16f);
            material.diffuse = XMFLOAT3(0.8f, 0.7f, 0.5f);
            material.specular = XMFLOAT3(1.0f, 0.95f, 0.8f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 64.0f;
            material.transparency = 1.0f;
            material.reflectivity = 0.5f;
            break;
        case STYLE_PLASTIC:
            color = XMFLOAT4(0.3f, 0.6f, 0.9f, 1.0f);
            material.ambient = XMFLOAT3(0.1f, 0.2f, 0.3f);
            material.diffuse = XMFLOAT3(0.3f, 0.6f, 0.9f);
            material.specular = XMFLOAT3(0.5f, 0.5f, 0.5f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 32.0f;
            material.transparency = 1.0f;
            material.reflectivity = 0.1f;
            break;
        case STYLE_GLASS:
            color = XMFLOAT4(0.9f, 0.95f, 1.0f, 0.3f);
            material.ambient = XMFLOAT3(0.1f, 0.1f, 0.1f);
            material.diffuse = XMFLOAT3(0.6f, 0.7f, 0.8f);
            material.specular = XMFLOAT3(1.0f, 1.0f, 1.0f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 96.0f;
            material.transparency = 0.3f;
            material.reflectivity = 0.8f;
            break;
        case STYLE_RUBBER:
            color = XMFLOAT4(0.2f, 0.2f, 0.2f, 1.0f);
            material.ambient = XMFLOAT3(0.05f, 0.05f, 0.05f);
            material.diffuse = XMFLOAT3(0.5f, 0.5f, 0.5f);
            material.specular = XMFLOAT3(0.1f, 0.1f, 0.1f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 8.0f;
            material.transparency = 1.0f;
            material.reflectivity = 0.0f;
            break;
        case STYLE_GOLD:
            color = XMFLOAT4(1.0f, 0.84f, 0.0f, 1.0f);
            material.ambient = XMFLOAT3(0.24725f, 0.1995f, 0.0745f);
            material.diffuse = XMFLOAT3(0.75164f, 0.60648f, 0.22648f);
            material.specular = XMFLOAT3(0.628281f, 0.555802f, 0.366065f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 51.2f;
            material.transparency = 1.0f;
            material.reflectivity = 0.7f;
            break;
        case STYLE_SILVER:
            color = XMFLOAT4(0.75f, 0.75f, 0.75f, 1.0f);
            material.ambient = XMFLOAT3(0.19225f, 0.19225f, 0.19225f);
            material.diffuse = XMFLOAT3(0.50754f, 0.50754f, 0.50754f);
            material.specular = XMFLOAT3(0.508273f, 0.508273f, 0.508273f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 51.2f;
            material.transparency = 1.0f;
            material.reflectivity = 0.8f;
            break;
        case STYLE_COPPER:
            color = XMFLOAT4(0.72f, 0.45f, 0.20f, 1.0f);
            material.ambient = XMFLOAT3(0.19125f, 0.0735f, 0.0225f);
            material.diffuse = XMFLOAT3(0.7038f, 0.27048f, 0.0828f);
            material.specular = XMFLOAT3(0.256777f, 0.137622f, 0.086014f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 12.8f;
            material.transparency = 1.0f;
            material.reflectivity = 0.6f;
            break;
        case STYLE_CHROME:
            color = XMFLOAT4(0.9f, 0.9f, 0.9f, 1.0f);
            material.ambient = XMFLOAT3(0.25f, 0.25f, 0.25f);
            material.diffuse = XMFLOAT3(0.4f, 0.4f, 0.4f);
            material.specular = XMFLOAT3(0.774597f, 0.774597f, 0.774597f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 76.8f;
            material.transparency = 1.0f;
            material.reflectivity = 0.9f;
            break;
        case STYLE_JADE:
            color = XMFLOAT4(0.54f, 0.89f, 0.63f, 0.95f);
            material.ambient = XMFLOAT3(0.135f, 0.2225f, 0.1575f);
            material.diffuse = XMFLOAT3(0.54f, 0.89f, 0.63f);
            material.specular = XMFLOAT3(0.316228f, 0.316228f, 0.316228f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 12.8f;
            material.transparency = 0.95f;
            material.reflectivity = 0.3f;
            break;
        case STYLE_EMERALD:
            color = XMFLOAT4(0.07f, 0.61f, 0.48f, 0.55f);
            material.ambient = XMFLOAT3(0.0215f, 0.1745f, 0.0215f);
            material.diffuse = XMFLOAT3(0.07568f, 0.61424f, 0.07568f);
            material.specular = XMFLOAT3(0.633f, 0.727811f, 0.633f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 76.8f;
            material.transparency = 0.55f;
            material.reflectivity = 0.6f;
            break;
        case STYLE_PEARL:
            color = XMFLOAT4(1.0f, 0.93f, 0.86f, 1.0f);
            material.ambient = XMFLOAT3(0.25f, 0.20725f, 0.20725f);
            material.diffuse = XMFLOAT3(1.0f, 0.829f, 0.829f);
            material.specular = XMFLOAT3(0.296648f, 0.296648f, 0.296648f);
            material.emissive = XMFLOAT3(0.0f, 0.0f, 0.0f);
            material.shininess = 11.264f;
            material.transparency = 1.0f;
            material.reflectivity = 0.4f;
            break;
        }
    }
};

#define SAFE_RELEASE(p) { if (p) { (p)->Release(); (p) = nullptr; } }
