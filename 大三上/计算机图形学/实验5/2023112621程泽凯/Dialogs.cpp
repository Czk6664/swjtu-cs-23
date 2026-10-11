// Dialogs.cpp - Dialog procedures
#include "Dialogs.h"
#include "Globals.h"
#include "Geometry.h"
#include <commdlg.h>

#pragma comment(lib, "comdlg32.lib")

DLGTEMPLATE* CreateShapePropertiesDialogTemplate()
{
    static BYTE dlgTemplate[1024];
    memset(dlgTemplate, 0, sizeof(dlgTemplate));
    LPDLGTEMPLATE lpdt = (LPDLGTEMPLATE)dlgTemplate;
    LPWORD lpw;

    lpdt->style = WS_POPUP | WS_BORDER | WS_SYSMENU | DS_MODALFRAME | WS_CAPTION | DS_CENTER | WS_VSCROLL;
    lpdt->cdit = 0;
    lpdt->x = 0;
    lpdt->y = 0;
    lpdt->cx = 320;
    lpdt->cy = 500;

    lpw = (LPWORD)(lpdt + 1);
    *lpw++ = 0;
    *lpw++ = 0;

    wcscpy_s((wchar_t*)lpw, 50, L"\u5b9e\u4f53\u5c5e\u6027");
    lpw += wcslen((wchar_t*)lpw) + 1;

    return lpdt;
}

DLGTEMPLATE* CreateLightSettingsDialogTemplate()
{
    static BYTE dlgTemplate[1024];
    memset(dlgTemplate, 0, sizeof(dlgTemplate));
    LPDLGTEMPLATE lpdt = (LPDLGTEMPLATE)dlgTemplate;
    LPWORD lpw;

    lpdt->style = WS_POPUP | WS_BORDER | WS_SYSMENU | DS_MODALFRAME | WS_CAPTION | DS_CENTER;
    lpdt->cdit = 0;
    lpdt->x = 0;
    lpdt->y = 0;
    lpdt->cx = 280;
    lpdt->cy = 160;

    lpw = (LPWORD)(lpdt + 1);
    *lpw++ = 0;
    *lpw++ = 0;

    wcscpy_s((wchar_t*)lpw, 50, L"\u5149\u7167\u8bbe\u7f6e");
    lpw += wcslen((wchar_t*)lpw) + 1;

    return lpdt;
}


