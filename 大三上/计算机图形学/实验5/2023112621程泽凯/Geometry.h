#pragma once
#include "Types.h"
#include <vector>

// 几何体创建函数声明
void CreateSphere(float radius, int slices, int stacks, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateCylinder(float radius, float height, int slices, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateCone(float radius, float height, int slices, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreatePlane(float width, float height, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateCube(float size, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateTetrahedron(float size, std::vector<Vertex>& vertices, std::vector<UINT>& indices);

// 坐标轴几何体创建（细长圆柱 + 圆锥箭头）
void CreateAxisCylinder(float radius, float length, int slices, XMFLOAT4 color, std::vector<Vertex>& vertices, std::vector<UINT>& indices);
void CreateAxisCone(float radius, float height, int slices, XMFLOAT4 color, std::vector<Vertex>& vertices, std::vector<UINT>& indices);

// 形状管理函数
Shape3D* CreateShape(ShapeType type);
Shape3D* PickShape(int x, int y);
bool UpdateShapeVertexColor(Shape3D* shape);
bool LoadTextureFromFile(const wchar_t* filename, ID3D11ShaderResourceView** textureView);
