# claude-code-plugins

개인 운영 Claude Code 플러그인 마켓플레이스. 현재 플러그인: **pl** — PL/테크리드 팀 오케스트레이션.

## 설치

전제조건: macOS/Linux + `python3` 3.10 이상 (Obsidian 백엔드의 헬퍼 스크립트가 Unix 전용 잠금(fcntl)을 사용한다. Windows는 미지원).

1. `/plugin marketplace add zz1996zz/claude-code-plugins`
2. `/plugin install pl@zz1996zz`
3. 메모리가 필요한 최초의 기능 작업에서 온보딩이 시작된다 (오탈자 점검 같은 routine 요청은 메모리를 쓰지 않으므로 온보딩이 나오지 않는다).

private 레포이므로 GitHub 계정이 이 레포에 초대돼 있어야 하고, git 자격증명(HTTPS 또는 SSH)이 설정돼 있어야 한다.

## 사용

`/pl:pl <기능 요청>` 으로 호출한다. 예: `/pl:pl 주문 취소 API에 부분 취소 지원 추가`
routine한 요청(오탈자 점검 등)은 솔로 패스로 처리되고, 기능 작업이면 역할 팀 구성·토론·구현·검증·메모리 기록까지 진행된다.

## 메모리 백엔드 선택 (온보딩 1회)

| 선택지 | 준비물 | 온보딩에서 할 일 |
|---|---|---|
| Obsidian vault (로컬 markdown) | 없음 (Obsidian 앱 불필요) | 저장 경로 1개 답하기 |
| Notion (공식 MCP) | Notion 계정 | `/mcp`에서 Notion OAuth 1회 + 메모리 root 페이지 URL 붙여넣기 |

Obsidian 백엔드만 쓸 경우 동봉된 Notion MCP 서버는 사용되지 않으므로, 원하면 `/mcp` 에서 `notion` 서버를 비활성화해도 된다.

Notion 선택 시 root 페이지 아래 Features/Decisions 데이터베이스와 Works 페이지가 자동 생성된다. 백엔드는 이후 `${CLAUDE_PLUGIN_DATA}/config.json` 삭제 후 재온보딩으로 바꿀 수 있다 (기존 데이터 이관은 미지원).

## 업데이트

`/plugin marketplace update zz1996zz` (사설 마켓플레이스는 자동 업데이트가 기본 꺼짐).

플러그인 콘텐츠 변경이 있어도 plugin.json 버전이 그대로면 업데이트가 감지되지 않는다 — 배포 시 반드시 버전을 올린다 (운영자 주의사항).

**주의**: `plugin uninstall`은 `${CLAUDE_PLUGIN_DATA}`(백엔드 설정 `config.json`·미반영 `pending/` 큐)를 함께 삭제한다(실측). 재설치가 아니라 버전 범프 + update 경로로 갱신해야 사용자 데이터가 보존된다. 부득이 uninstall 할 때는 `~/.claude/plugins/data/pl-zz1996zz/`를 먼저 백업할 것.

## 개발

- 스킬 시스템 변경 후: `plugins/pl/skills/team-pl-orchestrator/scripts/`의 `test_pl_config.py`, `test_memory_note.py`, `test_pl_user_config.py` 3종을 실행한다.
- 배포(push) 전 plugin.json의 version을 범프한다 — 설치 캐시가 버전 키라 버전이 같으면 팀원에게 변경이 전파되지 않는다.
- 설계 문서: `docs/specs/`, 구현 계획: `docs/plans/`.
