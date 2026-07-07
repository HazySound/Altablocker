# AlTab Blocker

> 메이플스토리에서 **Alt(점프) + Tab(기믹 키)** 이 겹쳐 창이 전환되는 사고를 막아주는 유틸리티

Alt 키를 점프로 쓰는 유저가 보스 기믹 등으로 Tab을 눌러야 할 때, Windows의 Alt+Tab 창 전환이 발동해 게임 화면이 내려가는 문제를 해결합니다. 보스 클리어 직전에 창이 바뀌어 죽는 일, 이제 없습니다.

---

## ✨ 주요 기능

- **선택 프로그램 모드** — 지정한 프로그램(예: `MapleStory.exe`)이 화면에 떠 있을 때**만** Alt+Tab 차단. 그 외에는 Alt+Tab 정상 작동
- **전역 차단 모드** — 켜져 있는 동안 모든 창에서 Alt+Tab 차단
- **원클릭 토글** — 스위치를 끄면 그 즉시 완전 원상복구
- **차단 카운터** — Alt+Tab이 실제로 막힐 때마다 횟수 표시 (동작 확인용)
- 단일 exe, 설치 불필요, 네트워크 미사용

## 📥 사용법

1. [Releases](../../releases)에서 `Altablocker.exe` 다운로드
2. 실행 후 프로그램 선택 (실행 중인 게임이 자동 감지됨) → 스위치 ON
3. 끝. 게임에서 Alt를 누른 채 Tab을 눌러도 창이 전환되지 않습니다

> **⚠ 작동이 안 된다면**: 게임을 관리자 권한으로 실행 중인 경우, Windows 보안 정책(UIPI)상 일반 권한 프로그램은 관리자 권한 창의 키 입력을 처리할 수 없습니다. 이 프로그램도 **우클릭 → 관리자 권한으로 실행**으로 켜주세요.

## ⚙ 동작 원리

Windows가 공식 문서로 제공하는 **저수준 키보드 훅(`WH_KEYBOARD_LL`)** 을 사용합니다. Microsoft의 공식 유틸리티인 PowerToys(Keyboard Manager)를 비롯해 수많은 정상 프로그램이 쓰는 표준 API입니다.

동작은 단 하나입니다: **"Alt가 눌린 상태에서 들어온 Tab 키 다운" 이벤트를 Windows에 전달하지 않고 무시**합니다. 그 결과 창 전환만 발동하지 않습니다.

| 이 프로그램이 하는 것 | 이 프로그램이 **하지 않는** 것 |
|---|---|
| OS 수준에서 Alt+Tab 조합 1종 무시 | ❌ 키 입력 생성·주입 (`SendInput` 등 일절 없음) |
| 포커스된 창의 프로세스 이름 확인 | ❌ 게임 프로세스/메모리/파일 접근 |
| | ❌ 입력 반복·자동화 (매크로 기능 없음) |
| | ❌ 패킷 조작, 네트워크 통신 |
| | ❌ 게임 클라이언트에 코드 주입 |

## 🛡 "이거 쓰면 정지당하는 거 아닌가요?"

결론부터: **이 프로그램에는 넥슨이 제재하는 유형의 동작이 원리적으로 존재하지 않습니다.** 근거를 공식 정책과 실제 사례로 설명합니다.

### 1. 넥슨이 실제로 제재하는 것

