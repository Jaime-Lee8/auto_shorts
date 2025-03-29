"""
자막 추출 및 번역 모듈
- YouTube 영상에서 자막을 추출합니다.
- 자막이 없는 경우 Whisper API를 사용하여 음성을 텍스트로 변환합니다.
- 추출된 텍스트를 한국어로 번역하고 요약합니다.
"""
import os
import json
import logging
import tempfile
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import openai
import requests

# 설정 파일 임포트
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    OPENAI_API_KEY, DATA_DIR, LOGS_DIR, TEMP_DIR
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'transcript_processor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('transcript_processor')

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

class TranscriptProcessor:
    """자막 추출 및 번역 클래스"""
    
    def __init__(self):
        """초기화 함수"""
        # 임시 디렉토리 생성
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'transcripts'), exist_ok=True)
        
        logger.info("TranscriptProcessor 초기화 완료")
    
    def get_youtube_transcript(self, video_id):
        """
        YouTube 영상의 자막 추출
        
        Args:
            video_id (str): YouTube 영상 ID
            
        Returns:
            str: 추출된 자막 텍스트
        """
        try:
            # 영어 자막 우선 시도
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 영어 자막 찾기
            transcript = None
            for t in transcript_list:
                if t.language_code == 'en':
                    transcript = t
                    break
            
            # 영어 자막이 없으면 자동 생성된 자막 사용
            if not transcript:
                for t in transcript_list:
                    if t.is_generated:
                        transcript = t
                        break
            
            # 자막이 없으면 첫 번째 자막 사용
            if not transcript and transcript_list:
                transcript = transcript_list[0]
            
            if transcript:
                # 자막 가져오기
                transcript_data = transcript.fetch()
                
                # 자막 텍스트 추출
                full_text = ' '.join([entry['text'] for entry in transcript_data])
                
                logger.info(f"YouTube 자막 추출 성공: {video_id}")
                return full_text
            else:
                logger.warning(f"YouTube 자막을 찾을 수 없음: {video_id}")
                return None
                
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            logger.warning(f"YouTube 자막을 찾을 수 없음: {video_id}, 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"YouTube 자막 추출 중 오류 발생: {e}")
            return None
    
    def download_audio(self, video_id):
        """
        YouTube 영상의 오디오 다운로드
        
        Args:
            video_id (str): YouTube 영상 ID
            
        Returns:
            str: 다운로드된 오디오 파일 경로
        """
        try:
            # 임시 파일 경로
            audio_file = os.path.join(TEMP_DIR, f"{video_id}.mp3")
            
            # youtube-dl 또는 yt-dlp를 사용하여 오디오 다운로드
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # yt-dlp 설치 확인 및 설치
            try:
                subprocess.run(['yt-dlp', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("yt-dlp 설치 중...")
                subprocess.run(['pip', 'install', 'yt-dlp'], check=True)
            
            # 오디오 다운로드
            command = [
                'yt-dlp',
                '-f', 'bestaudio',
                '-x',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '-o', audio_file,
                youtube_url
            ]
            
            subprocess.run(command, check=True)
            
            if os.path.exists(audio_file):
                logger.info(f"오디오 다운로드 성공: {video_id}")
                return audio_file
            else:
                logger.error(f"오디오 다운로드 실패: {video_id}")
                return None
                
        except Exception as e:
            logger.error(f"오디오 다운로드 중 오류 발생: {e}")
            return None
    
    def transcribe_audio_with_whisper(self, audio_file):
        """
        Whisper API를 사용하여 오디오 파일을 텍스트로 변환
        
        Args:
            audio_file (str): 오디오 파일 경로
            
        Returns:
            str: 변환된 텍스트
        """
        try:
            with open(audio_file, "rb") as audio:
                response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="en"
                )
            
            transcript = response.text
            logger.info(f"Whisper API 변환 성공: {audio_file}")
            return transcript
            
        except Exception as e:
            logger.error(f"Whisper API 변환 중 오류 발생: {e}")
            return None
    
    def translate_to_korean(self, text):
        """
        OpenAI API를 사용하여 텍스트를 한국어로 번역
        
        Args:
            text (str): 번역할 텍스트
            
        Returns:
            str: 번역된 텍스트
        """
        try:
            # 텍스트가 너무 길면 분할
            max_chunk_size = 4000
            chunks = []
            
            if len(text) > max_chunk_size:
                # 문장 단위로 분할
                sentences = text.split('. ')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < max_chunk_size:
                        current_chunk += sentence + '. '
                    else:
                        chunks.append(current_chunk)
                        current_chunk = sentence + '. '
                
                if current_chunk:
                    chunks.append(current_chunk)
            else:
                chunks = [text]
            
            # 각 청크 번역
            translated_chunks = []
            
            for chunk in chunks:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a professional translator specializing in translating English news to Korean."},
                        {"role": "user", "content": f"Translate the following English text to Korean. Maintain the formal tone appropriate for news content:\n\n{chunk}"}
                    ],
                    temperature=0.3
                )
                
                translated_chunk = response.choices[0].message.content
                translated_chunks.append(translated_chunk)
            
            # 번역된 청크 결합
            translated_text = ' '.join(translated_chunks)
            
            logger.info("텍스트 번역 성공")
            return translated_text
            
        except Exception as e:
            logger.error(f"텍스트 번역 중 오류 발생: {e}")
            return None
    
    def summarize_content(self, text, max_sentences=3):
        """
        OpenAI API를 사용하여 텍스트 요약
        
        Args:
            text (str): 요약할 텍스트
            max_sentences (int): 최대 문장 수
            
        Returns:
            dict: 요약 결과 (hook, summary, background)
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert news editor specializing in creating concise summaries for short-form video content."},
                    {"role": "user", "content": f"""
                    다음 뉴스 내용을 분석하고 YouTube Shorts용 스크립트를 생성해주세요.
                    
                    1. 감정적 Hook 멘트 (3초 이내, 질문형이나 경고형으로 작성)
                    2. 핵심 요약 (3문장 이내)
                    3. 배경 설명 또는 해설 (1문장)
                    
                    JSON 형식으로 다음과 같이 반환해주세요:
                    {{
                        "hook": "감정적 Hook 멘트",
                        "summary": "핵심 요약 (3문장 이내)",
                        "background": "배경 설명 또는 해설 (1문장)"
                    }}
                    
                    뉴스 내용:
                    {text}
                    """
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            summary_result = json.loads(response.choices[0].message.content)
            
            logger.info("텍스트 요약 성공")
            return summary_result
            
        except Exception as e:
            logger.error(f"텍스트 요약 중 오류 발생: {e}")
            return None
    
    def process_video(self, video_id):
        """
        영상 처리 메인 함수
        
        Args:
            video_id (str): YouTube 영상 ID
            
        Returns:
            dict: 처리 결과
        """
        try:
            # 1. YouTube 자막 추출 시도
            transcript = self.get_youtube_transcript(video_id)
            
            # 2. 자막이 없으면 Whisper API 사용
            if not transcript:
                logger.info(f"YouTube 자막이 없어 Whisper API 사용: {video_id}")
                audio_file = self.download_audio(video_id)
                
                if audio_file:
                    transcript = self.transcribe_audio_with_whisper(audio_file)
                    
                    # 임시 파일 삭제
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
            
            if not transcript:
                logger.error(f"자막 추출 실패: {video_id}")
                return None
            
            # 3. 한국어로 번역
            translated_text = self.translate_to_korean(transcript)
            
            if not translated_text:
                logger.error(f"번역 실패: {video_id}")
                return None
            
            # 4. 내용 요약
            summary = self.summarize_content(translated_text)
            
            if not summary:
                logger.error(f"요약 실패: {video_id}")
                return None
            
            # 5. 결과 저장
            result = {
                'video_id': video_id,
                'original_transcript': transcript,
                'translated_text': translated_text,
                'summary': summary
            }
            
            # 파일로 저장
            result_file = os.path.join(DATA_DIR, 'transcripts', f"{video_id}.json")
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"영상 처리 완료: {video_id}")
            return result
            
        except Exception as e:
            logger.error(f"영상 처리 중 오류 발생: {e}")
            return None

# 테스트 코드
if __name__ == "__main__":
    processor = TranscriptProcessor()
    
    # 테스트용 영상 ID (CNN 뉴스 영상)
    test_video_id = "dQw4w9WgXcQ"  # 실제 뉴스 영상 ID로 변경 필요
    
    result = processor.process_video(test_video_id)
    
    if result:
        print("처리 결과:")
        print(f"Hook: {result['summary']['hook']}")
        print(f"요약: {result['summary']['summary']}")
        print(f"배경: {result['summary']['background']}")
    else:
        print("영상 처리 실패")
