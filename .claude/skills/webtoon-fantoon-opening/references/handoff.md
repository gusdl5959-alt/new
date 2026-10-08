# 소스 목록과 이미지·프롬프트 HTML

프로젝트별 새 폴더에 저장한다. 동기화된 sources/와 사용자 원본은 그대로 둔다. 파일명 변경/폴더 모으기는 복사본으로 처리하는 것을 기본으로 한다.

## 소스 목록

scripts/media_inventory.py는 실제 경로, 크기, 해시, 가능한 메타데이터와 중복 그룹을 만든다. 외부 서비스에 접속하지 않는다.

사용:
python3 <skill>/scripts/media_inventory.py /path/to/sources --out /path/to/new-job/inventory.json
python3 <skill>/scripts/media_inventory.py /path/to/sources --out /path/to/new-job/inventory.json --ffprobe /path/to/ffprobe

이미지는 Pillow, 영상/음악은 제공 ffprobe 또는 PyAV를 사용할 수 있을 때 읽는다. 없거나 파일이 손상되면 결과에 남긴다. 기술적 목록이며 원작 유사도·움직임·최종 편집 검수 통과를 의미하지 않는다.

## HTML 전달

scripts/build_handoff.py는 사용자가 직접 생성·검수할 수 있는 로컬 패키지를 만든다. 새 출력 폴더를 사용하고 기존 패키지를 덮어쓰지 않는다.

입력 JSON 구조:

{
  "project": "작품명 팬툰OP",
  "aspect_ratio": "16:9",
  "output_resolution": "1280x720",
  "scenes": [{
    "id": "OP001",
    "title": "인물과 공간 소개",
    "status": "planned",
    "references": ["references/character.png"],
    "image": null,
    "video": null,
    "image_prompt": "한국어 이미지 프롬프트",
    "motion_prompt": "한국어 모션 프롬프트",
    "note": "아직 생성하지 않은 컷",
    "source_urls": []
  }]
}

상대 경로는 JSON 폴더 기준이고 절대 경로도 허용한다. 컷 ID는 영문·숫자·하이픈·밑줄이며 중복하지 않는다. image/video에는 실제 받은 파일만 넣는다. 참조 이미지를 생성 이미지로 표시하지 않는다.

사용:
python3 <skill>/scripts/build_handoff.py /path/to/manifest.json --out /path/to/new-handoff

결과:
- index.html: 이미지/영상, 상태, 한국어 프롬프트, 복사 버튼, 검색.
- images/: 모든 컷의 참고/시작 이미지를 컷 ID·역할별 파일명으로 복사한 하나의 폴더.
- videos/: 실제 입력된 영상만 복사.
- cuts/<ID>/: 두 프롬프트 TXT와 컷 JSON.
- manifest.json: 복사 경로, 상태와 누락 파일 기록.

생성·다운로드·웹툰 수집·원작 판정·영상 편집을 하는 스크립트가 아니다. 누락 파일을 만들거나 성공 상태로 바꾸지 않는다. HTML에서 누락을 확인하고 원본을 찾거나 생성하지 못했음을 알린다.

한 이미지가 여러 컷의 참조라면 대응 관계를 유지한다. 중복 프롬프트 삭제 요청에서는 고정 외형 조건은 유지하되 목적·행동·샷까지 같은 컷을 제거하고 번호와 연결 이미지도 갱신한다.
