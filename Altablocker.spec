# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Altablocker 단일 exe 빌드.

빌드:
    pyinstaller Altablocker.spec

산출물:
    dist/Altablocker.exe   (단일 파일, 콘솔 창 없음)

핵심 포함 사항:
    - customtkinter assets/themes (collect_all로 자동 누락 방지)
    - assets/icon.ico (exe 아이콘 + 런타임 iconbitmap/iconphoto)
    - Pretendard 폰트 2종 (런타임 FR_PRIVATE 등록 — 시스템 미설치)
"""
import os

from PyInstaller.utils.hooks import collect_all

# 어디서 실행하든 spec 위치(프로젝트 루트) 기준으로 리소스를 찾도록 고정
os.chdir(os.path.dirname(os.path.abspath(SPEC)))

datas = []
binaries = []
hiddenimports = []

# ── customtkinter (테마 json 등) ──
d, b, h = collect_all('customtkinter')
datas += d
binaries += b
hiddenimports += h

# ── PIL (런타임 iconphoto 멀티사이즈 로드) ──
hiddenimports += ['PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL.IcoImagePlugin']

# ── 앱 폰트 (Pretendard — 런타임 FR_PRIVATE 등록용) ──
for _f in ('assets/Pretendard-Regular.ttf', 'assets/Pretendard-Bold.ttf'):
    if os.path.exists(_f):
        datas.append((_f, 'assets'))
    else:
        print(f"[spec] {_f} 없음 — 기본 폰트로 빌드됩니다.")

# ── 아이콘 ──
_icon = 'assets/icon.ico'
_has_icon = os.path.exists(_icon)
if _has_icon:
    datas.append((_icon, 'assets'))
else:
    print("[spec] assets/icon.ico 없음 — 기본 아이콘으로 빌드됩니다.")


a = Analysis(
    ['altab_blocker.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Altablocker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[_icon] if _has_icon else None,
)
