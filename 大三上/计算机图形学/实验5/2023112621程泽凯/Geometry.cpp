#include "Geometry.h"
#include "Globals.h"
#include <cmath>
#include <new>

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

            v.color = XMFLOAT4(0.7f, 0.7f, 0.7f, 1.0f);
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
    XMFLOAT4 defaultColor(0.7f, 0.7f, 0.7f, 1.0f);

    Vertex topCenter;
    topCenter.position = XMFLOAT3(0, halfHeight, 0);
    topCenter.normal = XMFLOAT3(0, 1, 0);
    topCenter.color = defaultColor;
    topCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(topCenter);

    Vertex bottomCenter;
    bottomCenter.position = XMFLOAT3(0, -halfHeight, 0);
    bottomCenter.normal = XMFLOAT3(0, -1, 0);
    bottomCenter.color = defaultColor;
    bottomCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(bottomCenter);

    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = halfHeight;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(cosf(theta), 0, sinf(theta));
        v.color = defaultColor;
        v.texCoord = XMFLOAT2((float)i / slices, 0.0f);
        vertices.push_back(v);
    }

    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = -halfHeight;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(cosf(theta), 0, sinf(theta));
        v.color = defaultColor;
        v.texCoord = XMFLOAT2((float)i / slices, 1.0f);
        vertices.push_back(v);
    }

    // 顶面索引 - 从上往下看逆时针（外面看）
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(0);
        indices.push_back(2 + i + 1);
        indices.push_back(2 + i);
    }

    // 底面索引 - 从下往上看逆时针（外面看）
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(1);
        indices.push_back(2 + slices + 1 + i);
        indices.push_back(2 + slices + 1 + i + 1);
    }

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

// 创建圆锥体
void CreateCone(float radius, float height, int slices, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    XMFLOAT4 defaultColor(0.7f, 0.7f, 0.7f, 1.0f);

    // 顶点（圆锥尖端）
    Vertex apex;
    apex.position = XMFLOAT3(0, height, 0);
    apex.normal = XMFLOAT3(0, 1, 0);
    apex.color = defaultColor;
    apex.texCoord = XMFLOAT2(0.5f, 0.0f);
    vertices.push_back(apex);

    // 底部圆心
    Vertex bottomCenter;
    bottomCenter.position = XMFLOAT3(0, 0, 0);
    bottomCenter.normal = XMFLOAT3(0, -1, 0);
    bottomCenter.color = defaultColor;
    bottomCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(bottomCenter);

    // 侧面斜率用于计算法线
    float slopeAngle = atanf(radius / height);
    float ny = sinf(slopeAngle);
    float nxz = cosf(slopeAngle);

    // 底部圆周顶点（用于侧面）
    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = 0;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(nxz * cosf(theta), ny, nxz * sinf(theta));
        v.color = defaultColor;
        v.texCoord = XMFLOAT2((float)i / slices, 1.0f);
        vertices.push_back(v);
    }

    // 侧面索引
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(0);  // apex
        indices.push_back(2 + i);
        indices.push_back(2 + i + 1);
    }

    // 底面索引
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(1);  // bottom center
        indices.push_back(2 + i + 1);
        indices.push_back(2 + i);
    }
}

// 创建平面
void CreatePlane(float width, float height, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    float halfW = width * 10.0f;
    float halfH = height * 10.0f;
    XMFLOAT4 planeColor = XMFLOAT4(0.7f, 0.7f, 0.7f, 0.7f);

    Vertex v;
    v.normal = XMFLOAT3(0, 1, 0);
    v.color = planeColor;

    v.position = XMFLOAT3(-halfW, 0, -halfH);
    v.texCoord = XMFLOAT2(0.0f, 0.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(-halfW, 0, halfH);
    v.texCoord = XMFLOAT2(0.0f, 10.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(halfW, 0, halfH);
    v.texCoord = XMFLOAT2(10.0f, 10.0f);
    vertices.push_back(v);
    v.position = XMFLOAT3(halfW, 0, -halfH);
    v.texCoord = XMFLOAT2(10.0f, 0.0f);
    vertices.push_back(v);

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

    indices = { 0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7 };
}

// 创建立方体
void CreateCube(float size, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    float half = size * 0.5f;
    XMFLOAT4 color = XMFLOAT4(0.7f, 0.7f, 0.7f, 1.0f);
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

    XMFLOAT4 color = XMFLOAT4(0.7f, 0.7f, 0.7f, 1.0f);
    float h = size * sqrtf(2.0f / 3.0f);
    float r = size / sqrtf(3.0f);

    XMFLOAT3 v0(0, h, 0);
    XMFLOAT3 v1(-size * 0.5f, 0, r);
    XMFLOAT3 v2(size * 0.5f, 0, r);
    XMFLOAT3 v3(0, 0, -size / sqrtf(3.0f));

    XMVECTOR n1 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v1), XMLoadFloat3(&v0)),
        XMVectorSubtract(XMLoadFloat3(&v2), XMLoadFloat3(&v0))));
    XMFLOAT3 normal1;
    XMStoreFloat3(&normal1, n1);

    vertices.push_back({ v0, normal1, color, XMFLOAT2(0.5f, 0.0f) });
    vertices.push_back({ v1, normal1, color, XMFLOAT2(0.0f, 1.0f) });
    vertices.push_back({ v2, normal1, color, XMFLOAT2(1.0f, 1.0f) });

    XMVECTOR n2 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v2), XMLoadFloat3(&v0)),
        XMVectorSubtract(XMLoadFloat3(&v3), XMLoadFloat3(&v0))));
    XMFLOAT3 normal2;
    XMStoreFloat3(&normal2, n2);

    vertices.push_back({ v0, normal2, color, XMFLOAT2(0.5f, 0.0f) });
    vertices.push_back({ v2, normal2, color, XMFLOAT2(0.0f, 1.0f) });
    vertices.push_back({ v3, normal2, color, XMFLOAT2(1.0f, 1.0f) });

    XMVECTOR n3 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v3), XMLoadFloat3(&v0)),
        XMVectorSubtract(XMLoadFloat3(&v1), XMLoadFloat3(&v0))));
    XMFLOAT3 normal3;
    XMStoreFloat3(&normal3, n3);

    vertices.push_back({ v0, normal3, color, XMFLOAT2(0.5f, 0.0f) });
    vertices.push_back({ v3, normal3, color, XMFLOAT2(0.0f, 1.0f) });
    vertices.push_back({ v1, normal3, color, XMFLOAT2(1.0f, 1.0f) });

    XMVECTOR n4 = XMVector3Normalize(XMVector3Cross(
        XMVectorSubtract(XMLoadFloat3(&v2), XMLoadFloat3(&v1)),
        XMVectorSubtract(XMLoadFloat3(&v3), XMLoadFloat3(&v1))));
    XMFLOAT3 normal4;
    XMStoreFloat3(&normal4, n4);

    vertices.push_back({ v1, normal4, color, XMFLOAT2(0.0f, 0.0f) });
    vertices.push_back({ v3, normal4, color, XMFLOAT2(0.5f, 1.0f) });
    vertices.push_back({ v2, normal4, color, XMFLOAT2(1.0f, 0.0f) });

    for (UINT i = 0; i < 12; ++i)
    {
        indices.push_back(i);
    }
}