INT_PTR CALLBACK ShapePropertiesDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[64];
    static HWND hEdits[9];
    static HWND hComboPreset;
    static HWND hEditColorR, hEditColorG, hEditColorB;

    switch (message)
    {
    case WM_INITDIALOG:
    {
        if (!g_selectedShape) { EndDialog(hDlg, IDCANCEL); return TRUE; }

        int y = 10;
        const wchar_t* labels[] = { L"\u4f4d\u7f6e X:", L"Y:", L"Z:", L"\u65cb\u8f6c X\u00b0:", L"Y\u00b0:", L"Z\u00b0:", L"\u7f29\u653e X:", L"Y:", L"Z:" };
        float values[] = {
            g_selectedShape->position.x, g_selectedShape->position.y, g_selectedShape->position.z,
            XMConvertToDegrees(g_selectedShape->rotation.x),
            XMConvertToDegrees(g_selectedShape->rotation.y),
            XMConvertToDegrees(g_selectedShape->rotation.z),
            g_selectedShape->scale.x, g_selectedShape->scale.y, g_selectedShape->scale.z };

        for (int i = 0; i < 9; i++) {
            CreateWindowW(L"STATIC", labels[i], WS_CHILD | WS_VISIBLE, 10, y, 70, 18, hDlg, nullptr, nullptr, nullptr);
            hEdits[i] = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                90, y, 170, 18, hDlg, (HMENU)(UINT_PTR)(IDC_EDIT_POS_X + i), nullptr, nullptr);
            swprintf_s(buffer, L"%.2f", values[i]);
            SetWindowTextW(hEdits[i], buffer);
            y += 20;
        }

        y += 3;
        CreateWindowW(L"STATIC", L"----------------------------", WS_CHILD | WS_VISIBLE, 10, y, 260, 12, hDlg, nullptr, nullptr, nullptr);
        y += 15;

        CreateWindowW(L"STATIC", L"\u9884\u8bbe\u6837\u5f0f:", WS_CHILD | WS_VISIBLE, 10, y, 80, 18, hDlg, nullptr, nullptr, nullptr);
        hComboPreset = CreateWindowW(L"COMBOBOX", L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST,
            90, y, 170, 200, hDlg, (HMENU)(UINT_PTR)IDC_COMBO_PRESET, nullptr, nullptr);
        
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u65e0\u989c\u8272(\u7070\u8272)");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u91d1\u5c5e");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u5851\u6599");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u73bb\u7483");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u6a61\u80f6");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u9ec4\u91d1");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u767d\u94f6");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u7d2b\u94dc");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u94ec");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u7fe1\u7fe0");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u7eff\u5b9d\u77f3");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u73cd\u73e0");
        SendMessageW(hComboPreset, CB_SETCURSEL, g_selectedShape->presetStyle, 0);
        y += 22;

        CreateWindowW(L"STATIC", L"\u989c\u8272 R:", WS_CHILD | WS_VISIBLE, 10, y, 50, 18, hDlg, nullptr, nullptr, nullptr);
        hEditColorR = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
            60, y, 50, 18, hDlg, (HMENU)(UINT_PTR)IDC_EDIT_COLOR_R, nullptr, nullptr);
        swprintf_s(buffer, L"%.2f", g_selectedShape->color.x);
        SetWindowTextW(hEditColorR, buffer);

        CreateWindowW(L"STATIC", L"G:", WS_CHILD | WS_VISIBLE, 115, y, 20, 18, hDlg, nullptr, nullptr, nullptr);
        hEditColorG = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
            135, y, 50, 18, hDlg, (HMENU)(UINT_PTR)IDC_EDIT_COLOR_G, nullptr, nullptr);
        swprintf_s(buffer, L"%.2f", g_selectedShape->color.y);
        SetWindowTextW(hEditColorG, buffer);

        CreateWindowW(L"STATIC", L"B:", WS_CHILD | WS_VISIBLE, 190, y, 20, 18, hDlg, nullptr, nullptr, nullptr);
        hEditColorB = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
            210, y, 50, 18, hDlg, (HMENU)(UINT_PTR)IDC_EDIT_COLOR_B, nullptr, nullptr);
        swprintf_s(buffer, L"%.2f", g_selectedShape->color.z);
        SetWindowTextW(hEditColorB, buffer);
        y += 22;

        CreateWindowW(L"BUTTON", L"\u9009\u62e9\u989c\u8272...", WS_CHILD | WS_VISIBLE,
            10, y, 100, 22, hDlg, (HMENU)(UINT_PTR)IDC_BUTTON_COLOR, nullptr, nullptr);
        y += 26;

        CreateWindowW(L"BUTTON", L"\u786e\u5b9a", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON,
            90, y + 3, 80, 22, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindowW(L"BUTTON", L"\u53d6\u6d88", WS_CHILD | WS_VISIBLE,
            180, y + 3, 80, 22, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);

        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDC_COMBO_PRESET && HIWORD(wParam) == CBN_SELCHANGE) {
            int sel = (int)SendMessageW(hComboPreset, CB_GETCURSEL, 0, 0);
            if (g_selectedShape && sel >= 0) {
                Shape3D tempShape;
                tempShape.ApplyPresetStyle((PresetStyle)sel);
                swprintf_s(buffer, L"%.2f", tempShape.color.x);
                SetWindowTextW(hEditColorR, buffer);
                swprintf_s(buffer, L"%.2f", tempShape.color.y);
                SetWindowTextW(hEditColorG, buffer);
                swprintf_s(buffer, L"%.2f", tempShape.color.z);
                SetWindowTextW(hEditColorB, buffer);
            }
            return TRUE;
        }
        else if (LOWORD(wParam) == IDC_BUTTON_COLOR) {
            CHOOSECOLORW cc = {};
            static COLORREF acrCustClr[16];
            cc.lStructSize = sizeof(cc);
            cc.hwndOwner = hDlg;
            cc.lpCustColors = acrCustClr;
            cc.rgbResult = RGB((BYTE)(g_selectedShape->color.x * 255),
                (BYTE)(g_selectedShape->color.y * 255),
                (BYTE)(g_selectedShape->color.z * 255));
            cc.Flags = CC_FULLOPEN | CC_RGBINIT;

            if (ChooseColorW(&cc)) {
                float r = GetRValue(cc.rgbResult) / 255.0f;
                float g = GetGValue(cc.rgbResult) / 255.0f;
                float b = GetBValue(cc.rgbResult) / 255.0f;
                swprintf_s(buffer, L"%.2f", r);
                SetWindowTextW(hEditColorR, buffer);
                swprintf_s(buffer, L"%.2f", g);
                SetWindowTextW(hEditColorG, buffer);
                swprintf_s(buffer, L"%.2f", b);
                SetWindowTextW(hEditColorB, buffer);
            }
            return TRUE;
        }
        else if (LOWORD(wParam) == IDOK) {
            if (!g_selectedShape) { EndDialog(hDlg, IDCANCEL); return TRUE; }

            GetWindowTextW(hEdits[0], buffer, 64); g_selectedShape->position.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[1], buffer, 64); g_selectedShape->position.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[2], buffer, 64); g_selectedShape->position.z = (float)_wtof(buffer);
            GetWindowTextW(hEdits[3], buffer, 64); g_selectedShape->rotation.x = XMConvertToRadians((float)_wtof(buffer));
            GetWindowTextW(hEdits[4], buffer, 64); g_selectedShape->rotation.y = XMConvertToRadians((float)_wtof(buffer));
            GetWindowTextW(hEdits[5], buffer, 64); g_selectedShape->rotation.z = XMConvertToRadians((float)_wtof(buffer));
            GetWindowTextW(hEdits[6], buffer, 64); g_selectedShape->scale.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[7], buffer, 64); g_selectedShape->scale.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[8], buffer, 64); g_selectedShape->scale.z = (float)_wtof(buffer);

            int presetSel = (int)SendMessageW(hComboPreset, CB_GETCURSEL, 0, 0);
            g_selectedShape->presetStyle = (PresetStyle)presetSel;

            GetWindowTextW(hEditColorR, buffer, 64); float r = (float)_wtof(buffer);
            GetWindowTextW(hEditColorG, buffer, 64); float g = (float)_wtof(buffer);
            GetWindowTextW(hEditColorB, buffer, 64); float b = (float)_wtof(buffer);

            r = max(0.0f, min(1.0f, r));
            g = max(0.0f, min(1.0f, g));
            b = max(0.0f, min(1.0f, b));

            g_selectedShape->color = XMFLOAT4(r, g, b, g_selectedShape->color.w);
            g_selectedShape->material.diffuse = XMFLOAT3(r, g, b);
            UpdateShapeVertexColor(g_selectedShape);

            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL) {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}


