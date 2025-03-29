# GlobalNewsShortsRL 트러블슈팅 가이드

이 가이드는 GlobalNewsShortsRL 시스템 사용 중 발생할 수 있는 일반적인 문제와 해결 방법을 제공합니다.

## 목차

1. [API 관련 문제](#api-관련-문제)
2. [영상 다운로드 문제](#영상-다운로드-문제)
3. [자막 추출 문제](#자막-추출-문제)
4. [영상 제작 문제](#영상-제작-문제)
5. [업로드 문제](#업로드-문제)
6. [성과 분석 문제](#성과-분석-문제)
7. [데이터베이스 문제](#데이터베이스-문제)
8. [로그 확인 방법](#로그-확인-방법)

## API 관련 문제

### YouTube API 할당량 초과

**증상**: `quotaExceeded` 오류 메시지가 표시됩니다.

**해결 방법**:
1. Google Cloud Console에서 현재 API 사용량 확인
2. 할당량 증가 요청 또는 다음 날까지 대기
3. 여러 프로젝트에 API 키를 분산하여 사용

### OpenAI API 오류

**증상**: `RateLimitError` 또는 `ServiceUnavailableError` 오류가 발생합니다.

**해결 방법**:
1. 요청 간 지연 시간 추가 (최소 1초)
2. 오류 발생 시 자동 재시도 로직 구현
3. API 키가 유효한지 확인
4. OpenAI 서비스 상태 페이지 확인

### ElevenLabs API 오류

**증상**: TTS 오디오 생성 실패 또는 API 응답 오류가 발생합니다.

**해결 방법**:
1. API 키가 유효한지 확인
2. 월간 사용량 한도 확인
3. 텍스트 길이가 제한을 초과하지 않는지 확인
4. 네트워크 연결 상태 확인

## 영상 다운로드 문제

### 다운로드 실패

**증상**: `yt-dlp` 또는 `youtube-dl`이 영상 다운로드에 실패합니다.

**해결 방법**:
1. `yt-dlp` 최신 버전으로 업데이트:
   ```bash
   pip install -U yt-dlp
   ```
2. 영상 ID가 올바른지 확인
3. 영상이 지역 제한이 있는지 확인
4. 다른 형식 옵션 시도:
   ```python
   command = [
       'yt-dlp',
       '-f', 'best',  # 'bestvideo[height<=720]+bestaudio/best[height<=720]' 대신
       '--merge-output-format', 'mp4',
       '-o', video_path,
       youtube_url
   ]
   ```

### 영상 길이 제한

**증상**: 너무 긴 영상을 다운로드하려고 할 때 시간 초과 또는 메모리 오류가 발생합니다.

**해결 방법**:
1. `config.py`에서 `MAX_VIDEO_DURATION` 값을 줄임
2. 다운로드 시 시간 제한 설정:
   ```python
   command = [
       'yt-dlp',
       '--max-filesize', '100M',
       '--socket-timeout', '30',
       # 기타 옵션...
   ]
   ```

## 자막 추출 문제

### 자막을 찾을 수 없음

**증상**: `NoTranscriptFound` 또는 `TranscriptsDisabled` 오류가 발생합니다.

**해결 방법**:
1. 영상에 자막이 있는지 수동으로 확인
2. 자동 생성된 자막 사용 시도:
   ```python
   try:
       transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
       for transcript in transcript_list:
           if transcript.is_generated:
               return transcript.fetch()
   except Exception:
       pass
   ```
3. Whisper API를 사용한 음성-텍스트 변환으로 대체

### Whisper API 오류

**증상**: 오디오 파일 변환 중 오류가 발생합니다.

**해결 방법**:
1. 오디오 파일 형식이 지원되는지 확인 (MP3 권장)
2. 오디오 파일 크기가 25MB 미만인지 확인
3. 오디오 품질 개선 시도:
   ```python
   command = [
       'ffmpeg',
       '-i', input_file,
       '-af', 'highpass=200,lowpass=3000',
       '-ab', '128k',
       output_file
   ]
   ```

## 영상 제작 문제

### FFmpeg 오류

**증상**: FFmpeg 명령 실행 중 오류가 발생합니다.

**해결 방법**:
1. FFmpeg가 올바르게 설치되었는지 확인:
   ```bash
   ffmpeg -version
   ```
2. 입력 파일이 존재하고 접근 가능한지 확인
3. 출력 디렉토리에 쓰기 권한이 있는지 확인
4. FFmpeg 명령에 `-y` 플래그 추가하여 기존 파일 덮어쓰기

### 자막 오류

**증상**: 자막이 영상에 표시되지 않거나 잘못 표시됩니다.

**해결 방법**:
1. SRT 파일 형식이 올바른지 확인
2. 자막 인코딩이 UTF-8인지 확인
3. 자막 스타일 매개변수 조정:
   ```python
   subtitle_style = "FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H00000000,Bold=1,Alignment=10,MarginV=20"
   ```

## 업로드 문제

### 인증 오류

**증상**: YouTube API 인증 실패 또는 토큰 오류가 발생합니다.

**해결 방법**:
1. `token.json` 파일 삭제 후 재인증
2. OAuth 클라이언트 ID와 비밀번호가 올바른지 확인
3. 필요한 API 권한이 활성화되었는지 확인:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube`
   - `https://www.googleapis.com/auth/youtube.readonly`
   - `https://www.googleapis.com/auth/yt-analytics.readonly`

### 업로드 실패

**증상**: 영상 업로드 중 HTTP 오류가 발생합니다.

**해결 방법**:
1. 영상 파일 형식이 지원되는지 확인 (MP4 권장)
2. 영상 파일 크기가 YouTube 제한을 초과하지 않는지 확인
3. 제목, 설명, 태그에 금지된 문자가 없는지 확인
4. 네트워크 연결 상태 확인
5. 업로드 재시도 로직 구현:
   ```python
   max_retries = 3
   retry_count = 0
   
   while retry_count < max_retries:
       try:
           # 업로드 코드
           break
       except HttpError as e:
           retry_count += 1
           if retry_count >= max_retries:
               raise
           time.sleep(5)  # 5초 대기 후 재시도
   ```

## 성과 분석 문제

### 데이터 액세스 오류

**증상**: YouTube Analytics API에서 데이터를 가져오지 못합니다.

**해결 방법**:
1. 영상 업로드 후 최소 24-48시간 대기 (데이터 처리 시간)
2. API 권한이 올바르게 설정되었는지 확인
3. 날짜 범위가 올바른지 확인 (미래 날짜 불가)
4. 요청하는 지표가 유효한지 확인

### 불완전한 데이터

**증상**: 일부 지표가 누락되거나 0으로 표시됩니다.

**해결 방법**:
1. 더 긴 시간 범위로 데이터 요청
2. 영상이 공개 상태인지 확인
3. 영상 업로드 후 충분한 시간이 경과했는지 확인
4. 다른 지표 조합 시도

## 데이터베이스 문제

### 데이터베이스 액세스 오류

**증상**: SQLite 데이터베이스 연결 또는 쿼리 오류가 발생합니다.

**해결 방법**:
1. 데이터베이스 파일 경로가 올바른지 확인
2. 데이터베이스 파일에 대한 읽기/쓰기 권한 확인
3. 데이터베이스 파일이 손상되었는지 확인:
   ```bash
   sqlite3 /path/to/feedback.db "PRAGMA integrity_check;"
   ```
4. 손상된 경우 백업에서 복원 또는 새 데이터베이스 생성

### 데이터 불일치

**증상**: 데이터베이스의 데이터가 예상과 다릅니다.

**해결 방법**:
1. 트랜잭션 사용하여 데이터 일관성 보장:
   ```python
   conn = sqlite3.connect(db_path)
   try:
       # 데이터베이스 작업
       conn.commit()
   except Exception as e:
       conn.rollback()
       raise e
   finally:
       conn.close()
   ```
2. 데이터베이스 스키마 확인
3. 중복 데이터 확인 및 제거

## 로그 확인 방법

시스템 문제를 진단하기 위해 로그 파일을 확인하는 방법:

### 모듈별 로그 파일

각 모듈은 `logs` 디렉토리에 로그 파일을 생성합니다:

- `youtube_collector.log`: YouTube 데이터 수집 모듈
- `transcript_processor.log`: 자막 추출 및 번역 모듈
- `content_generator.log`: 콘텐츠 생성 모듈
- `video_producer.log`: 영상 제작 모듈
- `youtube_uploader.log`: 업로드 및 분석 모듈
- `feedback_processor.log`: 피드백 및 강화학습 모듈

### 로그 분석

로그 파일에서 오류 메시지 확인:

```bash
grep "ERROR" logs/*.log
```

특정 영상 ID에 대한 로그 확인:

```bash
grep "video_id" logs/*.log
```

최근 로그 확인:

```bash
tail -n 100 logs/youtube_uploader.log
```

### 디버그 모드 활성화

더 자세한 로그를 위해 디버그 모드 활성화:

```python
# config.py 파일에서
LOG_LEVEL = 'DEBUG'

# 또는 코드에서 직접 설정
logging.basicConfig(level=logging.DEBUG)
```

## 일반적인 문제 해결 단계

1. 최신 로그 확인
2. API 키와 인증 정보 확인
3. 네트워크 연결 상태 확인
4. 필요한 소프트웨어(FFmpeg, yt-dlp 등) 버전 확인
5. 임시 파일 및 캐시 삭제
6. 시스템 재시작
7. 각 모듈을 개별적으로 테스트하여 문제 지점 식별
