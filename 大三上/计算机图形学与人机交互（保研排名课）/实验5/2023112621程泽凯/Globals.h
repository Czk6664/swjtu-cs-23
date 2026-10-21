#pragma once
#include "Types.h"
#include <vector>

// 全局变量声明
extern HWND g_hWnd;
extern ID3D11Device* g_pd3dDevice;
extern ID3D11DeviceContext* g_pImmediateContext;
extern IDXGISwapChain* g_pSwapChain;
extern ID3D11RenderTargetView* g_pRenderTargetView;
extern ID3D11DepthStencilView* g_pDepthStencilView;
extern ID3D11VertexShader* g_pVertexShader;
extern ID3D11PixelShader* g_pPixelShader;
extern ID3D11InputLayout* g_pVertexLayout;
extern ID3D11Buffer* g_pConstantBuffer;
extern ID3D11RasterizerState* g_pRasterizerState;
extern ID3D11RasterizerState* g_pWireframeState;
extern ID3D11DepthStencilState* g_pDepthStencilState;
extern ID3D11BlendState* g_pBlendState;
extern ID3D11SamplerState* g_pSamplerState;

extern std::vector<Shape3D*> g_shapes;
extern Shape3D* g_selectedShape;
extern POINT g_lastMousePos;
extern bool g_isDragging;
extern bool g_cameraMode;
extern bool g_middleButtonDragging;
extern DWORD g_lastClickTime;
extern std::wstring g_statusText;
extern XMFLOAT3 g_dragOffset;

extern float g_cameraYaw;
extern float g_cameraPitch;
extern float g_cameraDistance;

extern bool g_showAxes;

// 坐标轴相关 - 使用圆柱和圆锥
extern ID3D11Buffer* g_pAxisXVertexBuffer;
extern ID3D11Buffer* g_pAxisXIndexBuffer;
extern UINT g_axisXIndexCount;
extern ID3D11Buffer* g_pAxisYVertexBuffer;
extern ID3D11Buffer* g_pAxisYIndexBuffer;
extern UINT g_axisYIndexCount;
extern ID3D11Buffer* g_pAxisZVertexBuffer;
extern ID3D11Buffer* g_pAxisZIndexBuffer;
extern UINT g_axisZIndexCount;

extern ID3D11Buffer* g_pArrowXVertexBuffer;
extern ID3D11Buffer* g_pArrowXIndexBuffer;
extern UINT g_arrowXIndexCount;
extern ID3D11Buffer* g_pArrowYVertexBuffer;
extern ID3D11Buffer* g_pArrowYIndexBuffer;
extern UINT g_arrowYIndexCount;
extern ID3D11Buffer* g_pArrowZVertexBuffer;
extern ID3D11Buffer* g_pArrowZIndexBuffer;
extern UINT g_arrowZIndexCount;

extern XMFLOAT3 g_axesOrigin;
extern bool g_isDraggingOrigin;

extern XMFLOAT3 g_lightDirection;
extern XMFLOAT3 g_lightColor;

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
#define IDC_COMBO_PRESET 2011
#define IDC_BUTTON_COLOR 2012
#define IDC_EDIT_COLOR_R 2013
#define IDC_EDIT_COLOR_G 2014
#define IDC_EDIT_COLOR_B 2015

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