INT_PTR CALLBACK LightSettingsDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[64];
    static HWND hEdits[6];

    switch (message)
    {
    case WM_INITDIALOG:
    {
        int y = 10;
        const wchar_t* labels[] = { L"\u5149\u6e90\u65b9\u5411 X:", L"Y:", L"Z:", L"\u5149\u6e90\u989c\u8272 R:", L"G:", L"B:" };
        float values[] = { g_lightDirection.x, g_lightDirection.y, g_lightDirection.z,
            g_lightColor.x, g_lightColor.y, g_lightColor.z };

        for (int i = 0; i < 6; i++) {
            CreateWindowW(L"STATIC", labels[i], WS_CHILD | WS_VISIBLE, 10, y, 100, 18, hDlg, nullptr, nullptr, nullptr);
            hEdits[i] = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                120, y, 140, 18, hDlg, (HMENU)(UINT_PTR)(IDC_EDIT_LIGHT_X + i), nullptr, nullptr);
            swprintf_s(buffer, L"%.2f", values[i]);
            SetWindowTextW(hEdits[i], buffer);
            y += 20;
        }

        CreateWindowW(L"BUTTON", L"\u786e\u5b9a", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON, 90, y + 3, 80, 22, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindowW(L"BUTTON", L"\u53d6\u6d88", WS_CHILD | WS_VISIBLE, 180, y + 3, 80, 22, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);
        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK) {
            GetWindowTextW(hEdits[0], buffer, 64); g_lightDirection.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[1], buffer, 64); g_lightDirection.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[2], buffer, 64); g_lightDirection.z = (float)_wtof(buffer);

            XMVECTOR lightDir = XMLoadFloat3(&g_lightDirection);
            lightDir = XMVector3Normalize(lightDir);
            XMStoreFloat3(&g_lightDirection, lightDir);

            GetWindowTextW(hEdits[3], buffer, 64); g_lightColor.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[4], buffer, 64); g_lightColor.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[5], buffer, 64); g_lightColor.z = (float)_wtof(buffer);

            g_lightColor.x = max(0.0f, min(2.0f, g_lightColor.x));
            g_lightColor.y = max(0.0f, min(2.0f, g_lightColor.y));
            g_lightColor.z = max(0.0f, min(2.0f, g_lightColor.z));

            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL) {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}

