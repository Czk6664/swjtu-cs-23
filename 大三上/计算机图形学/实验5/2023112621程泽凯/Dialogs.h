#pragma once
#include <windows.h>

// 对话框过程函数声明
INT_PTR CALLBACK ShapePropertiesDlgProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK LightSettingsDlgProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK MaterialSettingsDlgProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK TextureSettingsDlgProc(HWND, UINT, WPARAM, LPARAM);

// 对话框模板创建函数
DLGTEMPLATE* CreateShapePropertiesDialogTemplate();
DLGTEMPLATE* CreateLightSettingsDialogTemplate();