메이플스토리 공식 [운영정책](https://maplestory.nexon.com/Common/Footer/OperationPolicy)과 [권장하지 않는 플레이 방식 안내](https://maplestory.nexon.com/Guide/N23GameInformation/Articles/452)가 명시하는 단속 대상은 다음과 같습니다:

- **"자체적인 입력 반복 기능(매크로)을 제공하는 키보드, 마우스 등의 하드웨어/소프트웨어"** — 즉, 입력을 **만들어내는** 도구
- 비인가 프로그램(핵)을 통한 메모리·클라이언트 조작
- **"정상 범위를 넘어서는 게임 기록"**, 장시간 동일 키 입력 반복 등 **행동 로그 기반** 이상 패턴

공통점은 명확합니다. 제재는 **"가짜 입력을 생성하거나, 게임을 조작하거나, 사람이 아닌 것처럼 플레이하는 행위"** 를 향합니다.

### 2. 실제 정지 사례들과 무엇이 다른가

커뮤니티에 보고된 정지 사례의 대표격인 **AutoHotkey(오토핫키)** 는 `Send` 명령으로 **키 입력을 생성**하는 자동화 도구입니다. 키 연타, 스킬 시퀀스 자동 입력 등 "사람 대신 입력을 만들어내는" 사용이 가능하기에 제재 대상이 됩니다.

AlTab Blocker는 정확히 **반대 방향**으로 동작합니다:

- 입력을 **1개도 생성하지 않습니다.** 물리적으로 누른 키를 통과시키거나(그 외 전부), 무시하거나(Alt 눌린 상태의 Tab 1종) — 할 수 있는 일이 이 둘뿐입니다
- 게임 입장에서는 아무 일도 일어나지 않습니다. 게임이 받는 모든 입력은 **사람이 실제로 누른 키**뿐입니다
- 행동 로그에 남을 "비정상 패턴"을 만들 수단 자체가 없습니다 — 이 프로그램은 플레이를 **대신해 주는 게 아니라**, Windows 단축키 하나를 꺼줄 뿐입니다

### 3. FilterKeySetting과 같은 부류입니다

메이플 유저들이 키 씹힘 방지를 위해 널리 쓰는 [FilterKeySetting](https://github.com/lasiyan/Filter-Key-Setting)은 Windows **접근성 설정(필터 키)** 을 변경하는 프로그램입니다. 공개된 소스코드를 직접 확인해보면, Windows 공식 접근성 API인 `SystemParametersInfo(SPI_SETFILTERKEYS)` 호출로 필터 키 값을 적용합니다 — **제어판에서 직접 바꾸는 것과 동일한 경로**이며, 입력을 생성하는 코드(`SendInput` 등)는 소스 전체에 존재하지 않습니다. 이처럼 게임에 일절 관여하지 않고 **OS 설정만 바꾸는 구조**이기에 오랫동안 커뮤니티에서 사용되어 왔습니다.

AlTab Blocker도 같은 철학입니다:

| | FilterKeySetting | AlTab Blocker |
|---|---|---|
| 건드리는 대상 | Windows 접근성 설정 (레지스트리/`SystemParametersInfo`) | Windows 키 이벤트 전달 (저수준 훅) |
| 게임 프로세스 접촉 | ❌ 없음 | ❌ 없음 |
| 입력 생성/자동화 | ❌ 없음 | ❌ 없음 |
| 효과 | 키 반복 딜레이 등 OS 동작 변경 | Alt+Tab 창 전환이라는 OS 동작 1종 차단 |
| 수동 대체 수단 | 제어판에서 직접 설정 가능 | (Windows가 UI를 제공하지 않아 프로그램이 필요) |

둘 다 본질은 **"게임 밖 Windows의 동작을 바꾸는 도구"** 이지, 게임에 개입하는 도구가 아닙니다.

### 4. 그래도 솔직하게 말씀드리면

- 넥슨은 어떤 서드파티 프로그램도 공식적으로 "인증"하지 않습니다. 이 문서는 **동작 원리에 근거한 설명**이지 넥슨의 보증이 아닙니다
- 소스코드가 전부 공개되어 있으니(단일 파일, `altab_blocker.py`) 직접 확인하실 수 있습니다. 입력을 만드는 코드(`SendInput`, `keybd_event` 등)가 한 줄도 없다는 것을 검증 가능합니다
- 네트워크를 사용하지 않으므로 작업 관리자에서 직접 확인하실 수 있습니다

## 🔨 직접 빌드하기

```powershell
git clone https://github.com/HazySound/Altablocker.git
cd altablocker
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\pyinstaller Altablocker.spec   # → dist\Altablocker.exe
```

개발 실행: `.\venv\Scripts\python altab_blocker.py`

## 📄 라이선스 및 고지

- 이 프로그램: [MIT License](LICENSE)
- 폰트: [Pretendard](https://github.com/orioncactus/pretendard) — SIL Open Font License 1.1 (exe에 내장되어 함께 배포됩니다)
- 앱 아이콘: [Flaticon](https://www.flaticon.com/)의 무료 아이콘 2종을 조합해 제작 — [Shortcut icons created by Iconify Designs](https://www.flaticon.com/free-icons/shortcut), [Ban icons created by Anggara](https://www.flaticon.com/free-icons/ban)