INT_PTR CALLBACK MaterialSettingsDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[64];
    static HWND hEdits[16];
    static HWND hComboPreset;

    switch (message)
    {
    case WM_INITDIALOG:
    {
        if (!g_selectedShape) { EndDialog(hDlg, IDCANCEL); return TRUE; }

        int y = 10;
        
        // 材质预设下拉框
        CreateWindowW(L"STATIC", L"\u6750\u8d28\u9884\u8bbe:", WS_CHILD | WS_VISIBLE, 10, y, 100, 18, hDlg, nullptr, nullptr, nullptr);
        hComboPreset = CreateWindowW(L"COMBOBOX", L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST,
            120, y, 140, 200, hDlg, (HMENU)(UINT_PTR)IDC_COMBO_PRESET, nullptr, nullptr);
        
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u81ea\u5b9a\u4e49");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u91d1\u5c5e");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u5851\u6599");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u73bb\u7483");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u6a61\u80f6");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u9ec4\u91d1");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u767d\u94f6");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u7d2b\u94dc");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u94ec");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u7fe1\u7fe0");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u7eff\u5b9d\u77f3");
        SendMessageW(hComboPreset, CB_ADDSTRING, 0, (LPARAM)L"\u73cd\u73e0");
        SendMessageW(hComboPreset, CB_SETCURSEL, g_selectedShape->presetStyle, 0);
        y += 25;

        const wchar_t* labels[] = { 
            L"\u73af\u5883\u5149 R:", L"G:", L"B:", 
            L"\u6f2b\u53cd\u5c04 R:", L"G:", L"B:",
            L"\u955c\u9762\u53cd\u5c04 R:", L"G:", L"B:", 
            L"\u81ea\u53d1\u5149 R:", L"G:", L"B:",
            L"\u5149\u6cfd\u5ea6:", L"\u900f\u660e\u5ea6:", L"\u53cd\u5c04\u7387:", L"\u4fdd\u7559:" };
        float values[] = {
            g_selectedShape->material.ambient.x, g_selectedShape->material.ambient.y, g_selectedShape->material.ambient.z,
            g_selectedShape->material.diffuse.x, g_selectedShape->material.diffuse.y, g_selectedShape->material.diffuse.z,
            g_selectedShape->material.specular.x, g_selectedShape->material.specular.y, g_selectedShape->material.specular.z,
            g_selectedShape->material.emissive.x, g_selectedShape->material.emissive.y, g_selectedShape->material.emissive.z,
            g_selectedShape->material.shininess, g_selectedShape->material.transparency, g_selectedShape->material.reflectivity, 0.0f };

        for (int i = 0; i < 15; i++) {
            CreateWindowW(L"STATIC", labels[i], WS_CHILD | WS_VISIBLE, 10, y, 100, 18, hDlg, nullptr, nullptr, nullptr);
            hEdits[i] = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
                120, y, 140, 18, hDlg, (HMENU)(UINT_PTR)(IDC_EDIT_AMBIENT_R + i), nullptr, nullptr);
            swprintf_s(buffer, L"%.3f", values[i]);
            SetWindowTextW(hEdits[i], buffer);
            y += 20;
        }

        CreateWindowW(L"BUTTON", L"\u786e\u5b9a", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON, 90, y + 3, 80, 22, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindowW(L"BUTTON", L"\u53d6\u6d88", WS_CHILD | WS_VISIBLE, 180, y + 3, 80, 22, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);
        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDC_COMBO_PRESET && HIWORD(wParam) == CBN_SELCHANGE) {
            int sel = (int)SendMessageW(hComboPreset, CB_GETCURSEL, 0, 0);
            if (g_selectedShape && sel >= 0) {
                Shape3D tempShape;
                tempShape.ApplyPresetStyle((PresetStyle)sel);
                
                // 更新所有编辑框
                swprintf_s(buffer, L"%.3f", tempShape.material.ambient.x);
                SetWindowTextW(hEdits[0], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.ambient.y);
                SetWindowTextW(hEdits[1], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.ambient.z);
                SetWindowTextW(hEdits[2], buffer);
                
                swprintf_s(buffer, L"%.3f", tempShape.material.diffuse.x);
                SetWindowTextW(hEdits[3], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.diffuse.y);
                SetWindowTextW(hEdits[4], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.diffuse.z);
                SetWindowTextW(hEdits[5], buffer);
                
                swprintf_s(buffer, L"%.3f", tempShape.material.specular.x);
                SetWindowTextW(hEdits[6], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.specular.y);
                SetWindowTextW(hEdits[7], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.specular.z);
                SetWindowTextW(hEdits[8], buffer);
                
                swprintf_s(buffer, L"%.3f", tempShape.material.emissive.x);
                SetWindowTextW(hEdits[9], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.emissive.y);
                SetWindowTextW(hEdits[10], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.emissive.z);
                SetWindowTextW(hEdits[11], buffer);
                
                swprintf_s(buffer, L"%.3f", tempShape.material.shininess);
                SetWindowTextW(hEdits[12], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.transparency);
                SetWindowTextW(hEdits[13], buffer);
                swprintf_s(buffer, L"%.3f", tempShape.material.reflectivity);
                SetWindowTextW(hEdits[14], buffer);
            }
            return TRUE;
        }
        else if (LOWORD(wParam) == IDOK) {
            if (!g_selectedShape) { EndDialog(hDlg, IDCANCEL); return TRUE; }

            GetWindowTextW(hEdits[0], buffer, 64); g_selectedShape->material.ambient.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[1], buffer, 64); g_selectedShape->material.ambient.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[2], buffer, 64); g_selectedShape->material.ambient.z = (float)_wtof(buffer);
            GetWindowTextW(hEdits[3], buffer, 64); g_selectedShape->material.diffuse.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[4], buffer, 64); g_selectedShape->material.diffuse.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[5], buffer, 64); g_selectedShape->material.diffuse.z = (float)_wtof(buffer);
            GetWindowTextW(hEdits[6], buffer, 64); g_selectedShape->material.specular.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[7], buffer, 64); g_selectedShape->material.specular.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[8], buffer, 64); g_selectedShape->material.specular.z = (float)_wtof(buffer);
            GetWindowTextW(hEdits[9], buffer, 64); g_selectedShape->material.emissive.x = (float)_wtof(buffer);
            GetWindowTextW(hEdits[10], buffer, 64); g_selectedShape->material.emissive.y = (float)_wtof(buffer);
            GetWindowTextW(hEdits[11], buffer, 64); g_selectedShape->material.emissive.z = (float)_wtof(buffer);
            GetWindowTextW(hEdits[12], buffer, 64); g_selectedShape->material.shininess = (float)_wtof(buffer);
            GetWindowTextW(hEdits[13], buffer, 64); g_selectedShape->material.transparency = (float)_wtof(buffer);
            GetWindowTextW(hEdits[14], buffer, 64); g_selectedShape->material.reflectivity = (float)_wtof(buffer);

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
            g_selectedShape->material.emissive.x = max(0.0f, min(1.0f, g_selectedShape->material.emissive.x));
            g_selectedShape->material.emissive.y = max(0.0f, min(1.0f, g_selectedShape->material.emissive.y));
            g_selectedShape->material.emissive.z = max(0.0f, min(1.0f, g_selectedShape->material.emissive.z));
            g_selectedShape->material.shininess = max(1.0f, min(128.0f, g_selectedShape->material.shininess));
            g_selectedShape->material.transparency = max(0.0f, min(1.0f, g_selectedShape->material.transparency));
            g_selectedShape->material.reflectivity = max(0.0f, min(1.0f, g_selectedShape->material.reflectivity));

            int presetSel = (int)SendMessageW(hComboPreset, CB_GETCURSEL, 0, 0);
            g_selectedShape->presetStyle = (PresetStyle)presetSel;
            
            // 更新颜色的alpha通道以反映透明度
            g_selectedShape->color.w = g_selectedShape->material.transparency;

            UpdateShapeVertexColor(g_selectedShape);
            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL) {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}