// 创建坐标轴圆柱（沿Y轴方向，从0到length）
void CreateAxisCylinder(float radius, float length, int slices, XMFLOAT4 color, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    // 底部圆心
    Vertex bottomCenter;
    bottomCenter.position = XMFLOAT3(0, 0, 0);
    bottomCenter.normal = XMFLOAT3(0, -1, 0);
    bottomCenter.color = color;
    bottomCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(bottomCenter);

    // 顶部圆心
    Vertex topCenter;
    topCenter.position = XMFLOAT3(0, length, 0);
    topCenter.normal = XMFLOAT3(0, 1, 0);
    topCenter.color = color;
    topCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(topCenter);

    // 底部圆周
    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = 0;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(cosf(theta), 0, sinf(theta));
        v.color = color;
        v.texCoord = XMFLOAT2((float)i / slices, 1.0f);
        vertices.push_back(v);
    }

    // 顶部圆周
    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = length;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(cosf(theta), 0, sinf(theta));
        v.color = color;
        v.texCoord = XMFLOAT2((float)i / slices, 0.0f);
        vertices.push_back(v);
    }

    // 底面索引
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(0);
        indices.push_back(2 + i + 1);
        indices.push_back(2 + i);
    }

    // 顶面索引
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(1);
        indices.push_back(2 + slices + 1 + i);
        indices.push_back(2 + slices + 1 + i + 1);
    }

    // 侧面索引
    int bottomStart = 2;
    int topStart = 2 + slices + 1;
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(bottomStart + i);
        indices.push_back(bottomStart + i + 1);
        indices.push_back(topStart + i);

        indices.push_back(bottomStart + i + 1);
        indices.push_back(topStart + i + 1);
        indices.push_back(topStart + i);
    }
}

// 创建坐标轴圆锥（沿Y轴方向，底部在0，顶点在height）
void CreateAxisCone(float radius, float height, int slices, XMFLOAT4 color, std::vector<Vertex>& vertices, std::vector<UINT>& indices)
{
    vertices.clear();
    indices.clear();

    // 顶点
    Vertex apex;
    apex.position = XMFLOAT3(0, height, 0);
    apex.normal = XMFLOAT3(0, 1, 0);
    apex.color = color;
    apex.texCoord = XMFLOAT2(0.5f, 0.0f);
    vertices.push_back(apex);

    // 底部圆心
    Vertex bottomCenter;
    bottomCenter.position = XMFLOAT3(0, 0, 0);
    bottomCenter.normal = XMFLOAT3(0, -1, 0);
    bottomCenter.color = color;
    bottomCenter.texCoord = XMFLOAT2(0.5f, 0.5f);
    vertices.push_back(bottomCenter);

    float slopeAngle = atanf(radius / height);
    float ny = sinf(slopeAngle);
    float nxz = cosf(slopeAngle);

    for (int i = 0; i <= slices; ++i)
    {
        float theta = 2.0f * XM_PI * i / slices;
        Vertex v;
        v.position.x = radius * cosf(theta);
        v.position.y = 0;
        v.position.z = radius * sinf(theta);
        v.normal = XMFLOAT3(nxz * cosf(theta), ny, nxz * sinf(theta));
        v.color = color;
        v.texCoord = XMFLOAT2((float)i / slices, 1.0f);
        vertices.push_back(v);
    }

    // 侧面索引
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(0);
        indices.push_back(2 + i);
        indices.push_back(2 + i + 1);
    }

    // 底面索引
    for (int i = 0; i < slices; ++i)
    {
        indices.push_back(1);
        indices.push_back(2 + i + 1);
        indices.push_back(2 + i);
    }
}