INT_PTR CALLBACK TextureSettingsDlgProc(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
    static wchar_t buffer[MAX_PATH];
    static HWND hEditPath = nullptr;
    static HWND hComboMode = nullptr;

    switch (message)
    {
    case WM_INITDIALOG:
    {
        if (!g_selectedShape) { EndDialog(hDlg, IDCANCEL); return TRUE; }

        CreateWindowW(L"STATIC", L"\u7eb9\u7406\u8def\u5f84:", WS_CHILD | WS_VISIBLE, 10, 10, 100, 20, hDlg, nullptr, nullptr, nullptr);
        hEditPath = CreateWindowW(L"EDIT", L"", WS_CHILD | WS_VISIBLE | WS_BORDER | ES_AUTOHSCROLL,
            10, 35, 250, 20, hDlg, (HMENU)(UINT_PTR)IDC_EDIT_TEXTURE_PATH, nullptr, nullptr);
        SetWindowTextW(hEditPath, g_selectedShape->texturePath.c_str());

        CreateWindowW(L"BUTTON", L"\u6d4f\u89c8...", WS_CHILD | WS_VISIBLE, 10, 65, 80, 25, hDlg, (HMENU)(UINT_PTR)IDC_BUTTON_BROWSE, nullptr, nullptr);

        CreateWindowW(L"STATIC", L"\u6620\u5c04\u65b9\u5f0f:", WS_CHILD | WS_VISIBLE, 10, 105, 100, 20, hDlg, nullptr, nullptr, nullptr);
        hComboMode = CreateWindowW(L"COMBOBOX", L"", WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST,
            10, 130, 250, 80, hDlg, (HMENU)(UINT_PTR)IDC_COMBO_TEXTURE_MODE, nullptr, nullptr);

        SendMessageW(hComboMode, CB_ADDSTRING, 0, (LPARAM)L"\u65e0\u7eb9\u7406");
        SendMessageW(hComboMode, CB_ADDSTRING, 0, (LPARAM)L"\u989c\u8272\u6df7\u5408");
        SendMessageW(hComboMode, CB_ADDSTRING, 0, (LPARAM)L"\u7eb9\u7406\u66ff\u6362");
        SendMessageW(hComboMode, CB_SETCURSEL, g_selectedShape->textureMode, 0);

        CreateWindowW(L"BUTTON", L"\u786e\u5b9a", WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON, 90, 170, 80, 25, hDlg, (HMENU)IDOK, nullptr, nullptr);
        CreateWindowW(L"BUTTON", L"\u53d6\u6d88", WS_CHILD | WS_VISIBLE, 180, 170, 80, 25, hDlg, (HMENU)IDCANCEL, nullptr, nullptr);
        return TRUE;
    }

    case WM_COMMAND:
        if (LOWORD(wParam) == IDC_BUTTON_BROWSE) {
            OPENFILENAMEW ofn = {};
            ofn.lStructSize = sizeof(ofn);
            ofn.hwndOwner = hDlg;
            ofn.lpstrFilter = L"\u56fe\u7247\u6587\u4ef6\0*.bmp;*.png;*.jpg;*.jpeg;*.gif;*.tiff\0\u6240\u6709\u6587\u4ef6\0*.*\0";
            ofn.lpstrFile = buffer;
            ofn.nMaxFile = MAX_PATH;
            ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
            if (GetOpenFileNameW(&ofn)) {
                SetWindowTextW(hEditPath, buffer);
                // 自动选择"颜色混合"模式（索引2）
                SendMessageW(hComboMode, CB_SETCURSEL, 2, 0);
            }
            return TRUE;
        }
        else if (LOWORD(wParam) == IDOK) {
            if (!g_selectedShape) { EndDialog(hDlg, IDCANCEL); return TRUE; }

            GetWindowTextW(hEditPath, buffer, MAX_PATH);
            std::wstring newPath = buffer;
            int modeIndex = (int)SendMessageW(hComboMode, CB_GETCURSEL, 0, 0);

            bool needReload = (newPath != g_selectedShape->texturePath) ||
                (modeIndex > 0 && g_selectedShape->textureView == nullptr);

            if (needReload && g_selectedShape->textureView) {
                g_selectedShape->textureView->Release();
                g_selectedShape->textureView = nullptr;
            }

            if (needReload && modeIndex > 0 && !newPath.empty()) {
                if (!LoadTextureFromFile(newPath.c_str(), &g_selectedShape->textureView)) {
                    MessageBoxW(hDlg, L"\u65e0\u6cd5\u52a0\u8f7d\u7eb9\u7406\u6587\u4ef6\uff01\n\u8bf7\u786e\u4fdd\u6587\u4ef6\u683c\u5f0f\u6b63\u786e\uff08\u652f\u6301BMP/PNG/JPG/JPEG/GIF/TIFF\uff09\u3002", L"\u9519\u8bef", MB_OK | MB_ICONERROR);
                    g_selectedShape->textureMode = 0;
                    EndDialog(hDlg, IDCANCEL);
                    return TRUE;
                }
            }

            if (modeIndex == 0 && g_selectedShape->textureView) {
                g_selectedShape->textureView->Release();
                g_selectedShape->textureView = nullptr;
            }

            g_selectedShape->texturePath = newPath;
            g_selectedShape->textureMode = modeIndex;
            EndDialog(hDlg, IDOK);
            return TRUE;
        }
        else if (LOWORD(wParam) == IDCANCEL) {
            EndDialog(hDlg, IDCANCEL);
            return TRUE;
        }
        break;
    }
    return FALSE;
}
